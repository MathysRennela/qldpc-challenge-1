"""Build edge toric [[2L²,2,L]] codes and triangular 6.6.6 color codes.

Edge toric: standard toric code on an L×L torus (n=2L², k=2, d=L).
Color code: triangular 6.6.6 on hexagonal lattice (n=3m²+3m+1, k=1, d=2m+1).

Stages validated candidates to research/candidates/.
"""
import sys, os, json, math, itertools
from collections import defaultdict
import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "kit"))
sys.path.insert(0, os.path.join(_HERE, "..", "verify"))

from css import compute_k, verify_css
from surrogate import distance_rand, lightest_logical
from submit import make_submission, save_submission


# ---------------------------------------------------------------------------
# Edge toric code on an L×L torus
# ---------------------------------------------------------------------------

def build_toric_code(L):
    """Standard toric code on an L×L torus.

    Qubits on edges.  Horizontal edge from (ix,iy) to ((ix+1)%L, iy)
    has index 2*(iy*L+ix); vertical edge from (ix,iy) to (ix,(iy+1)%L)
    has index 2*(iy*L+ix)+1.

    X checks (star): one per vertex, weight 4.
    Z checks (plaq): one per face,  weight 4.

    Returns (HX, HZ) as int8 arrays.
    """
    n = 2 * L * L
    HX = np.zeros((L * L, n), dtype=np.int8)
    HZ = np.zeros((L * L, n), dtype=np.int8)

    def h(ix, iy):  # horizontal edge index
        return 2 * ((iy % L) * L + (ix % L))
    def v(ix, iy):  # vertical edge index
        return 2 * ((iy % L) * L + (ix % L)) + 1

    for iy in range(L):
        for ix in range(L):
            vtx = iy * L + ix
            # star (X) at vertex (ix, iy): 4 incident edges
            HX[vtx, h(ix, iy)]      = 1   # right
            HX[vtx, h(ix - 1, iy)]  = 1   # left
            HX[vtx, v(ix, iy)]      = 1   # down
            HX[vtx, v(ix, iy - 1)]  = 1   # up
            # plaquette (Z) at face (ix, iy): 4 bounding edges
            HZ[vtx, h(ix, iy)]      = 1   # bottom
            HZ[vtx, h(ix, iy + 1)]  = 1   # top  (shifted up by 1 in y)
            HZ[vtx, v(ix, iy)]      = 1   # left
            HZ[vtx, v(ix + 1, iy)]  = 1   # right (shifted right by 1 in x)

    return HX, HZ


def toric_coords(L):
    """Per-qubit 2-D coordinates for the toric code.
    Horizontal edge at (ix+0.5, iy); vertical edge at (ix, iy+0.5)."""
    coords = []
    for iy in range(L):
        for ix in range(L):
            coords.append([ix + 0.5, iy])   # horizontal
            coords.append([ix, iy + 0.5])   # vertical
    return coords


# ---------------------------------------------------------------------------
# Triangular 6.6.6 colour code  (Bombín & Martin-Delgado)
# ---------------------------------------------------------------------------

def _hex_neighbors(q, r, s):
    """Yield the 6 cube-coordinate neighbours of a hex cell."""
    for dq, dr, ds in [(1,-1,0),(-1,1,0),(1,0,-1),(-1,0,1),(0,1,-1),(0,-1,1)]:
        yield (q+dq, r+dr, s+ds)


def _hex_to_cartesian(q, r, s):
    """Cube → cartesian (axial-style)."""
    x = q + 0.5 * r
    y = (math.sqrt(3) / 2) * r
    return (x, y)


