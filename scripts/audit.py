#!/usr/bin/env python3
"""Check the complete corpus, frozen split/model, and data integrity."""
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
from fit import load_calibration, train, choose_reduced
from study import ROOT, configs, POLICIES


def main():
    cfg={c['id']:c for c in configs()}
    proto=json.loads((ROOT/'data/protocol.json').read_text())
    assert set(proto['training_ids']).isdisjoint(proto['test_ids'])
    stages=[('calibration','train',20,432),('reference','test',20,432),
            ('online','test',500,600),('transfer','test',500,108)]
    counts={};instances=0;first_test=float('inf');last_check=0
    for stage,split,horizon,expected_count in stages:
        paths=sorted((ROOT/'data'/stage).glob('*.csv'))
        assert len(paths)==expected_count,(stage,len(paths))
        expected_ids={cid for cid,c in cfg.items() if c['split']==split}
        if stage in ['calibration','reference']:
            names={f'{cid}__a{a}__r{r}.csv' for cid in expected_ids for a in range(12) for r in range(3)}
        else:
            policies=POLICIES if stage=='online' else ['warm','greedy','bestfixed']
            reps=5 if stage=='online' else 3
            names={f'{cid}__{pol}__r{r}.csv' for cid in expected_ids for pol in policies for r in range(reps)}
        assert {p.name for p in paths}==names
        for path in paths:
            meta=json.loads(path.with_suffix('.meta.json').read_text())
            assert meta['returncode']==0 and 'CHECK ' in meta['stderr'],path
            assert meta['csv_sha256']==hashlib.sha256(path.read_bytes()).hexdigest(),path
            assert meta['config']==cfg[path.stem.split('__')[0]],path
            d=pd.read_csv(path)
            assert list(d.t)==list(range(horizon)),path
            assert np.isfinite(d.to_numpy()).all() and (d.loop_s>0).all(),path
            if stage in ['reference','online']:
                first_test=min(first_test,meta['started_unix'])
            instances+=len(d);last_check+=1
        counts[stage]=len(paths)
    assert (ROOT/'data/model.txt').stat().st_mtime < first_test
    assert (ROOT/'data/protocol.json').stat().st_mtime < first_test
    X,C,ids,groups=load_calibration();hp=proto['selected']
    mean,scale,inv,b=train(X,C,hp['weight'],hp['ridge'])
    stored=np.loadtxt(ROOT/'data/model.txt')
    m=int(stored[4]);offset=5+m
    assert np.allclose(stored[offset:offset+6],mean,rtol=1e-12,atol=1e-12)
    assert np.allclose(stored[offset+6:offset+12],scale,rtol=1e-12,atol=1e-12)
    offset+=12
    for a in range(12):
        assert np.allclose(stored[offset:offset+36].reshape(6,6),inv[a],rtol=1e-12,atol=1e-12)
        assert np.allclose(stored[offset+36:offset+42],b[a],rtol=1e-12,atol=1e-12)
        offset+=42
    assert choose_reduced(C)==proto['reduced']
    result=dict(processes=last_check,logged_instances=instances,stage_counts=counts,
                hashes_verified=last_check,output_checks_passed=last_check,
                training_test_ids_disjoint=True,model_reproduces_from_training_only=True,
                protocol_and_model_predate_test=True,
                model_sha256=hashlib.sha256((ROOT/'data/model.txt').read_bytes()).hexdigest(),
                protocol_sha256=hashlib.sha256((ROOT/'data/protocol.json').read_bytes()).hexdigest())
    (ROOT/'results/validation').mkdir(parents=True,exist_ok=True)
    (ROOT/'results/validation/corpus_audit.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
