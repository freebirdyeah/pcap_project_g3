#!/usr/bin/env python3
"""Fresh budget/quality measurements, with wall and process CPU accounting."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import random
import resource
import subprocess
import time
import sys
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'scripts'))
from study import ENV,ARM_NAMES,configs as old_configs
from fit import train

POLICIES=['bestfixed','prior','budget2','budget4','budget8','random4','exhaustive']

def configs():
    sizes={'mandelbrot':[36864,57600,20736,43264],
           'triad':[524288,655360,458752,917504],
           'triangle':[768,1792,1280,1920]}
    return [dict(id=f'{kind}_s{seed}_p{p}',kind=kind,n=n,seed=seed,p=p,split='test')
            for kind,ns in sizes.items() for seed,n in zip(range(4,8),ns) for p in [2,4]]

def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def run(c,policy,horizon,out,model='none',budget=0,arm=0,rep=0):
    out=Path(out);out.parent.mkdir(parents=True,exist_ok=True)
    meta_path=Path(str(out)+'.meta.json')
    if out.exists() and meta_path.exists():
        old=json.loads(meta_path.read_text())
        assert old['csv_sha256']==digest(out)
        assert old['executable_sha256']==digest(ROOT/'build/tradeoff')
        return
    env=ENV.copy();env['TRADEOFF_RANDOM_SEED']=str(7381+rep*101+c['seed']*17+c['p'])
    cmd=[str(ROOT/'build/tradeoff'),c['kind'],str(c['n']),str(c['seed']),str(c['p']),
         policy,str(horizon),str(model),str(out),str(budget),str(arm)]
    before=resource.getrusage(resource.RUSAGE_CHILDREN);start=time.perf_counter()
    started=time.time()
    result=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True,timeout=180)
    elapsed=time.perf_counter()-start;after=resource.getrusage(resource.RUSAGE_CHILDREN)
    meta=dict(config=c,policy=policy,horizon=horizon,budget=budget,arm=arm,rep=rep,
              started_unix=started,process_wall_s=elapsed,
              process_cpu_s=(after.ru_utime+after.ru_stime-before.ru_utime-before.ru_stime),
              stderr=result.stderr,stdout=result.stdout,returncode=result.returncode,
              command=cmd,executable_sha256=digest(ROOT/'build/tradeoff'),
              model_sha256=None if model=='none' else digest(model),
              protocol_sha256=digest(HERE/'data/protocol.json'))
    if result.returncode or 'CHECK ' not in result.stderr:
        Path(str(out)+'.failed.json').write_text(json.dumps(meta,indent=2))
        raise RuntimeError(meta)
    meta['csv_sha256']=digest(out)
    meta['summary_sha256']=digest(str(out)+'.summary.json')
    meta_path.write_text(json.dumps(meta,indent=2))

def freeze():
    dest=HERE/'data';dest.mkdir(parents=True,exist_ok=True)
    protocol=dict(question='selection cost / CPU versus residual scheduling slowdown',
                  seed=202610231,blocks=5,horizon=500,prefixes=[10,50,100,500],
                  repeats_per_candidate=3,reference_observations=25,
                  budgets=[1,2,4,8,12],policies=POLICIES,
                  quality_tolerances=[.05,.10],training=old_configs(),testing=configs(),
                  prior=dict(weight=.25,ridge=1.,alpha=.025),
                  frozen_unix=time.time(),source_sha256=digest(HERE/'src/tradeoff.cpp'),
                  shared_source_sha256=digest(ROOT/'src/experiment.cpp'),
                  executable_sha256=digest(ROOT/'build/tradeoff'),
                  measurement='CLOCK_MONOTONIC wall and CLOCK_PROCESS_CPUTIME_ID CPU, all runtime threads',
                  semantics='additional calibration then 500 useful executions; no in-situ-work credit',
                  environment={k:v for k,v in ENV.items() if k.startswith(('OMP','KMP'))})
    path=dest/'protocol.json'
    if path.exists():raise RuntimeError('Frozen protocol already exists; preserve it.')
    path.write_text(json.dumps(protocol,indent=2))

def calibration():
    jobs=[(c,a,r) for c in old_configs() if c['split']=='train'
          for a in range(12) for r in range(3)]
    random.Random(202610231).shuffle(jobs)
    for i,(c,a,r) in enumerate(jobs):
        out=HERE/'data/calibration'/f"{c['id']}__a{a}__r{r}.csv"
        run(c,'calibrate',20,out,arm=a,rep=r)
        if i%36==0:print(f'calibration {i+1}/{len(jobs)}',flush=True)

def fit_model():
    started=time.perf_counter();cpu=time.process_time();features=[];costs=[];ids=[]
    for c in old_configs():
        if c['split']!='train':continue
        allprobes=[];armcost=[]
        for arm in range(12):
            samples=[]
            for r in range(3):
                df=pd.read_csv(HERE/'data/calibration'/f"{c['id']}__a{arm}__r{r}.csv")
                samples.extend(df.loc[df.phase=='payload','loop_s'])
                allprobes.extend(df.loc[df.phase=='probe',['loop_s','lib','cv']].to_numpy())
            armcost.append(float(np.median(samples)))
        probe=np.median(allprobes,axis=0)
        features.append([1,np.log2(c['n']),np.log2(c['p']),np.log2(probe[0]),probe[1],probe[2]])
        costs.append(armcost);ids.append(c['id'])
    X=np.array(features);C=np.array(costs)
    mean,scale,inv,b=train(X,C,.25,1.)
    fixed=int(np.argmin(np.log(C/C[:,[0]]).mean(axis=0)))
    values=[6,12,.025,fixed,12,*range(12),*mean,*scale]
    for arm in range(12):values.extend(inv[arm].ravel());values.extend(b[arm])
    path=HERE/'data/model.txt'
    if path.exists():raise RuntimeError('Frozen fitted model already exists; preserve it.')
    path.write_text('\n'.join(repr(float(v)) if isinstance(v,(float,np.floating)) else str(v) for v in values)+'\n')
    metas=[json.loads(p.read_text()) for p in (HERE/'data/calibration').glob('*.meta.json')]
    fitcost=dict(fit_wall_s=time.perf_counter()-started,fit_cpu_s=time.process_time()-cpu,
                 calibration_wall_s=sum(m['process_wall_s'] for m in metas),
                 calibration_cpu_s=sum(m['process_cpu_s'] for m in metas),
                 best_fixed=fixed,best_fixed_name=ARM_NAMES[fixed],training_ids=ids,
                 model_sha256=digest(path),fitted_unix=time.time())
    (HERE/'data/prior_cost.json').write_text(json.dumps(fitcost,indent=2))
    pd.DataFrame(C,index=ids,columns=ARM_NAMES).to_csv(HERE/'data/calibration_medians.csv')
    print(json.dumps(fitcost,indent=2),flush=True)

def evaluate():
    proto=json.loads((HERE/'data/protocol.json').read_text())
    fit=json.loads((HERE/'data/prior_cost.json').read_text());model=HERE/'data/model.txt'
    assert digest(model)==fit['model_sha256']
    for block in range(proto['blocks']):
        jobs=[(c,'reference',a) for c in configs() for a in range(12)]
        jobs.extend((c,pol,0) for c in configs() for pol in POLICIES)
        random.Random(202610231+block).shuffle(jobs)
        for i,(c,label,arm) in enumerate(jobs):
            stage='reference' if label=='reference' else 'online'
            out=HERE/'data'/stage/f"{c['id']}__{label if label!='reference' else 'a'+str(arm)}__b{block}.csv"
            policy=label;budget=0;use_model='none';horizon=500
            if label=='reference':horizon=proto['reference_observations']
            elif label=='bestfixed':policy='fixed';arm=fit['best_fixed']
            elif label.startswith('budget'):policy='budget';budget=int(label[6:]);use_model=model
            elif label=='prior':use_model=model;budget=1
            elif label=='random4':policy='random';budget=4
            elif label=='exhaustive':budget=12
            run(c,policy,horizon,out,use_model,budget,arm,block)
            if i%40==0:print(f'block {block+1}/{proto["blocks"]}: {i+1}/{len(jobs)}',flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=['freeze','calibrate','fit','evaluate'])
    stage=parser.parse_args().stage
    {'freeze':freeze,'calibrate':calibration,'fit':fit_model,'evaluate':evaluate}[stage]()