def build_color_code(m):
    """Triangular 6.6.6 colour code of distance d=2m+1.

    n = 3m²+3m+1, k = 1, d = 2m+1.

    Construction: hexagonal (honeycomb / {6,3}) lattice within an
    equilateral-triangular patch of hex-cells of "radius" m.  Qubits sit on
    vertices; X and Z checks on faces (self-dual CSS: H_X = H_Z = face-vertex
    incidence matrix).

    The triangular patch is: all hex cells (q, r, s) with q+r+s = 0, q >= 0,
    r >= 0, s >= 0, q <= m, r <= m, s <= m.

    Returns (HX, HZ).
    """
    # --- 1. Collect all hex cells in the triangular patch ---
    cells = set()
    for q in range(m + 1):
        for r in range(m + 1 - q):
            s = -q - r
            cells.add((q, r, s))

    # --- 2. Build the dual graph: edges between adjacent cells ---
    # Each edge in the dual graph corresponds to a shared edge between
    # two hexagons, which becomes an edge in the honeycomb lattice.
    #
    # But the honeycomb lattice is the *primal* graph whose faces are the
    # hex cells.  We need vertices and edges of the honeycomb lattice.
    #
    # Alternative (simpler): the vertices of the honeycomb lattice sit at
    # the corners of each hex cell.  Each hex cell has 6 corners, and
    # neighbouring cells share corners.
    #
    # We'll identify corners by their position in the plane.

    # --- 2a. Find all unique vertex positions ---
    # A hex cell at cube (q, r, s) has 6 corner positions.
    # In cube coordinates, the corners of the hex centered at (q, r, s)
    # are at fractional cube positions (q + dq/3, r + dr/3, s + ds/3)
    # for the 6 directions.  But it's easier to work in cartesian.

    # The 6 corner offsets (in cube coords, relative to cell center)
    corner_offsets_cube = [
        (2/3, -1/3, -1/3),
        (1/3,  1/3, -2/3),
        (-1/3, 2/3, -1/3),
        (-2/3, 1/3,  1/3),
        (-1/3,-1/3,  2/3),
        (1/3, -2/3,  1/3),
    ]

    # Round fractional cube coords to the nearest integer cube coord
    def cube_round(fr, fs, ft):
        r = round(fr)
        s = round(fs)
        t = round(ft)
        fr_diff = abs(fr - r)
        fs_diff = abs(fs - s)
        ft_diff = abs(ft - t)
        if fr_diff > fs_diff and fr_diff > ft_diff:
            r = -s - t
        elif fs_diff > ft_diff:
            s = -r - t
        else:
            t = -r - s
        return (r, s, t)

    vertex_set = {}  # (q, r, s) cube -> integer id
    vid = 0

    for (cq, cr, cs) in cells:
        for (dq, dr, ds) in corner_offsets_cube:
            fq, fr, fs = cq + dq, cr + dr, cs + ds
            vq, vr, vs = cube_round(fq, fr, fs)
            # Only keep vertices that belong to at least one cell in our patch
            key = (vq, vr, vs)
            if key not in vertex_set:
                vertex_set[key] = vid
                vid += 1

    n_verts = len(vertex_set)
    assert n_verts == 3 * m * m + 3 * m + 1, f"expected {3*m*m+3*m+1}, got {n_verts}"

    # --- 3. For each cell, find its 6 vertex ids in order ---
    cell_faces = []
    for (cq, cr, cs) in sorted(cells):
        face_vids = []
        for (dq, dr, ds) in corner_offsets_cube:
            fq, fr, fs = cq + dq, cr + dr, cs + ds
            vq, vr, vs = cube_round(fq, fr, fs)
            face_vids.append(vertex_set[(vq, vr, vs)])
        cell_faces.append(face_vids)

    # --- 4. Identify boundary faces ---
    # Interior hex cells have all 6 neighbours in the patch.
    # Boundary cells are those missing at least one neighbour.
    # Each boundary cell contributes its hexagonal face, but the
    # overall graph also has "boundary faces" that are NOT hex cells
    # of the original lattice — they are the complement polygons.
    #
    # For the colour code, ALL faces of the planar graph (including
    # boundary faces) contribute stabilizers.  We need to find ALL
    # faces of the planar graph formed by the edges.

    # Build edge list from cell faces
    edges = set()
    vertex_edges = defaultdict(list)  # vertex -> list of neighbor vertices
    for face in cell_faces:
        nv = len(face)
        for i in range(nv):
            a, b = face[i], face[(i + 1) % nv]
            edges.add((min(a, b), max(a, b)))
            vertex_edges[a].append(b)
            vertex_edges[b].append(a)

    # --- 5. Find ALL faces of the planar graph ---
    # Use the "left-hand walk" algorithm: for each directed edge (u -> v),
    # turn as far left as possible to find the next edge, tracing a face.

    # For each vertex, sort neighbors by angle (to determine "left turn")
    vertex_coords = {}
    for (vq, vr, vs), vid in vertex_set.items():
        x = vq + 0.5 * vr
        y = (math.sqrt(3) / 2) * vr
        vertex_coords[vid] = (x, y)

    # For each vertex, sort neighbors by angle from positive x-axis
    vertex_neighbors_sorted = {}
    for vid in range(n_verts):
        cx, cy = vertex_coords[vid]
        nbrs = vertex_edges[vid]
        # Compute angle of each neighbor
        angles = []
        for nbr in nbrs:
            nx, ny = vertex_coords[nbr]
            ang = math.atan2(ny - cy, nx - cx)
            angles.append((ang, nbr))
        angles.sort()
        vertex_neighbors_sorted[vid] = [nbr for _, nbr in angles]

    # Find faces using the "rotate around vertex" algorithm
    # For directed edge (u, v), the next edge in the face is (v, w)
    # where w is the neighbor of v that comes right after u in the
    # clockwise ordering around v.
    visited_edges = set()
    all_faces = []

    def next_edge(u, v):
        """Given directed edge u->v, find the next edge in the face
        by going to the rightmost turn at v."""
        nbrs = vertex_neighbors_sorted[v]
        # Find u's position in v's neighbor list
        idx = nbrs.index(u)
        # Go to the previous neighbor (clockwise = right turn)
        w = nbrs[(idx - 1) % len(nbrs)]
        return (v, w)

    for u in range(n_verts):
        for v in list(vertex_edges[u]):
            if (u, v) in visited_edges:
                continue
            # Trace the face
            face = []
            cu, cv = u, v
            while True:
                visited_edges.add((cu, cv))
                face.append(cu)
                cu, cv = next_edge(cu, cv)
                if cu == u and cv == v:
                    break
            all_faces.append(face)

    # --- 6. Build the face-vertex incidence matrix ---
    n_faces = len(all_faces)
    H = np.zeros((n_faces, n_verts), dtype=np.int8)
    for fi, face in enumerate(all_faces):
        for vi in face:
            H[fi, vi] = 1

    # Self-dual CSS: H_X = H_Z = H
    return H.copy(), H.copy()


