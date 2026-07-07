# Quantum Software Workshop 2026 lightning talk

Extended abstract for a lightning-talk submission to the Quantum Software
Workshop 2026 (IEEE Quantum Week, Toronto, September 17, 2026), highlighting the
QEC Challenge.

- `abstract.tex` is the extended abstract (about four pages). It reuses the
  framing of the project whitepaper (`docs/planar_code_challenge.tex`) but is
  updated to the current board: the computed layered track scheme, the distance
  refutation gate, and current numbers.

- `refs.bib` holds the references (self-contained so the folder builds
  standalone); the bibliography is generated with BibTeX rather than hand-listed.

Build:

```
pdflatex abstract.tex
bibtex abstract
pdflatex abstract.tex
pdflatex abstract.tex
```

Submission is via the workshop's Google Form (deadline July 13, 2026); this
document is the supporting extended abstract.
