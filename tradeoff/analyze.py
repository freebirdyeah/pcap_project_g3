#!/usr/bin/env python3
"""Audit fresh measurements and quantify tuning/quality/deployment trade-offs."""
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
sys.path.insert(0,str(ROOT/'scripts'))
from analyze import bootstrap_log_ratios
from study import ARM_NAMES
# Load the new configuration module without shadowing the old study import.
import importlib.util
spec=importlib.util.spec_from_file_location('budget_study',HERE/'study.py')
study=importlib.util.module_from_spec(spec);spec.loader.exec_module(study)
LABELS={'bestfixed':'Best fixed','prior':'Prior only','budget2':'Guided 2',
        'budget4':'Guided 4','budget8':'Guided 8','random4':'Random 4','exhaustive':'Full 12'}
ORDER=list(LABELS)
RESULT=HERE/'results';FIG=HERE/'paper/figures'

def geom(x):return float(np.exp(np.log(np.asarray(x)).mean()))
def ci_ratio(values,groups):
    return bootstrap_log_ratios(np.log(np.asarray(values)),np.asarray(groups))

def ci_fraction(values,groups):
    values=np.asarray(values,dtype=float);groups=np.asarray(groups)
    keys=sorted(set(groups));arr=np.stack([values[groups==key] for key in keys])
    rng=np.random.default_rng(97531)
    outer=rng.integers(0,len(keys),size=(10000,len(keys),1))
    inner=rng.integers(0,arr.shape[1],size=(10000,len(keys),arr.shape[1]))
    return [float(x) for x in np.quantile(arr[outer,inner].mean(axis=(1,2)),[.025,.975])]

def verify(path):
    meta=json.loads(Path(str(path)+'.meta.json').read_text())
    summary=json.loads(Path(str(path)+'.summary.json').read_text())
    protocol_path=HERE/'data/protocol.json'
    protocol=json.loads(protocol_path.read_text())
    assert meta['protocol_sha256']==hashlib.sha256(protocol_path.read_bytes()).hexdigest(),path
    assert meta['executable_sha256']==protocol['executable_sha256'],path
    assert meta['returncode']==0 and 'CHECK ' in meta['stderr'],path
    assert hashlib.sha256(path.read_bytes()).hexdigest()==meta['csv_sha256'],path
    assert hashlib.sha256(Path(str(path)+'.summary.json').read_bytes()).hexdigest()==meta['summary_sha256'],path
    assert abs(summary['checksum']-summary['serial_checksum'])<=1e-8*max(1.,abs(summary['serial_checksum']))
    df=pd.read_csv(path)
    numeric=df.select_dtypes('number').to_numpy()
    assert np.isfinite(numeric).all() and (df.wall_s>0).all() and (df.cpu_s>=0).all(),path
    return meta,summary,df