def color_code_coords(m):
    """Per-qubit 2-D coordinates for the colour code."""
    # Same as the vertex positions we computed above
    cells = set()
    for q in range(m + 1):
        for r in range(m + 1 - q):
            s = -q - r
            cells.add((q, r, s))

    corner_offsets_cube = [
        (2/3, -1/3, -1/3),
        (1/3,  1/3, -2/3),
        (-1/3, 2/3, -1/3),
        (-2/3, 1/3,  1/3),
        (-1/3,-1/3,  2/3),
        (1/3, -2/3,  1/3),
    ]

    def cube_round(fr, fs, ft):
        r = round(fr)
        s = round(fs)
        t = round(ft)
        fr_diff = abs(fr - r)
        fs_diff = abs(fs - s)
        ft_diff = abs(ft - t)
        if fr_diff > fs_diff and fr_diff > ft_diff:
            r = -s - t
        elif fs_diff > ft_diff:
            s = -r - t
        else:
            t = -r - s
        return (r, s, t)

    vertex_set = {}
    vid = 0
    for (cq, cr, cs) in sorted(cells):
        for (dq, dr, ds) in corner_offsets_cube:
            fq, fr, fs = cq + dq, cr + dr, cs + ds
            vq, vr, vs = cube_round(fq, fr, fs)
            key = (vq, vr, vs)
            if key not in vertex_set:
                vertex_set[key] = vid
                vid += 1

    # Sort by vid to get coordinates in qubit order
    coords = [None] * len(vertex_set)
    for (vq, vr, vs), vid in vertex_set.items():
        x = vq + 0.5 * vr
        y = (math.sqrt(3) / 2) * vr
        coords[vid] = [float(x), float(y)]

    return coords


