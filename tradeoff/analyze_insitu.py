#!/usr/bin/env python3
"""Audit equal-useful-work comparisons and generate their manuscript table."""
import importlib.util
import json
from pathlib import Path
import sys
import numpy as np
import pandas as pd

HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
sys.path.insert(0,str(ROOT/'scripts'))
from analyze import bootstrap_log_ratios
spec=importlib.util.spec_from_file_location('budget_analysis',HERE/'analyze.py')
analysis=importlib.util.module_from_spec(spec);spec.loader.exec_module(analysis)

def main():
    expected={f"{c['id']}__{p}__h{h}__b{b}.csv" for c in analysis.study.configs()
              for p in ['prior','budget4','exhaustive'] for h in [50,500] for b in range(3)}
    paths=list((HERE/'data/insitu').glob('*.csv'))
    assert {p.name for p in paths}==expected
    rows=[];instances=0
    for path in sorted(paths):
        cid,policy,h,block=path.stem.split('__');h=int(h[1:]);block=int(block[1:])
        meta,s,d=analysis.verify(path)
        assert len(d)==h
        assert s['calibration_evaluations']=={'prior':3,'budget4':12,'exhaustive':36}[policy]
        instances+=len(d)
        rows.append(dict(scenario=cid,input=cid.rsplit('_p',1)[0],policy=policy,horizon=h,block=block,
                         wall_s=s['selection_wall_s']+s['payload_wall_s'],
                         cpu_s=s['selection_cpu_s']+s['payload_cpu_s']))
    df=pd.DataFrame(rows);df.to_csv(HERE/'results/insitu_runs.csv',index=False)
    results=[]
    for h in [50,500]:
        for policy in ['prior','budget4']:
            d=df[df.horizon==h]
            item=dict(policy=policy,horizon=h)
            for metric in ['wall','cpu']:
                p=d.pivot(index=['scenario','block','input'],columns='policy',values=metric+'_s')
                values=(p.exhaustive/p[policy]).to_numpy()
                item[metric+'_speedup']=float(np.exp(np.log(values).mean()))
                item[metric+'_ci']=bootstrap_log_ratios(np.log(values),p.index.get_level_values('input').to_numpy())
            results.append(item)
    report=dict(secondary=True,processes=len(df),logged_instances=instances,comparisons=results)
    (HERE/'results/insitu_report.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
