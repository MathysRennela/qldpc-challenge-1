# Metadata-only arXiv harvest

This directory is the durable, resumable record for the literature-harvest pilot in
`fieldnotes/2026-08-15-arxiv-board-harvest.md`.

The pilot deliberately uses only arXiv Atom metadata: identifier, version, title,
submission timestamp, authors, and abstract-derived triage. It does **not** download
or inspect PDFs, source archives, appendices, figures, or supplementary files. A lead
must be explicitly approved before paper content is opened.

## Files

- `queries.json`: exact query strings, filters, sort order, page size, and query hash.
- `cursors.json`: one checkpoint per query. The ordering key is
  `(submitted_at, canonical_arxiv_id)`; the first run establishes a baseline.
- `records.jsonl`: append-only normalized metadata and triage records. Revisions are
  retained as distinct `canonical_id + version` records.
- `runs/2026-08-16T114302Z.json`: immutable run manifest for the pilot.
- `harvest.py`: stdlib-only metadata fetcher. It never requests an arXiv PDF URL.

## Re-running

```sh
uv run python research/literature/harvest.py \
  --queries research/literature/queries.json \
  --cursors research/literature/cursors.json \
  --records research/literature/records.jsonl \
  --runs research/literature/runs
```

The fetcher queries with the configured overlap window, discards already-recorded
`canonical_id + version` pairs, appends records and the run manifest, and advances a
cursor only after those writes succeed. Network/API failures leave the previous
cursor unchanged.

Current triage is metadata-only. `reconstructible` means the abstract explicitly
suggests a finite recipe or public artifact; it is not evidence that reconstruction
has been performed. No candidate in this pilot is a board submission.
