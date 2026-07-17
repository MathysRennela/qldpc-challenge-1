# Locality-track score f

This note defines the locality-track score `f` used on the board and the proven
ceiling it is measured against. It follows the proposal in issue #168. The score
lives in `verify/locality_score.py`; the verifier attaches it to every code that
carries a certified embedding.

## The inequality

Place a stabilizer code on a D-dimensional grid of sites, one qubit per site, n
sites, and suppose every stabilizer generator is supported inside a box of `w`
sites per axis (range-w local). The Bravyi-Poulin-Terhal tradeoff
(arXiv:0909.5200), with the w- and D-dependence made explicit through the
Bravyi-Terhal cleaning lemma (arXiv:0810.1983), gives

    k * d^(2/(D-1))  <=  64 * g(D) * w^(2 + 2/(D-1)) * n,
    g(D) = D(D-1) * (4D)^(2/(D-1)).

Two parts of this statement have different standing.

- The exponents are provably optimal. Tiling n / w^D disjoint copies of an
  asymptotically good qLDPC code [[m, rho*m, delta*m]] (Panteleev-Kalachev,
  arXiv:2111.03654) at blocklength m = w^D fills a single w-box with each copy,
  is range-w local by construction, and reaches
  k * d^(2/(D-1)) / n = rho * delta^(2/(D-1)) * w^(2 + 2/(D-1)). That matches the
  w- and D-exponents in every dimension (at D=2, kd^2/n = rho*delta^2 * w^4). The
  same scaling on the (n,k,d) axis is reached by surface-code stacks, layer codes
  (arXiv:2309.16503) in 3D, and subdivision codes (arXiv:2309.16104) in general
  D. See also Dai-Li (arXiv:2409.15203) and Dai-Li-Tang (arXiv:2503.22651).

- The multiplicative constant is not tight. The true ceiling lies between roughly
  rho * delta^(2/(D-1)) (flat in D, from the tiling) and 64 * g(D) (of order D^2).
  The g(D) shape comes from the cubical bookkeeping in the proof, not from any
  matching construction.

## The score

The score contains only the proven-tight structure, the exponents, plus a fixed
display constant:

    f = 16 * k * d^(2/(D-1)) / ( w^(2 + 2/(D-1)) * n ).

The constant 16 is fixed, not tunable: it normalizes the rotated surface code to
`f = 1` (n = d^2, k = 1, range w = 2) at every distance. The challenge reads:
maximize f; any score above 1 beats the surface code. Unlike kd^2/n, f is
scale-free. A code family converges to a constant instead of inflating with n;
in particular the exponent-saturating tiled construction scores 16 * rho *
delta^(2/(D-1)), roughly flat across dimensions, and beats the surface code iff
rho * delta^2 > 1/16 at D=2. That is a concrete open target: exhibit a good code
with rho * delta^2 > 1/16, or any 2D-local family with f > 1.

Because f decreases in both D and w, and a code can trade D against w along its
embedding curve, a code's score is f*, the maximum of f over its certified
embeddings, an intrinsic invariant of (H_X, H_Z), NP-hard to compute exactly but
certifiable in the same sense as the distance d. A submission gives its canonical
layout in `locality` and may list further certified layouts in `alt_embeddings`;
the verifier scores each honest one and reports the maximum. Extra embeddings can
only raise f*, never lower it, and they do not change track membership, which
stays with `locality`.

## The ceiling (versioned)

The theorem is quoted separately as the proven ceiling, never mixed into the
score:

    f  <=  1024 * g(D),      which is 2^17 at D = 2.

This bound is loose and D-dependent. It, not the score, carries a version tag
(`ceiling v1`). Tightening the tracked constant changes the quoted ceiling and
never any published score, in any dimension. The proven-tight exponents go in the
score; the unproven parts (the 64, the g(D) shape) go here.

## The range-w convention

The score needs a single integer `w`: the side, in sites, of the smallest box
that contains any one stabilizer's support. The verifier measures it from the
submitted coordinates as

    w = 1 + max over stabilizers, over axes, of (site span of the support / lattice spacing),

rounded to the nearest site. A support that spans s lattice steps along some axis
needs a box of s + 1 sites on that axis. The weight-4 rotated surface-code
plaquette spans one step per axis, so w = 2, which is exactly what fixes the
f = 1 calibration. Note this is a geometric quantity distinct from the algebraic
max check weight shown elsewhere on the board (issue #165 uses the check weight;
the two are not interchangeable).

## Scope

`f` is defined only for codes with a certified embedding into a grid of fixed
dimension. Good high-rate qLDPC codes are expanders with no such embedding; for
them f is undefined and they compete on the kd^2/n tracks, which this score
complements rather than replaces (the theorem provably has no content as
D grows). Dimension and range are established from a submitter-provided layout
when present, and otherwise from a heuristic embedding search whose output is
still a layout the verifier checks, so a found embedding can only lower a score,
never inflate it. Spectral-gap and separator lower bounds on D give upper bounds
on f and are used only to audit posted scores or to flag codes for which no
embedding exists, never to score.

## Open points

- Tightening the ceiling constant (changes only the quoted ceiling).
- The flat-ceiling conjecture: is the optimal constant c_opt(D) bounded in D?
  This reduces to a foam-type geometry question and is what would justify
  comparing raw f across dimensions.
- A credit convention for layout improvements: anyone can raise an existing
  code's score by certifying a better embedding, as with distance re-claims.
