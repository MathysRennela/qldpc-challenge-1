#!/usr/bin/env python3
"""Run a bounded Python RIS check and persist any refutation witness."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'research' / 'kit'), str(ROOT / 'verify')]
import heuristic_distance as hd
from submit import make_submission, save_submission

def main():
    p = argparse.ArgumentParser()
    p.add_argument('path')
    p.add_argument('--trials', type=int, default=2500)
    p.add_argument('--seed', type=int, required=True)
    a = p.parse_args()
    path = Path(a.path); doc = json.loads(path.read_text())
    result = hd.estimate(doc, trials=a.trials, seed=a.seed, fast_trials=0)
    report = ROOT / 'research' / 'candidates' / (path.stem + f'.quick-confirmation-{a.seed}.json')
    report.write_text(json.dumps(result, indent=2) + '\n')
    if result['verdict'] != 'refuted':
        print(json.dumps({'report': str(report), 'verdict': result['verdict']})); return
    lighter = result['d_heuristic']
    side = next(s for s, v in result['sides'].items() if v.get('lightest_found') == lighter)
    support = result['sides'][side]['witness']
    hx = hd._matrix(doc['checks']['X'], doc['n'])
    hz = hd._matrix(doc['checks']['Z'], doc['n'])
    new_doc = make_submission(
        hx, hz,
        name=f"[[{doc['n']},{doc['k']},d<={lighter}]] corrected campaign candidate",
        construction=doc['provenance']['construction'] +
                     f" Quick fresh RIS confirmation found a {side}-logical of weight {lighter}.",
        authors=doc['provenance']['authors'], family=doc.get('family'),
        confidence='upper_bound', trials=2000, seed=a.seed)
    stem = path.stem + f'-corrected-{lighter}'
    out = ROOT / 'research' / 'candidates' / f'{stem}.json'
    save_submission(new_doc, str(out))
    print(json.dumps({'report': str(report), 'corrected': str(out),
                      'side': side, 'weight': lighter, 'witness_weight': len(support)}, indent=2))
if __name__ == '__main__': main()
