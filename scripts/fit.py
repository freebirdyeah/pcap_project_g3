#!/usr/bin/env python3
"""Train and validate solely on the calibration split, then freeze the protocol."""
import json
from pathlib import Path
import sys
import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import linkage, fcluster
from scipy.spatial.distance import pdist, squareform
from study import ROOT, configs, ARM_NAMES

D,K=6,12

def load_calibration():
    features=[];costs=[];ids=[];groups=[]
    for c in configs():
        if c['split']!='train':continue
        times=[];probes=[]
        for a in range(K):
            ts=[]
            for rep in range(3):
                p=ROOT/'data/calibration'/f"{c['id']}__a{a}__r{rep}.csv"
                df=pd.read_csv(p);ts.extend(df.loc[df.t>0,'loop_s'])
                probes.append(df.iloc[0][['loop_s','lib','cv']].values.astype(float))
            times.append(np.median(ts))
        probe=np.median(probes,axis=0)
        features.append([1,np.log2(c['n']),np.log2(c['p']),np.log2(probe[0]),probe[1],probe[2]])
        costs.append(times);ids.append(c['id']);groups.append(f"{c['kind']}_{c['seed']}")
    return np.array(features),np.array(costs),ids,np.array(groups)

def train(X,C,weight,ridge):
    mean=X.mean(axis=0);scale=X.std(axis=0);mean[0]=0;scale[0]=1
    scale=np.maximum(scale,1e-8);Z=(X-mean)/scale
    # Each scenario contributes one median label per arm, rather than treating
    # serially correlated loop rows as independent evidence.
    rewards=np.clip(-np.log(C/C[:,[0]])/np.log(4),-1,1)
    A=ridge*np.eye(D)+weight*Z.T@Z
    inv=np.linalg.inv(A)
    b=weight*np.einsum('nd,nk->kd',Z,rewards)
    return mean,scale,np.repeat(inv[None,:,:],K,axis=0),b

def simulate(x,c,model,alpha,H=200):
    mean,scale,inv,b=model
    inv=inv.copy();b=b.copy();x=(x-mean)/scale
    rewards=np.clip(-np.log(c/c[0])/np.log(4),-1,1)
    total=c[0]
    for t in range(1,H):
        v=inv@x
        a=int(np.argmax(np.sum(v*b,axis=1)+alpha*np.sqrt(np.maximum(0,v@x))))
        total+=c[a];u=v[a];inv[a]-=np.outer(u,u)/(1+x@u);b[a]+=rewards[a]*x
    return total/(H*min(c))

def choose_reduced(C):
    remaining=np.array([i for i in range(K) if i not in [0,4]])
    perf=np.log(C/C.min(axis=1,keepdims=True)).T
    dist=squareform(pdist(perf[remaining]))
    labels=fcluster(linkage(perf[remaining],method='average'),4,criterion='maxclust')
    chosen=[0,4]
    for g in np.unique(labels):
        ix=np.flatnonzero(labels==g)
        chosen.append(int(remaining[ix[np.argmin(dist[np.ix_(ix,ix)].sum(axis=1))]]))
    return sorted(set(chosen))

def main():
    X,C,ids,groups=load_calibration();validation=[]
    for weight in [.25,1.,4.]:
        for ridge in [.1,1.]:
            for alpha in [.025,.1,.4]:
                vals=[]
                for group in np.unique(groups):
                    tr=groups!=group;model=train(X[tr],C[tr],weight,ridge)
                    vals.extend(simulate(x,c,model,alpha) for x,c in zip(X[~tr],C[~tr]))
                score=float(np.exp(np.mean(np.log(vals))))
                validation.append(dict(weight=weight,ridge=ridge,alpha=alpha,score=score))
    best=min(validation,key=lambda d:d['score'])
    mean,scale,inv,b=train(X,C,best['weight'],best['ridge'])
    reduced=choose_reduced(C)
    fixed=int(np.argmin(np.mean(np.log(C/C[:,[0]]),axis=0)))
    values=[str(D),str(K),repr(best['alpha']),str(fixed),str(len(reduced)),
            *map(str,reduced),*map(repr,mean.tolist()),*map(repr,scale.tolist())]
    for a in range(K):values.extend(map(repr,inv[a].ravel().tolist()));values.extend(map(repr,b[a].tolist()))
    (ROOT/'data/model.txt').write_text('\n'.join(values)+'\n')
    proto=dict(horizon=500,repetitions=5,training_ids=ids,
               test_ids=[c['id'] for c in configs() if c['split']=='test'],
               selected=best,validation=validation,reduced=reduced,
               reduced_names=[ARM_NAMES[i] for i in reduced],best_fixed=fixed,
               best_fixed_name=ARM_NAMES[fixed],feature_dim=D,
               feature_names=['intercept','log2_N','log2_P','log2_static_probe_s','static_lib','static_cv'],
               validation_method='leave-one-kind-and-seed-out; deterministic median-cost surrogate, 200 rounds',
               calibration_total_s=float(C.sum()),
               notes='Validation uses calibration measurements only; simulated validation is not a measured online result.')
    (ROOT/'data/protocol.json').write_text(json.dumps(proto,indent=2))
    pd.DataFrame(C,index=ids,columns=ARM_NAMES).to_csv(ROOT/'data/calibration_medians.csv')
    print(json.dumps({k:proto[k] for k in ['selected','reduced_names','best_fixed_name']},indent=2))

if __name__=='__main__':main()
