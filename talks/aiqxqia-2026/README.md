# AIQxQIA 2026 full-paper submission

Draft for the International Workshop on AI for Quantum and Quantum for AI
(AIQxQIA 2026), https://aiqxqia2026.cnr.it/. Full-paper format (body exceeds
4 pages, references excluded), per the instructions for authors.

- `paper.tex`: the paper. CEUR-WS `ceurart` class, single column,
  single-blind (authors named), as the workshop requires.
- `ceurart.cls`, `ccicons.sty`, `elsarticle-num-names.bst`: the CEUR-WS
  template class and its dependencies, vendored so the folder is
  self-contained for EasyChair/Overleaf.
- `refs.bib`: snapshot of the repository's root `refs.bib` at draft time.

Build:

    latexmk -pdf paper.tex

Submission is through EasyChair
(https://easychair.org/conferences/?conf=aiqxqia2026). Deadline July 31.

Authors are alphabetical by surname. Before submitting: add ORCIDs and
co-author emails, and update the
`\conference` line once the workshop announces dates and location.