def main():
    RESULT.mkdir(exist_ok=True);FIG.mkdir(parents=True,exist_ok=True)
    protocol=json.loads((HERE/'data/protocol.json').read_text())
    prior=json.loads((HERE/'data/prior_cost.json').read_text())
    assert not {c['id'] for c in study.old_configs() if c['split']=='train'}&{c['id'] for c in study.configs()}
    ref=[];audited=0;first_test=float('inf');all_instances=0
    expected_ref={f"{c['id']}__a{a}__b{b}.csv" for c in study.configs() for a in range(12) for b in range(5)}
    ref_paths=list((HERE/'data/reference').glob('*.csv'))
    assert {p.name for p in ref_paths}==expected_ref
    for path in sorted(ref_paths):
        cid,arm,block=path.stem.split('__');meta,s,d=verify(path)
        assert len(d)==25 and (d.phase=='payload').all()
        ref.append(dict(scenario=cid,arm=int(arm[1:]),block=int(block[1:]),
                        median_s=float(d.loop_s.median())))
        audited+=1;all_instances+=len(d);first_test=min(first_test,meta['started_unix'])
    ref=pd.DataFrame(ref)
    matrix=ref.pivot(index=['scenario','block'],columns='arm',values='median_s')
    empirical=matrix.min(axis=1)
    cross={}
    for (cid,block),row in matrix.iterrows():
        other=matrix.loc[cid].drop(index=block).median(axis=0)
        selected=int(other.idxmin());cross[(cid,block)]=float(row[selected])
    configs={c['id']:c for c in study.configs()}
    expected_online={f'{cid}__{pol}__b{b}.csv' for cid in configs for pol in ORDER for b in range(5)}
    online_paths=list((HERE/'data/online').glob('*.csv'))
    assert {p.name for p in online_paths}==expected_online
    runs=[];prefixes=[]
    for path in sorted(online_paths):
        cid,policy,block=path.stem.split('__');block=int(block[1:]);c=configs[cid]
        meta,s,d=verify(path);payload=d[d.phase=='payload']
        assert list(payload['index'])==list(range(500)) and payload.arm.nunique()==1
        expected={'bestfixed':0,'prior':3,'budget2':6,'budget4':12,'budget8':24,'random4':12,'exhaustive':36}[policy]
        assert s['calibration_evaluations']==expected and len(d)==500+expected
        tuning=d[d.phase!='payload']
        assert tuning.arm.nunique()==len(s['tested_arms']) and len(set(s['tested_arms']))==len(s['tested_arms'])
        if expected:
            assert (tuning.groupby('arm').size()==3).all() and 0 in s['tested_arms']
        if policy not in ['prior','bestfixed']:
            med=tuning.groupby('arm').loop_s.median()
            assert s['selected_arm'] in med.index
            assert med[s['selected_arm']]<=med.min()+1e-12
        if policy=='prior':
            values=np.loadtxt(HERE/'data/model.txt');offset=5+int(values[4])
            mean=values[offset:offset+6];scale=values[offset+6:offset+12];offset+=12
            probe=tuning[['loop_s','lib','cv']].median()
            x=np.array([1,np.log2(c['n']),np.log2(c['p']),np.log2(probe.loop_s),probe.lib,probe.cv])
            x=(x-mean)/scale;scores=[]
            for arm in range(12):
                inv=values[offset:offset+36].reshape(6,6);b=values[offset+36:offset+42]
                scores.append(float(x@inv@b));offset+=42
            assert scores[s['selected_arm']]>=max(scores)-1e-10
        median_payload=float(payload.loop_s.median())
        common=dict(scenario=cid,input=c['kind']+'_s'+str(c['seed']),kind=c['kind'],
                    p=c['p'],block=block,policy=policy,selected_arm=s['selected_arm'],
                    selection_wall_s=s['selection_wall_s'],selection_cpu_s=s['selection_cpu_s'],
                    evaluations=expected,payload_median_s=median_payload,
                    payload_mean_s=float(payload.wall_s.mean()),
                    residual=median_payload/empirical[(cid,block)]-1,
                    cross_residual=median_payload/cross[(cid,block)]-1,
                    retained_speed=empirical[(cid,block)]/median_payload)
        runs.append(common)
        for pref in s['prefixes']:
            prefixes.append(dict(**common,horizon=pref['horizon'],
                                 total_wall_s=s['selection_wall_s']+pref['payload_wall_s'],
                                 total_cpu_s=s['selection_cpu_s']+pref['payload_cpu_s']))
        audited+=1;all_instances+=len(d);first_test=min(first_test,meta['started_unix'])
    for path in sorted((HERE/'data/calibration').glob('*.csv')):
        meta,s,d=verify(path);assert len(d)==23
        assert meta['config']['split']=='train';audited+=1;all_instances+=len(d)
    assert len(list((HERE/'data/calibration').glob('*.csv')))==432
    assert protocol['frozen_unix']<first_test and prior['fitted_unix']<first_test
    runs=pd.DataFrame(runs);prefixes=pd.DataFrame(prefixes)
    runs.to_csv(RESULT/'run_metrics.csv',index=False)
    prefixes.to_csv(RESULT/'prefix_metrics.csv',index=False)
    ref.to_csv(RESULT/'reference_metrics.csv',index=False)
    selection=[];quality=[];deploy=[]
    e=runs[runs.policy=='exhaustive'].set_index(['scenario','block'])
    for policy in ORDER:
        m=runs[runs.policy==policy].set_index(['scenario','block']).sort_index();base=e.loc[m.index]
        wall=base.selection_wall_s/m.selection_wall_s
        cpu=base.selection_cpu_s/m.selection_cpu_s
        group=m.input.to_numpy()
        ws=geom(wall);cs=geom(cpu)
        selection.append(dict(policy=policy,evaluations=int(m.evaluations.iloc[0]),
                              median_wall_ms=float(m.selection_wall_s.median()*1000),
                              median_cpu_ms=float(m.selection_cpu_s.median()*1000),
                              wall_saved_pct=100*(1-1/ws),cpu_saved_pct=100*(1-1/cs),
                              wall_speedup=ws,wall_speedup_ci=ci_ratio(wall,group),
                              cpu_speedup=cs,cpu_speedup_ci=ci_ratio(cpu,group)))
        q=m.residual;ret=m.retained_speed
        relative_full=m.payload_median_s/base.payload_median_s
        quality.append(dict(policy=policy,geomean_residual=geom(q+1)-1,
                            geomean_residual_ci=[x-1 for x in ci_ratio(q+1,group)],
                            median_residual=float(q.median()),p90_residual=float(q.quantile(.9)),
                            retained_geomean=geom(ret),within5=float((q<=.05).mean()),
                            within10=float((q<=.10).mean()),
                            within5_ci=ci_fraction(q<=.05,group),within10_ci=ci_fraction(q<=.10,group),
                            cross_geomean_residual=geom(m.cross_residual+1)-1,
                            cross_within5=float((m.cross_residual<=.05).mean()),
                            cross_within10=float((m.cross_residual<=.10).mean()),
                            extra_loss_to_full=geom(relative_full)-1,
                            extra_loss_to_full_ci=[v-1 for v in ci_ratio(relative_full,group)]))
    for h in protocol['prefixes']:
        d=prefixes[prefixes.horizon==h]
        pivot_w=d.pivot(index=['scenario','block','input'],columns='policy',values='total_wall_s')
        pivot_c=d.pivot(index=['scenario','block','input'],columns='policy',values='total_cpu_s')
        for policy in ORDER:
            ws=pivot_w.exhaustive/pivot_w[policy];cs=pivot_c.exhaustive/pivot_c[policy]
            group=pivot_w.index.get_level_values('input').to_numpy()
            meta=d[d.policy==policy].set_index(['scenario','block']).loc[pivot_w.index.droplevel('input')]
            good=(ws.to_numpy()>1)&(cs.to_numpy()>1)
            deploy.append(dict(policy=policy,horizon=h,wall_speedup=geom(ws),wall_ci=ci_ratio(ws,group),
                               cpu_speedup=geom(cs),cpu_ci=ci_ratio(cs,group),
                               worthwhile5=float(np.mean(good&(meta.residual.to_numpy()<=.05))),
                               worthwhile10=float(np.mean(good&(meta.residual.to_numpy()<=.10))),
                               worthwhile5_ci=ci_fraction(good&(meta.residual.to_numpy()<=.05),group),
                               worthwhile10_ci=ci_fraction(good&(meta.residual.to_numpy()<=.10),group)))
    pd.DataFrame(selection).to_csv(RESULT/'selection_cost.csv',index=False)
    pd.DataFrame(quality).to_csv(RESULT/'quality.csv',index=False)
    pd.DataFrame(deploy).to_csv(RESULT/'deployment.csv',index=False)
    # Arithmetic mean savings determine how many sequential deployments amortize
    # an operationally paid prior. This is an estimate conditional on this mix.
    offline_w=prior['calibration_wall_s']+prior['fit_wall_s']
    offline_c=prior['calibration_cpu_s']+prior['fit_cpu_s']
    amort=[];crossover=[]
    for policy in ['bestfixed','prior','budget2','budget4','budget8']:
        m=runs[runs.policy==policy].set_index(['scenario','block']).sort_index();base=e.loc[m.index]
        saved=base.selection_wall_s-m.selection_wall_s
        gap=m.payload_mean_s-base.payload_mean_s
        eligible=(gap>0)&(saved>0)
        crosses=saved[eligible]/gap[eligible]
        crossover.append(dict(policy=policy,finite_cases=len(crosses),total_cases=len(m),
                              saved_setup_and_no_payload_penalty=int(((saved>0)&(gap<=0)).sum()),
                              no_setup_saving=int((saved<=0).sum()),
                              median_finite_horizon=None if not len(crosses) else float(crosses.median())))
        for h in protocol['prefixes']:
            d=prefixes[prefixes.horizon==h].pivot(index=['scenario','block'],columns='policy',values=['total_wall_s','total_cpu_s'])
            dw=(d['total_wall_s']['exhaustive']-d['total_wall_s'][policy]).mean()
            dc=(d['total_cpu_s']['exhaustive']-d['total_cpu_s'][policy]).mean()
            groups=np.array([cid.rsplit('_p',1)[0] for cid in d.index.get_level_values('scenario')])
            amort.append(dict(policy=policy,horizon=h,mean_wall_saving_s=float(dw),mean_cpu_saving_s=float(dc),
                              wall_mean_saving_ci=ci_fraction(d['total_wall_s']['exhaustive']-d['total_wall_s'][policy],groups),
                              cpu_mean_saving_ci=ci_fraction(d['total_cpu_s']['exhaustive']-d['total_cpu_s'][policy],groups),
                              wall_reuses=None if dw<=0 else int(np.ceil(offline_w/dw)),
                              cpu_reuses=None if dc<=0 else int(np.ceil(offline_c/dc))))
    families=[]
    for kind in ['mandelbrot','triad','triangle']:
        for policy in ORDER:
            m=runs[(runs.kind==kind)&(runs.policy==policy)].set_index(['scenario','block']).sort_index()
            base=e.loc[m.index]
            item=dict(kind=kind,policy=policy,
                      selection_wall_saved_pct=100*(1-1/geom(base.selection_wall_s/m.selection_wall_s)),
                      selection_cpu_saved_pct=100*(1-1/geom(base.selection_cpu_s/m.selection_cpu_s)),
                      payload_residual=geom(m.residual+1)-1)
            for h in [50,500]:
                x=prefixes[(prefixes.kind==kind)&(prefixes.horizon==h)].pivot(index=['scenario','block'],columns='policy',values='total_wall_s')
                item[f'wall_speedup_{h}']=geom(x.exhaustive/x[policy])
            families.append(item)
    pd.DataFrame(families).to_csv(RESULT/'family_metrics.csv',index=False)
    report=dict(processes=audited,logged_instances=all_instances,online_runs=len(runs),
                useful_online_instances=len(runs)*500,reference_runs=len(ref),
                test_scenarios=len(configs),independent_inputs=12,selection=selection,quality=quality,
                deployment=deploy,prior_cost=dict(wall_s=offline_w,cpu_s=offline_c),
                amortization=amort,crossover=crossover,families=families,
                training_ids_disjoint=True,protocol_predates_tests=True)
    (RESULT/'report.json').write_text(json.dumps(report,indent=2))
    make_figures(report,runs,prefixes)
    print(pd.DataFrame(selection)[['policy','evaluations','wall_saved_pct','cpu_saved_pct']].to_string(index=False))
    print(pd.DataFrame(quality)[['policy','geomean_residual','within5','within10']].to_string(index=False))
    print(pd.DataFrame(deploy)[['policy','horizon','wall_speedup','cpu_speedup','worthwhile5']].to_string(index=False))
    print('PRIOR COST',report['prior_cost']);print('AUDITED',audited,'processes',all_instances,'rows')

