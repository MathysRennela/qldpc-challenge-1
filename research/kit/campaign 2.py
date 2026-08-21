"""Small, dependency-free bookkeeping helpers for autoresearch campaigns.

This module coordinates search evidence; it does not judge candidates. The
trusted validator remains the only promotion gate. Campaign files are ordinary
JSON working artifacts and should normally live outside ``codes/``.

A campaign manifest has this shape::

    {
      "campaign": "weight-6-2026-08",
      "target": {"locality": "unrestricted", "weight": 6},
      "families": {
        "bb-geometry": {"status": "active", "sample_budget": 1000}
      },
      "rounds": []
    }

The helpers deliberately accept and return dictionaries so an external agent
harness can add fields without depending on this module.
"""
import json
import os


ROUTE_STATUSES = {
    "underexplored",
    "active",
    "promising",
    "calibrated_negative",
    "blocked",
    "parked",
}


def new_campaign(name, *, target=None, budget=None, families=None):
    """Return a fresh campaign manifest with no search results."""
    return {
        "campaign": name,
        "target": target or {},
        "budget": budget or {},
        "families": families or {},
        "rounds": [],
    }


def load_campaign(path):
    """Load a manifest, or raise ``FileNotFoundError`` if it does not exist."""
    with open(path) as f:
        manifest = json.load(f)
    if not isinstance(manifest, dict) or not manifest.get("campaign"):
        raise ValueError("campaign manifest must contain a non-empty 'campaign'")
    manifest.setdefault("target", {})
    manifest.setdefault("budget", {})
    manifest.setdefault("families", {})
    manifest.setdefault("rounds", [])
    return manifest


def save_campaign(path, manifest):
    """Write a manifest, creating its parent directory when necessary."""
    if not isinstance(manifest, dict) or not manifest.get("campaign"):
        raise ValueError("campaign manifest must contain a non-empty 'campaign'")
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)
        f.write("\n")


def register_family(manifest, family_id, *, hypothesis="", sample_budget=None,
                    status="underexplored", evidence=None):
    """Register or replace one family entry and return ``manifest``.

    Status changes are explicit so a controller cannot silently treat an
    insufficiently searched family as a negative result.
    """
    if status not in ROUTE_STATUSES:
        raise ValueError(f"unknown route status: {status}")
    families = manifest.setdefault("families", {})
    entry = families.setdefault(family_id, {})
    entry.update({"status": status, "hypothesis": hypothesis})
    if sample_budget is not None:
        entry["sample_budget"] = int(sample_budget)
    if evidence is not None:
        entry["evidence"] = list(evidence)
    entry.setdefault("rounds", 0)
    entry.setdefault("generated", 0)
    entry.setdefault("survivors", 0)
    entry.setdefault("best", None)
    return manifest


def record_round(manifest, round_id, family_id, records, audit=None):
    """Record one family run and update aggregate family counters.

    ``records`` are the output of :func:`search.screen`; ``audit`` is the
    optional output returned with ``return_audit=True``. No candidate is
    promoted by this function.
    """
    families = manifest.setdefault("families", {})
    if family_id not in families:
        register_family(manifest, family_id)
    entry = families[family_id]
    records = list(records)
    audit = dict(audit or {})
    entry["rounds"] = int(entry.get("rounds", 0)) + 1
    entry["generated"] = int(entry.get("generated", 0)) + int(audit.get("generated", 0))
    entry["survivors"] = int(entry.get("survivors", 0)) + len(records)
    if records:
        best = max(records, key=lambda record: record.get("efficiency", 0))
        if entry.get("best") is None or best.get("efficiency", 0) > entry["best"].get("efficiency", 0):
            entry["best"] = best
    manifest.setdefault("rounds", []).append({
        "round": round_id,
        "family": family_id,
        "audit": audit,
        "records": records,
    })
    return manifest


def set_route_status(manifest, family_id, status, *, reason=None, reopen_if=None):
    """Set a route status with an optional explanation for future searchers."""
    if status not in ROUTE_STATUSES:
        raise ValueError(f"unknown route status: {status}")
    if family_id not in manifest.setdefault("families", {}):
        register_family(manifest, family_id)
    entry = manifest["families"][family_id]
    entry["status"] = status
    if reason is not None:
        entry["status_reason"] = reason
    if reopen_if is not None:
        entry["reopen_if"] = reopen_if
    return manifest


def family_summary(manifest):
    """Return a compact, JSON-serializable summary suitable for a report."""
    summary = []
    for family_id, entry in manifest.get("families", {}).items():
        best = entry.get("best") or {}
        summary.append({
            "family": family_id,
            "status": entry.get("status", "underexplored"),
            "rounds": entry.get("rounds", 0),
            "generated": entry.get("generated", 0),
            "survivors": entry.get("survivors", 0),
            "best": best.get("fingerprint"),
            "best_parameters": [best.get(key) for key in ("n", "k", "d")]
            if best else None,
            "best_efficiency": best.get("efficiency"),
        })
    return sorted(summary, key=lambda item: (
        -float(item["best_efficiency"] or 0), item["family"]))


def write_round_report(path, manifest):
    """Write a compact report without dropping the full manifest."""
    report = {
        "campaign": manifest.get("campaign"),
        "target": manifest.get("target", {}),
        "budget": manifest.get("budget", {}),
        "families": family_summary(manifest),
        "rounds": len(manifest.get("rounds", [])),
    }
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w") as f:
        json.dump(report, f, indent=2, sort_keys=True)
        f.write("\n")
    return report


if __name__ == "__main__":
    demo = new_campaign("demo", target={"weight": 6})
    register_family(demo, "bb-geometry", hypothesis="structured supports", sample_budget=10)
    record_round(demo, 1, "bb-geometry", [], {"generated": 10})
    print(json.dumps(family_summary(demo), indent=2))
