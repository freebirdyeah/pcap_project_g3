#!/usr/bin/env python3
"""Sequential, resumable experiment orchestration; no synthetic test timings."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import random
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
ARM_NAMES = ['STATIC','SS','TSS','AutoLLVM','GSS','mFAC2','StaticSteal',
             'AWFB','AWFC','AWFD','AWFE','mAF']
POLICIES = ['static','gss','bestfixed','exhaustive','qlearn','ucb','cold',
            'greedy','warm','reduced']
ENV = dict(os.environ, OMP_PLACES='{0},{2},{4},{6}',OMP_PROC_BIND='close',
           OMP_DYNAMIC='FALSE', OMP_WAIT_POLICY='ACTIVE',KMP_BLOCKTIME='200',
           KMP_CPU_SPEED='3200', KMP_Golden_Chunksize='1',
           KMP_RL_ALPHA='0.5',KMP_RL_GAMMA='0.5',KMP_RL_ALPHA_DECAY='0.05',
           KMP_RL_EPS_DECAY='0',KMP_RL_REWARD='looptime',KMP_RL_INIT='zero',
           KMP_RL_POLICY='explore_first',KMP_RL_DECAY='exponential',
           KMP_RL_AVG_WINDOW='10',INVERSE_REWARD_MULT='10',
           KMP_RL_REWARD_NUM='0.01,-2.0,-4.0',KMP_RL_TAU='1.5',
           KMP_RL_EPSILON='0.9',KMP_RL_AGENT_STATS='notOutputtingStats',
           OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='4')

def configs():
    sizes={'mandelbrot':[16384,65536,25600,50176],
           'triad':[262144,1048576,393216,786432],
           'triangle':[512,2048,1024,1536]}
    return [dict(id=f'{kind}_s{s}_p{p}',kind=kind,n=n,seed=s,p=p,
                 split='train' if s<2 else 'test')
            for kind,ns in sizes.items() for s,n in enumerate(ns) for p in [2,4]]

def run(c,policy,horizon,out,model='none',arm=0,golden=True):
    out=Path(out);out.parent.mkdir(parents=True,exist_ok=True)
    if out.exists() and out.with_suffix('.meta.json').exists():return
    actual={'static':'fixed','gss':'fixed'}.get(policy,policy)
    if policy=='gss':arm=4
    env=ENV.copy();env['KMP_Golden_Chunksize']='1' if golden else '0'
    cmd=[str(ROOT/'build/experiment'),c['kind'],str(c['n']),str(c['seed']),str(c['p']),
         actual,str(horizon),str(model),str(out),str(arm)]
    start=time.time()
    with out.with_suffix('.stdout.txt').open('w') as log:
        r=subprocess.run(cmd,env=env,cwd=ROOT,stdout=log,stderr=subprocess.PIPE,
                         text=True,timeout=180)
    meta=dict(config=c,policy=policy,horizon=horizon,arm=arm,golden=golden,
              command=cmd,started_unix=start,elapsed_s=time.time()-start,
              stderr=r.stderr,returncode=r.returncode)
    if r.returncode or 'CHECK ' not in r.stderr:
        out.with_suffix('.failed.json').write_text(json.dumps(meta,indent=2))
        raise RuntimeError(f'{out}: {r.stderr}')
    meta['csv_sha256']=hashlib.sha256(out.read_bytes()).hexdigest()
    out.with_suffix('.meta.json').write_text(json.dumps(meta,indent=2))

def measure(split):
    jobs=[(c,a,r) for c in configs() if c['split']==split
          for a in range(12) for r in range(3)]
    random.Random(20261023+(split=='test')).shuffle(jobs)
    for i,(c,a,r) in enumerate(jobs):
        out=ROOT/'data'/('calibration' if split=='train' else 'reference')/f"{c['id']}__a{a}__r{r}.csv"
        run(c,'fixed',20,out,arm=a)
        if i%24==0:print(f'{split} calibration {i+1}/{len(jobs)}',flush=True)

def online():
    protocol=json.loads((ROOT/'data/protocol.json').read_text())
    model=ROOT/'data/model.txt'
    for rep in range(protocol['repetitions']):
        jobs=[(c,policy) for c in configs() if c['split']=='test' for policy in POLICIES]
        random.Random(20261023+rep).shuffle(jobs)
        for i,(c,policy) in enumerate(jobs):
            out=ROOT/'data/online'/f"{c['id']}__{policy}__r{rep}.csv"
            run(c,policy,protocol['horizon'],out,model)
            if i%10==0:print(f'online block {rep+1}/{protocol["repetitions"]}: {i+1}/{len(jobs)}',flush=True)

def manifest():
    commands={'lscpu':['lscpu'],'topology':['lscpu','-e=CPU,CORE,SOCKET,NODE'],
              'uname':['uname','-a'],'compiler':['clang++-16','--version'],
              'lb4omp_commit':['git','-C',str(ROOT/'vendor/LB4OMP'),'rev-parse','HEAD']}
    info={k:subprocess.check_output(v,text=True) for k,v in commands.items()}
    import platform,numpy,scipy,matplotlib,pandas
    info.update(python=platform.python_version(),numpy=numpy.__version__,
                scipy=scipy.__version__,matplotlib=matplotlib.__version__,pandas=pandas.__version__,
                environment={k:v for k,v in ENV.items() if k.startswith(('OMP','KMP','INVERSE'))},
                captured_unix=time.time(),configs=configs())
    (ROOT/'data').mkdir(exist_ok=True)
    (ROOT/'data/environment.json').write_text(json.dumps(info,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=['manifest','train','reference','online','pilot'])
    args=parser.parse_args()
    if args.stage=='manifest':manifest()
    elif args.stage=='train':measure('train')
    elif args.stage=='reference':measure('test')
    elif args.stage=='online':online()
    else:
        for c in [x for x in configs() if x['seed']==0 and x['p']==4]:
            for a in range(12):
                run(c,'fixed',6,ROOT/'data/pilot'/f"{c['id']}__a{a}.csv",arm=a)
            print('pilot',c['kind'],'complete',flush=True)