def make_figures(r,runs,prefixes):
    plt.rcParams.update({'font.size':9,'pdf.fonttype':42,'axes.spines.top':False,'axes.spines.right':False})
    colors=dict(zip(ORDER,['#666666','#008837','#2166ac','#762a83','#e08214','#b2182b','#000000']))
    fig,ax=plt.subplots(figsize=(6.5,3.3))
    for s,q in zip(r['selection'],r['quality']):
        ax.scatter(s['wall_saved_pct'],100*q['geomean_residual'],label=LABELS[s['policy']],color=colors[s['policy']],s=35)
        ax.annotate(LABELS[s['policy']],(s['wall_saved_pct'],100*q['geomean_residual']),xytext=(4,4),textcoords='offset points',fontsize=8)
    ax.axhline(5,color='gray',ls='--',lw=.8);ax.axhline(10,color='gray',ls=':',lw=.8)
    ax.set_xlabel('Tuning wall-time saving versus full search (%)')
    ax.set_ylabel('Payload slowdown to empirical best (%)')
    fig.tight_layout();fig.savefig(FIG/'tradeoff.pdf');plt.close(fig)
    fig,axs=plt.subplots(1,2,figsize=(7,2.9))
    for policy in ORDER[:-1]:
        d=[v for v in r['deployment'] if v['policy']==policy]
        for ax,key in zip(axs,['wall_speedup','cpu_speedup']):
            ax.plot([v['horizon'] for v in d],[v[key] for v in d],marker='o',ms=3,label=LABELS[policy],color=colors[policy])
    for ax,title in zip(axs,['Elapsed time','Process CPU time']):
        ax.axhline(1,color='black',ls='--',lw=.8);ax.set_xscale('log');ax.set_title(title)
        ax.set_xticks([10,50,100,500],[10,50,100,500]);ax.set_xlabel('Useful loop executions')
    axs[0].set_ylabel('Full-search cost / policy cost')
    handles,labels=axs[0].get_legend_handles_labels();fig.legend(handles,labels,ncol=3,loc='upper center',bbox_to_anchor=(.5,1.12),fontsize=8)
    fig.tight_layout();fig.savefig(FIG/'horizons.pdf',bbox_inches='tight');plt.close(fig)
    fig,ax=plt.subplots(figsize=(6.4,3))
    rows=r['quality'];x=np.arange(len(rows))
    ax.bar(x-.18,[v['within5'] for v in rows],.36,label='Within 5%')
    ax.bar(x+.18,[v['within10'] for v in rows],.36,label='Within 10%')
    ax.set_xticks(x,[LABELS[v['policy']] for v in rows],rotation=20,ha='right')
    ax.yaxis.set_major_formatter(PercentFormatter(1));ax.set_ylabel('Observed runs meeting payload tolerance')
    ax.legend();fig.tight_layout();fig.savefig(FIG/'acceptance.pdf');plt.close(fig)

if __name__=='__main__':main()
