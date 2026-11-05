#!/usr/bin/env python3
"""Secondary direct measurement: calibration calls also count as useful work."""
import json
import random
from pathlib import Path
import importlib.util

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('budget_study',HERE/'study.py')
study=importlib.util.module_from_spec(spec);spec.loader.exec_module(study)

def main():
    note=dict(secondary=True,semantics='exactly H total useful calls, including all calibration calls',
              horizons=[50,500],blocks=3,policies=['prior','budget4','exhaustive'],
              statement='No changes to the primary binary, fitted model, or frozen main protocol.')
    (HERE/'data/insitu_protocol.json').write_text(json.dumps(note,indent=2))
    model=HERE/'data/model.txt'
    for block in range(3):
        jobs=[(c,pol,h) for c in study.configs()
              for pol in ['prior','budget4','exhaustive'] for h in [50,500]]
        random.Random(900123+block).shuffle(jobs)
        for i,(c,label,h) in enumerate(jobs):
            trials={'prior':3,'budget4':12,'exhaustive':36}[label]
            policy={'prior':'prior','budget4':'budget','exhaustive':'exhaustive'}[label]
            budget={'prior':1,'budget4':4,'exhaustive':12}[label]
            out=HERE/'data/insitu'/f"{c['id']}__{label}__h{h}__b{block}.csv"
            study.run(c,policy,h-trials,out,'none' if label=='exhaustive' else model,budget,0,block)
            if i%36==0:print(f'in-situ block {block+1}/3: {i+1}/{len(jobs)}',flush=True)

if __name__=='__main__':main()
