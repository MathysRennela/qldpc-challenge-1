#!/usr/bin/env python3
"""Fetch arXiv Atom metadata only; never fetch paper, source, or ancillary URLs."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, cast

ATOM = "http://www.w3.org/2005/Atom"
ARXIV = "http://arxiv.org/schemas/atom"
UA = "qldpc-challenge-metadata-harvest/1.0"


def canonical_id(raw: str) -> tuple[str, str]:
    value = raw.rsplit("/", 1)[-1]
    match = re.fullmatch(r"(.+?)(?:v(\d+))?", value)
    if not match:
        raise ValueError(f"unexpected arXiv id: {raw}")
    return match.group(1), f"v{match.group(2) or '1'}"


def text(node: ET.Element, name: str) -> str:
    child = node.find(f"{{{ATOM}}}{name}")
    if child is None or child.text is None:
        return ""
    return child.text.strip()


def fetch(query: str, size: int) -> list[dict[str, Any]]:
    params = urllib.parse.urlencode({
        "search_query": query,
        "start": 0,
        "max_results": size,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    })
    request = urllib.request.Request(
        f"https://export.arxiv.org/api/query?{params}",
        headers={"User-Agent": UA},
    )
    with urllib.request.urlopen(request, timeout=45) as response:
        root = ET.fromstring(response.read())
    result: list[dict[str, Any]] = []
    for entry in root.findall(f"{{{ATOM}}}entry"):
        raw_id = text(entry, "id")
        cid, version = canonical_id(raw_id)
        result.append({
            "canonical_arxiv_id": cid,
            "version": version,
            "submitted_at": text(entry, "published"),
            "updated_at": text(entry, "updated"),
            "title": " ".join(text(entry, "title").split()),
            "authors": [
                text(author, "name")
                for author in entry.findall(f"{{{ATOM}}}author")
            ],
            "abstract": " ".join(text(entry, "summary").split()),
            "categories": [
                category.attrib.get("term", "")
                for category in entry.findall(f"{{{ARXIV}}}primary_category")
            ],
        })
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--queries", type=Path, required=True)
    parser.add_argument("--cursors", type=Path, required=True)
    parser.add_argument("--records", type=Path, required=True)
    parser.add_argument("--runs", type=Path, required=True)
    args = parser.parse_args()
    config = cast(dict[str, Any], json.loads(args.queries.read_text()))
    cursors = cast(dict[str, Any], json.loads(args.cursors.read_text()))
    recorded = set()
    if args.records.exists():
        for line in args.records.read_text().splitlines():
            if line.strip():
                item = json.loads(line)
                recorded.add((item["canonical_arxiv_id"], item["version"]))

    run_at = datetime.now(timezone.utc).replace(microsecond=0)
    run: dict[str, Any] = {"schema_version": 1, "run_at": run_at.isoformat().replace("+00:00", "Z"),
           "queries": [], "api_errors": []}
    new_records: list[dict[str, Any]] = []
    fetched_by_query: dict[str, list[dict[str, Any]]] = {}
    for definition in config["queries"]:
        name = definition["name"]
        cursor = cursors["queries"].get(name, {})
        previous = cursor.get("last_successful")
        effective_query = definition["search_query"]
        if previous:
            timestamp = datetime.fromisoformat(previous["submitted_at"].replace("Z", "+00:00"))
            start = timestamp - timedelta(days=config.get("overlap_days", 7))
            effective_query = (f"submittedDate:[{start.strftime('%Y%m%d%H%M')} TO *] "
                               f"AND ({definition['search_query']})")
        try:
            entries = fetch(effective_query, definition["page_size"])
        except Exception as exc:  # preserve the old cursor on any failed query
            run["api_errors"].append({"query": name, "error": repr(exc)})
            continue
        fetched_by_query[name] = entries
        fresh = []
        for entry in entries:
            key = (entry["canonical_arxiv_id"], entry["version"])
            if key in recorded:
                continue
            entry.update({"query": name, "metadata_source": "arXiv Atom API"})
            fresh.append(entry)
            recorded.add(key)
        new_records.extend(fresh)
        run["queries"].append({"name": name, "effective_query": effective_query,
                                "result_count": len(entries),
                                "new_record_count": len(fresh),
                                "newest_seen": ({
                                    "submitted_at": entries[0]["submitted_at"],
                                    "canonical_arxiv_id": entries[0]["canonical_arxiv_id"],
                                } if entries else None)})

    if run["api_errors"]:
        print(json.dumps(run, indent=2), file=sys.stderr)
        return 2
    args.records.parent.mkdir(parents=True, exist_ok=True)
    with args.records.open("a", encoding="utf-8") as output:
        for entry in new_records:
            output.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")
    args.runs.mkdir(parents=True, exist_ok=True)
    stamp = run_at.strftime("%Y-%m-%dT%H%M%SZ")
    (args.runs / f"{stamp}.json").write_text(json.dumps(run, indent=2) + "\n")

    # Only successful queries advance. The run manifest and records are durable first.
    for item in run["queries"]:
        entries = fetched_by_query[item["name"]]
        definition = next(q for q in config["queries"] if q["name"] == item["name"])
        cursors["queries"][item["name"]]["query_definition_sha256"] = hashlib.sha256(
            json.dumps(definition, sort_keys=True).encode("utf-8")
        ).hexdigest()
        if not entries:
            continue
        cursors["queries"][item["name"]].update({
            "last_successful": {
                "submitted_at": entries[0]["submitted_at"],
                "canonical_arxiv_id": entries[0]["canonical_arxiv_id"],
            },
            "newest_seen": {
                "submitted_at": entries[0]["submitted_at"],
                "canonical_arxiv_id": entries[0]["canonical_arxiv_id"],
            },
            "last_run_at": run["run_at"],
        })
    args.cursors.write_text(json.dumps(cursors, indent=2) + "\n")
    print(json.dumps(run, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
