#!/usr/bin/env python3
"""Audit and summarize the explicitly exploratory family-transfer campaign."""
import hashlib
import json
import numpy as np
import pandas as pd
from analyze import bootstrap_log_ratios, geom, RESULT
from study import ROOT, configs


def main():
    cfg={c['id']:c for c in configs()}
    expected={f"{c['id']}__{pol}__r{rep}.csv" for c in configs() if c['split']=='test'
              for pol in ['warm','greedy','bestfixed'] for rep in range(3)}
    actual={p.name for p in (ROOT/'data/transfer').glob('*.csv')}
    assert expected==actual,sorted(expected-actual)
    rows=[]
    for path in sorted((ROOT/'data/transfer').glob('*.csv')):
        cid,policy,rep=path.stem.split('__');c=cfg[cid]
        meta=json.loads(path.with_suffix('.meta.json').read_text())
        assert meta['csv_sha256']==hashlib.sha256(path.read_bytes()).hexdigest()
        assert meta['returncode']==0 and 'CHECK ' in meta['stderr']
        df=pd.read_csv(path)
        assert len(df)==500 and list(df.t)==list(range(500))
        cost=df.loop_s+df.decision_s+df.update_s
        rows.append(dict(scenario=cid,input=c['kind']+'_s'+str(c['seed']),kind=c['kind'],
                         policy=policy,rep=int(rep[1:]),time_s=float(cost.sum())))
    data=pd.DataFrame(rows);data.to_csv(RESULT/'transfer_runs.csv',index=False)
    pivot=data.pivot(index=['scenario','input','kind','rep'],columns='policy',values='time_s')
    comparisons=[]
    for base in ['bestfixed','greedy']:
        logs=np.log((pivot[base]/pivot.warm).values)
        ci=bootstrap_log_ratios(logs,pivot.index.get_level_values('input').to_numpy())
        comparisons.append(dict(baseline=base,speedup=geom(np.exp(logs)),ci_low=ci[0],ci_high=ci[1]))
    family={}
    for kind in ['mandelbrot','triad','triangle']:
        g=pivot.xs(kind,level='kind')
        family[kind]={base:geom(g[base]/g.warm) for base in ['bestfixed','greedy']}
    result=dict(exploratory=True,run_count=len(rows),loop_instances=len(rows)*500,
                comparisons=comparisons,family=family)
    (RESULT/'transfer_report.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
