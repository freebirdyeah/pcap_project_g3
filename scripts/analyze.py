#!/usr/bin/env python3
"""Recreate every reported statistic and figure directly from the raw CSVs."""
import json
import hashlib
import re
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import wilcoxon
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator, FormatStrFormatter
from study import ROOT,configs,ARM_NAMES,POLICIES

LABELS={'static':'STATIC','gss':'GSS','bestfixed':'Best fixed','exhaustive':'Exhaustive',
        'qlearn':'Native Q-learning','ucb':'UCB','cold':'Cold LinUCB','greedy':'Prior greedy',
        'warm':'Warm LinUCB','reduced':'Warm reduced'}
ORDER=['static','gss','bestfixed','exhaustive','qlearn','ucb','cold','greedy','warm','reduced']
RESULT=ROOT/'results';FIG=ROOT/'paper/figures'

def geom(x):return float(np.exp(np.mean(np.log(x))))

def bootstrap_log_ratios(values,groups,seed=811,reps=10000):
    # Sample input configurations (both thread settings together), then paired
    # run blocks within each configuration. Six inputs are independent clusters.
    rng=np.random.default_rng(seed);keys=sorted(set(groups));vals=[]
    clustered=[np.asarray(values)[np.flatnonzero(groups==key)] for key in keys]
    if len({len(v) for v in clustered})==1:
        arr=np.stack(clustered)
        outer=rng.integers(0,len(keys),size=(reps,len(keys),1))
        inner=rng.integers(0,arr.shape[1],size=(reps,len(keys),arr.shape[1]))
        estimates=np.exp(arr[outer,inner].mean(axis=(1,2)))
        return [float(x) for x in np.quantile(estimates,[.025,.975])]
    for _ in range(reps):
        sample=[]
        for key in rng.choice(keys,len(keys),replace=True):
            ix=np.flatnonzero(groups==key)
            sample.extend(values[rng.choice(ix,len(ix),replace=True)])
        vals.append(np.exp(np.mean(sample)))
    return [float(x) for x in np.quantile(vals,[.025,.975])]

