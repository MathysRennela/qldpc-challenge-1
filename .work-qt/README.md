# Ancillary files: parity-check matrices for quantum Tanner code instances

This archive contains parity-check matrices (CSS form) for the quantum Tanner code
instances reported in the accompanying paper. 

## Directory layout

The zip contains three directories, organized by the choice of local codes:

- `633x212/` : A-side local code `[6,3,3]` (shortened Hamming), B-side local code `[2,1,2]` (repetition).
- `844x212/` : A-side local code `[8,4,4]` (extended Hamming), B-side local code `[2,1,2]` (repetition).
- `633x633/` : A-side local code `[6,3,3]`, B-side local code `[6,3,3]`.

Each directory contains one pair of files per code instance: an X-check matrix `HX` and
a Z-check matrix `HZ`.

## File naming convention

Files are named
HX_<G><n><k><d>.mtx
HZ<G><n><k>_<d>.mtx

where:
- `<G>` is a short label for the lift group (as used in the paper tables; e.g. `C7`, `Q8`, `C2xC2`, `C2xC2xC2xC3`, etc.).
- `<n>` is the number of physical qubits (number of columns of `HX`/`HZ`).
- `<k>` is the number of logical qubits (CSS dimension).
- `<d>` is the estimated distance value reported in the paper for that instance.

Within a given instance, `HX_<G>_<n>_<k>_<d>.mtx` and `HZ_<G>_<n>_<k>_<d>.mtx`
always share the same `<G>,<n>,<k>,<d>`.

## Matrix format

All matrices are provided in **Matrix Market** format (`.mtx`), as sparse
coordinate data.

Interpretation:
- `HX` and `HZ` are binary matrices over GF(2).
- Columns correspond to qubits.
- Rows correspond to stabilizer generators (X-type for `HX`, Z-type for `HZ`).
- Valid CSS condition: `HX * HZ^T = 0 (mod 2)`.


## Citation

If you use these matrices in academic work, please cite the accompanying paper. 
