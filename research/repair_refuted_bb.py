#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'research/kit'),str(ROOT/'verify')]
from submit import make_submission
from heuristic_distance import _matrix
src=ROOT/'research/candidates/bb-weight26-312-10-48-73b991d8c5c9236f.json'
d=json.loads(src.read_text())
hx=_matrix(d['checks']['X'],d['n']); hz=_matrix(d['checks']['Z'],d['n'])
new=make_submission(hx,hz,name='[[312,10,d<=43]] BB weight-26 corrected',construction=d['provenance']['construction']+' Deep RIS confirmation found a weight-43 logical, correcting the earlier d<=48 screen claim.',authors=d['provenance']['authors'],family=d.get('family'),references=d['provenance'].get('references',[]),confidence='upper_bound',trials=8000,seed=454506451)
out=ROOT/'research/candidates/bb-weight26-312-10-43-corrected.json'; out.write_text(json.dumps(new,indent=2)+'\n'); print(out.relative_to(ROOT))