def main():
    RESULT.mkdir(exist_ok=True);FIG.mkdir(parents=True,exist_ok=True)
    cfg={c['id']:c for c in configs()};reference=[]
    test_ids={cid for cid,c in cfg.items() if c['split']=='test'}
    expected={f'{cid}__{pol}__r{rep}.csv' for cid in test_ids
              for pol in POLICIES for rep in range(5)}
    actual={p.name for p in (ROOT/'data/online').glob('*.csv')}
    assert expected==actual,dict(missing=sorted(expected-actual),unexpected=sorted(actual-expected))
    for p in sorted((ROOT/'data/reference').glob('*.csv')):
        cid,aa,rr=p.stem.split('__');df=pd.read_csv(p)
        meta=json.loads(p.with_suffix('.meta.json').read_text())
        assert len(df)==20 and meta['returncode']==0 and 'CHECK ' in meta['stderr']
        assert meta['csv_sha256']==hashlib.sha256(p.read_bytes()).hexdigest()
        reference.append(dict(scenario=cid,arm=int(aa[1:]),rep=int(rr[1:]),
                              median=float(df.loc[df.t>0,'loop_s'].median()),
                              mean=float(df.loc[df.t>0,'loop_s'].mean())))
    assert len(reference)==432
    ref=pd.DataFrame(reference)
    rmed=ref.groupby(['scenario','arm'])['median'].median().unstack()
    oracle=rmed.min(axis=1);best=rmed.idxmin(axis=1)
    normalized=rmed.div(oracle,axis=0);normalized.columns=ARM_NAMES
    normalized.to_csv(RESULT/'fixed_arm_slowdowns.csv')
    runs=[];trajectories=[];oh=[];selections=[]
    for path in sorted((ROOT/'data/online').glob('*.csv')):
        cid,pol,rep=path.stem.split('__');rep=int(rep[1:]);c=cfg[cid]
        df=pd.read_csv(path);meta=json.loads(path.with_suffix('.meta.json').read_text())
        assert len(df)==500 and list(df.t)==list(range(500)),path
        assert meta['returncode']==0 and 'CHECK ' in meta['stderr']
        assert meta['csv_sha256']==hashlib.sha256(path.read_bytes()).hexdigest()
        assert np.all(df.loop_s>0) and np.all(np.isfinite(df.select_dtypes('number')))
        cost=df.loop_s+df.decision_s+df.update_s
        wall=float(re.search(r'WALL ([0-9.eE+-]+)',meta['stderr']).group(1))
        for h in [50,144,500]:
            runs.append(dict(scenario=cid,input=c['kind']+'_s'+str(c['seed']),
                             kind=c['kind'],p=c['p'],policy=pol,rep=rep,horizon=h,
                             time_s=float(cost.iloc[:h].sum()),
                             loop_s=float(df.loop_s.iloc[:h].sum()),
                             overhead_s=float((df.decision_s+df.update_s).iloc[:h].sum()),
                             reference_s=float(oracle[cid]*h),
                             slowdown=float(cost.iloc[:h].sum()/(oracle[cid]*h)),
                             wall_s=wall,oracle_arm=int(best[cid])))
        traj=np.cumsum(cost.values)/(np.arange(1,501)*oracle[cid])
        trajectories.append((cid,pol,rep,traj))
        oh.append(dict(policy=pol,median_us=float(np.median(df.decision_s+df.update_s)*1e6),
                       p95_us=float(np.quantile(df.decision_s+df.update_s,.95)*1e6),
                       wall_gap=wall/float(cost.sum())-1))
        if pol!='qlearn':
            selections.append(dict(scenario=cid,policy=pol,rep=rep,
                                   distinct_arms=int(df.arm.nunique()),
                                   distinct_first50=int(df.loc[df.t<50,'arm'].nunique()),
                                   switch_count=int((df.arm.diff().fillna(0)!=0).sum()),
                                   modal_arm=int(df.arm.mode().iloc[0]),
                                   modal_fraction=float(df.arm.value_counts(normalize=True).iloc[0])))
    runs=pd.DataFrame(runs);runs.to_csv(RESULT/'run_metrics.csv',index=False)
    overhead=pd.DataFrame(oh);overhead.to_csv(RESULT/'overhead.csv',index=False)
    selections=pd.DataFrame(selections);selections.to_csv(RESULT/'arm_selections.csv',index=False)
    selection_summary=selections.groupby('policy')[['distinct_arms','distinct_first50','switch_count','modal_fraction']].median()
    selection_summary.to_csv(RESULT/'selection_summary.csv')
    summary=[];comparisons=[]
    for h in [50,144,500]:
        d=runs[runs.horizon==h];pivot=d.pivot(index=['scenario','rep','input'],columns='policy',values='time_s')
        for pol in ORDER:
            dd=d[d.policy==pol]
            summary.append(dict(policy=pol,horizon=h,geomean_slowdown=geom(dd.slowdown),
                                median_slowdown=float(dd.slowdown.median()),
                                total_measured_s=float(dd.time_s.sum())))
        for candidate in ['warm','reduced']:
            for base in ['qlearn','exhaustive','bestfixed','cold','ucb','greedy']:
                logs=np.log((pivot[base]/pivot[candidate]).values)
                groups=pivot.index.get_level_values('input').to_numpy()
                ci=bootstrap_log_ratios(logs,groups)
                # Thread counts and repeated runs are not independent samples.
                input_logs=pd.Series(logs,index=groups).groupby(level=0).mean().values
                p=float(wilcoxon(input_logs,alternative='two-sided').pvalue) if np.any(input_logs!=0) else 1.
                comparisons.append(dict(candidate=candidate,baseline=base,horizon=h,
                    speedup=geom(np.exp(logs)),ci_low=ci[0],ci_high=ci[1],p_raw=p,
                    input_wins=int(np.sum(input_logs>0)),inputs=len(input_logs)))
    summary=pd.DataFrame(summary);summary.to_csv(RESULT/'summary.csv',index=False)
    comparison=pd.DataFrame(comparisons)
    # Holm adjustment across six comparisons, separately per candidate and H.
    comparison['p_holm']=0.
    for _,g in comparison.groupby(['candidate','horizon']):
        ix=g.p_raw.sort_values().index
        corrected=np.maximum.accumulate([(len(ix)-j)*comparison.loc[i,'p_raw'] for j,i in enumerate(ix)])
        comparison.loc[ix,'p_holm']=np.minimum(corrected,1.)
    comparison.to_csv(RESULT/'paired_comparisons.csv',index=False)
    family=runs[runs.horizon==500].groupby(['kind','policy']).slowdown.apply(geom).unstack()
    family.to_csv(RESULT/'family_summary.csv')
    plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False,
                         'pdf.fonttype':42,'ps.fonttype':42})
    fig,ax=plt.subplots(figsize=(7,3.4))
    im=ax.imshow(np.log2(normalized.values),aspect='auto',cmap='YlOrRd',vmin=0,
                 vmax=max(.1,float(np.log2(normalized.values).max())))
    for i in range(len(normalized)):
        for j in range(12):
            value=normalized.values[i,j]
            ax.text(j,i,f'{value:.2f}',ha='center',va='center',fontsize=5.5,
                    color='white' if np.log2(value)>.65*im.norm.vmax else 'black')
    ax.set_xticks(range(12),ARM_NAMES,rotation=40,ha='right');ax.set_yticks(range(len(normalized)),normalized.index)
    cb=fig.colorbar(im,ax=ax);cb.set_label('log2 slowdown to best fixed arm')
    fig.tight_layout();fig.savefig(FIG/'portfolio.pdf');plt.close(fig)
    fig,axs=plt.subplots(1,3,figsize=(7.1,2.7),sharey=False)
    colors={'exhaustive':'#2b8cbe','qlearn':'#b2182b','ucb':'#7b3294','cold':'#999999',
            'greedy':'#d8a500','warm':'#1b7837','reduced':'#e08214'}
    for ax,kind in zip(axs,['mandelbrot','triad','triangle']):
        for pol in colors:
            arr=np.array([tr for cid,pp,r,tr in trajectories if pp==pol and cfg[cid]['kind']==kind])
            ax.plot(range(1,501),np.exp(np.mean(np.log(arr),axis=0)),label=LABELS[pol],color=colors[pol])
        ax.axvline(144,color='black',lw=.7,ls=':');ax.axhline(1,color='black',lw=.6,ls='--')
        ax.set_title(kind.capitalize());ax.set_xlabel('Loop instance')
        ax.yaxis.set_major_locator(MaxNLocator(4))
        ax.yaxis.set_major_formatter(FormatStrFormatter('%.2f'))
        ax.grid(axis='y',alpha=.18,linewidth=.5)
    axs[0].set_ylabel('Cumulative slowdown to fixed-arm reference')
    handles,labels=axs[0].get_legend_handles_labels();fig.legend(handles,labels,ncol=4,loc='upper center',bbox_to_anchor=(.5,1.1),fontsize=7)
    fig.tight_layout();fig.savefig(FIG/'trajectories.pdf',bbox_inches='tight');plt.close(fig)
    fig,ax=plt.subplots(figsize=(6.8,3))
    c=comparison[(comparison.candidate=='warm')&(comparison.horizon==500)]
    ax.errorbar(c.speedup,range(len(c)),xerr=[c.speedup-c.ci_low,c.ci_high-c.speedup],fmt='o',color='#1b7837',capsize=3)
    ax.axvline(1,color='black',ls='--',lw=.8);ax.set_yticks(range(len(c)),[LABELS[x] for x in c.baseline])
    ax.set_xlabel('Warm LinUCB speedup (baseline time / warm time); 95% cluster bootstrap CI')
    fig.tight_layout();fig.savefig(FIG/'comparisons.pdf');plt.close(fig)
    # All final manuscript numbers are collected in one auditable JSON file.
    final=runs[runs.horizon==500]
    run_cv=final.groupby(['scenario','policy']).time_s.agg(lambda x:float(x.std(ddof=1)/x.mean()))
    stable=final[final.rep!=3].pivot(index=['scenario','rep','input'],columns='policy',values='time_s')
    sensitivity=[]
    for base in ['qlearn','exhaustive','bestfixed']:
        logs=np.log((stable[base]/stable.warm).values)
        ci=bootstrap_log_ratios(logs,stable.index.get_level_values('input').to_numpy())
        sensitivity.append(dict(baseline=base,speedup=geom(np.exp(logs)),ci_low=ci[0],ci_high=ci[1]))
    report={'run_count':len(overhead),'loop_instances':int(len(overhead)*500),
            'reference_runs':len(ref),'test_scenarios':len(rmed),
            'independent_test_inputs':6,'checks_passed':len(overhead),
            'measured_online_s':float(runs[runs.horizon==500].time_s.sum()),
            'summary':summary.to_dict('records'),'comparisons':comparison.to_dict('records'),
            'family':family.to_dict('index'),
            'overhead_us':overhead.groupby('policy').median_us.median().to_dict(),
            'wall_gap_median':float(overhead.wall_gap.median()),
            'selection_summary':selection_summary.to_dict('index'),
            'median_between_run_cv':float(run_cv.median()),
            'reference_max_slowdown':float(normalized.values.max()),
            'exclude_interrupted_block':sensitivity}
    (RESULT/'report.json').write_text(json.dumps(report,indent=2))
    print(summary[summary.horizon==500].to_string(index=False))
    print(comparison[(comparison.candidate=='warm')&(comparison.horizon==500)].to_string(index=False))
    print(f'Validated {len(overhead)} runs, {len(overhead)*500} loop instances')

if __name__=='__main__':main()
