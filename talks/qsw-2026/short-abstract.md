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
which codes are best under a given hardware constraint, principally qubit
connectivity and check weight. Parameters are scattered across papers, and
distance claims are especially hard to reproduce and easy to overstate:
computing distance is NP-hard, and the heuristic searches used to estimate it
only ever return an upper bound.

The QEC Challenge treats this as a software-infrastructure problem. A participant
opens a pull request adding one JSON file describing a CSS code; continuous
integration recomputes
the code's parameters from its parity-check matrices, checks a self-certifying
distance witness, actively searches for a lighter logical operator that would
refute the claim, and merges the entry only if it survives. Codes are compared
like with like, grouped by those same connectivity and weight constraints and
ranked on a Pareto frontier rather than by a single gameable number, with the
groupings computed from the code rather than self-declared. Because a distance
from a heuristic search is only an upper bound, a missed lighter operator
silently inflates it; the board's refutation step therefore also serves as a
referee for machine-discovered codes, which are generated in volume with exactly
such search-based distance estimates.

The lightning talk walks through the end-to-end flow (submit, CI verifies, board
updates), the layered trust model behind the distance tiers, and how to
contribute by hand or by automated agent. The board and pipeline are public at
github.com/unitaryfoundation/qldpc-challenge.
