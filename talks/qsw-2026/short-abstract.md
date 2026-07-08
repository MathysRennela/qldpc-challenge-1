# QSW 2.6 lightning-talk form submission

Plain-text answers for the Google Form (no PDF required). The extended
abstract in `abstract.tex` remains the supporting document if one is wanted
later.

## Name
Farrokh Labib

## Lightning talk category
QEC, infrastructure, and hardware

## Talk title
The QEC Challenge: a public, automatically verified leaderboard for quantum LDPC codes

## Talk description
Quantum low-density parity-check (qLDPC) codes are the leading route to
low-overhead fault tolerance, but there is no shared, machine-checked record of
which codes are best under which constraints. Parameters are scattered across
papers, and distance claims are especially hard to reproduce and easy to
overstate: computing distance is NP-hard, and the heuristic decoders often used
to estimate it can be wrong.

The QEC Challenge treats this as a software-infrastructure problem. A participant
submits one JSON file describing a CSS code; continuous integration recomputes
the code's parameters from its parity-check matrices, checks a self-certifying
distance witness, actively searches for a lighter logical operator that would
refute the claim, and merges the entry only if it survives. Ranking is a
per-track Pareto frontier rather than a single gameable number, track membership
is computed from the code rather than self-declared, and the whole pipeline runs
on every pull request. This also makes the board a natural referee for
machine-discovered codes, whose characteristic failure mode is an overstated
distance.

The lightning talk walks through the end-to-end flow (submit, CI verifies, board
updates), the layered trust model behind the distance tiers, and how to
contribute by hand or by automated agent.