# ---------------------------------------------------------------------------
# Validation helper
# ---------------------------------------------------------------------------

def validate_and_stage(HX, HZ, *, name, construction, authors, family,
                       coordinates=None, layers=None, outdir="research/candidates",
                       trials=8000, seed=0):
    """Build submission, validate, stage if passed."""
    n = HX.shape[1]
    k = compute_k(HX, HZ)

    print(f"  Building submission for {name} ...")
    doc = make_submission(
        HX, HZ,
        name=name,
        construction=construction,
        authors=authors,
        family=family,
        references=["arXiv:quant-ph/0605138"],
        confidence="upper_bound",
        coordinates=coordinates,
        layers=layers,
        trials=trials,
        seed=seed,
    )

    # Quick sanity
    assert verify_css(HX, HZ), "CSS check failed"
    dval = doc["distance"]["d"]
    print(f"  n={n}, k={k}, d={dval}")

    # Stage
    os.makedirs(outdir, exist_ok=True)
    outpath = os.path.join(outdir, f"{n}-{k}-{dval}.json")
    errs = save_submission(doc, outpath)
    if errs:
        print(f"  WARNING schema errors: {errs}")
    print(f"  Saved to {outpath}")
    return doc


# ---------------------------------------------------------------------------
# Main: build and stage all targets
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--toric", action="store_true", help="Build edge toric codes")
    parser.add_argument("--color", action="store_true", help="Build color codes")
    parser.add_argument("--validate-only", action="store_true",
                        help="Only validate already-staged candidates")
    args = parser.parse_args()

    do_toric = args.toric or (not args.toric and not args.color)
    do_color = args.color or (not args.toric and not args.color)

    if do_toric:
        print("=" * 60)
        print("Edge toric codes [[2L²,2,L]]")
        print("=" * 60)
        for L in [9, 10, 11]:
            n = 2 * L * L
            print(f"\nL={L}: target [[{n},2,{L}]]")
            HX, HZ = build_toric_code(L)
            k = compute_k(HX, HZ)
            assert k == 2, f"expected k=2, got k={k}"
            assert verify_css(HX, HZ), "CSS failed"
            coords = toric_coords(L)
            doc = validate_and_stage(
                HX, HZ,
                name=f"[[{n},2,{L}]] edge toric code",
                construction=f"Standard toric code on {L}×{L} torus, "
                             f"distance {L}. Qubits on edges, "
                             f"star checks at vertices, plaquette checks on faces.",
                authors=["autoresearch"],
                family="topological",
                coordinates=coords,
                layers=1,
                trials=10000,
            )

    if do_color:
        print("\n" + "=" * 60)
        print("Triangular 6.6.6 colour codes")
        print("=" * 60)
        for m in range(2, 18):
            n = 3 * m * m + 3 * m + 1
            d = 2 * m + 1
            fname = f"codes/{n}-1-{d}.json"
            if os.path.exists(fname):
                print(f"\nm={m}: [[{n},1,{d}]] already on board, skipping")
                continue
            print(f"\nm={m}: building [[{n},1,{d}]]")
            HX, HZ = build_color_code(m)
            k = compute_k(HX, HZ)
            assert k == 1, f"expected k=1, got k={k}"
            assert verify_css(HX, HZ), "CSS failed"
            coords = color_code_coords(m)
            doc = validate_and_stage(
                HX, HZ,
                name=f"[[{n},1,{d}]] triangular 6.6.6 colour code",
                construction=f"Triangular 6.6.6 (hexagonal) colour code, "
                             f"m={m}, d=2m+1={d}, n=3m²+3m+1={n}. "
                             f"Self-dual CSS: H_X = H_Z = face-incidence matrix "
                             f"of a triangular patch of the {{6,3}} lattice.",
                authors=["autoresearch"],
                family="topological",
                coordinates=coords,
                layers=1,
                trials=10000,
            )
