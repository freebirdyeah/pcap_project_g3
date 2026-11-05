#!/usr/bin/env python3
"""Exploratory leave-one-workload-family-out test; no test labels are fitted."""
import json
import random
import numpy as np
from fit import load_calibration, train, choose_reduced, D, K
from study import ROOT, configs, run


def main():
    X, C, ids, groups = load_calibration()
    protocol = json.loads((ROOT / 'data/protocol.json').read_text())
    hp = protocol['selected']
    paths = {}
    training = {}
    for kind in ['mandelbrot', 'triad', 'triangle']:
        mask = np.array([not cid.startswith(kind + '_') for cid in ids])
        mean, scale, inv, b = train(X[mask], C[mask], hp['weight'], hp['ridge'])
        reduced = choose_reduced(C[mask])
        fixed = int(np.argmin(np.mean(np.log(C[mask] / C[mask, 0][:, None]), axis=0)))
        values = [str(D), str(K), repr(hp['alpha']), str(fixed), str(len(reduced)),
                  *map(str, reduced), *map(repr, mean.tolist()), *map(repr, scale.tolist())]
        for a in range(K):
            values.extend(map(repr, inv[a].ravel().tolist()))
            values.extend(map(repr, b[a].tolist()))
        path = ROOT / 'data' / f'model_without_{kind}.txt'
        path.write_text('\n'.join(values) + '\n')
        paths[kind] = path
        training[kind] = [cid for cid, keep in zip(ids, mask) if keep]
    (ROOT / 'data/transfer_protocol.json').write_text(json.dumps(dict(
        exploratory=True, horizon=500, repetitions=3, hyperparameters=hp,
        training_ids=training, policies=['warm', 'greedy', 'bestfixed'],
        notes='Added after primary protocol freeze. Uses the primary training-only hyperparameters unchanged.'
    ), indent=2))
    for rep in range(3):
        jobs = [(c, pol) for c in configs() if c['split'] == 'test'
                for pol in ['warm', 'greedy', 'bestfixed']]
        random.Random(6421 + rep).shuffle(jobs)
        for i, (c, pol) in enumerate(jobs):
            out = ROOT / 'data/transfer' / f"{c['id']}__{pol}__r{rep}.csv"
            run(c, pol, 500, out, paths[c['kind']])
            if i % 12 == 0:
                print(f'transfer block {rep + 1}/3: {i + 1}/{len(jobs)}', flush=True)


if __name__ == '__main__':
    main()
