#!/usr/bin/env python3
"""All numerical manuscript text comes from the measured report."""
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
LABELS={'bestfixed':'Best fixed','prior':'Prior only','budget2':'Guided 2',
        'budget4':'Guided 4','budget8':'Guided 8','random4':'Random 4','exhaustive':'Full 12'}
ORDER=list(LABELS)
def pct(x):return f'{100*x:.1f}\\%'
def num(x):return f'{x:.3f}'
def table(path,caption,cols,header,rows,label):
    text='\\begin{table*}[t]\n\\centering\\small\n\\caption{'+caption+'}\n'
    text+='\\label{'+label+'}\n\\begin{tabular}{'+cols+'}\n\\hline\n'
    text+=header+r'\\'+'\n\\hline\n'+'\n'.join(' & '.join(row)+r' \\' for row in rows)
    text+='\n\\hline\n\\end{tabular}\n\\end{table*}\n'
    path.write_text(text)

def main():
    r=json.loads((HERE/'results/report.json').read_text())
    prior=json.loads((HERE/'data/prior_cost.json').read_text())
    insitu=json.loads((HERE/'results/insitu_report.json').read_text())
    s={d['policy']:d for d in r['selection']};q={d['policy']:d for d in r['quality']}
    d={(v['policy'],v['horizon']):v for v in r['deployment']}
    a={(v['policy'],v['horizon']):v for v in r['amortization']}
    def ratio(ci):return f'{num(ci[0])}--{num(ci[1])}'
    def reuse(value):return 'no finite estimate' if value is None else f'{value:,}'
    b=s['budget4'];quality=q['budget4'];h50=d[('budget4',50)];h500=d[('budget4',500)]
    abstract=(f"Four-candidate screening saves {b['wall_saved_pct']:.1f}\\% of tuning wall time "
              f"and {b['cpu_saved_pct']:.1f}\\% of tuning CPU time, with a geometric mean "
              f"payload penalty of {pct(quality['geomean_residual'])} to the same-block empirical best. "
              f"Its additional payload loss relative to full search's chosen schedule is "
              f"{pct(quality['extra_loss_to_full'])} "
              f"(95\\% CI {pct(quality['extra_loss_to_full_ci'][0])}--{pct(quality['extra_loss_to_full_ci'][1])}). "
              f"For 50 useful executions and an available prior, its total-cost ratio is "
              f"{num(h50['wall_speedup'])} relative to full search (95\\% CI {ratio(h50['wall_ci'])}), "
              "where ratios above one favor screening. ")
    selections=(f"Guided 2, Guided 4, and Guided 8 save "
                f"{s['budget2']['wall_saved_pct']:.1f}\\%, {s['budget4']['wall_saved_pct']:.1f}\\%, "
                f"and {s['budget8']['wall_saved_pct']:.1f}\\% of tuning wall time, respectively. "
                f"Their corresponding CPU savings are {s['budget2']['cpu_saved_pct']:.1f}\\%, "
                f"{s['budget4']['cpu_saved_pct']:.1f}\\%, and {s['budget8']['cpu_saved_pct']:.1f}\\%. "
                f"Prior-only selection saves {s['prior']['wall_saved_pct']:.1f}\\% wall time "
                f"and {s['prior']['cpu_saved_pct']:.1f}\\% CPU time. "
                "These are paired geometric cost ratios over complete tuning phases, not ratios of median milliseconds.")
    qualities=(f"Guided 4's geometric mean payload loss is {pct(quality['geomean_residual'])} "
               f"(95\\% CI {pct(quality['geomean_residual_ci'][0])}--{pct(quality['geomean_residual_ci'][1])}). "
               f"It retains {pct(quality['retained_geomean'])} of reference speed. "
               f"Relative to the schedule actually selected by Full 12, its extra payload loss "
               f"is {pct(quality['extra_loss_to_full'])} "
               f"(95\\% CI {pct(quality['extra_loss_to_full_ci'][0])}--{pct(quality['extra_loss_to_full_ci'][1])}). "
               f"Its payload is within 5\\% in {pct(quality['within5'])} of runs and within "
               f"10\\% in {pct(quality['within10'])}. "
               f"Full search itself has a geometric residual of {pct(q['exhaustive']['geomean_residual'])}, "
               "illustrating the gap between a finite noisy sweep and an independent best-arm reference.")
    deployment=(f"Guided 4's wall-cost ratios at horizons 10, 50, 100, and 500 are "
                +', '.join(num(d[('budget4',h)]['wall_speedup']) for h in [10,50,100,500])+'. '
                f"At 50 executions the CPU-cost ratio is {num(h50['cpu_speedup'])} "
                f"(95\\% CI {ratio(h50['cpu_ci'])}); at 500 it is {num(h500['cpu_speedup'])}. "
                "Ratios above one indicate lower total cost for screening.")
    worth=(f"At 50 useful executions, {pct(h50['worthwhile5'])} of Guided 4 runs satisfy "
           f"(95\\% cluster-bootstrap interval {pct(h50['worthwhile5_ci'][0])}--{pct(h50['worthwhile5_ci'][1])}) "
           f"all three conditions of lower wall cost, lower CPU cost, and at most 5\\% payload loss; "
           f"with a 10\\% tolerance this rises to {pct(h50['worthwhile10'])}. "
           f"At 500 executions the corresponding rates are {pct(h500['worthwhile5'])} "
           f"and {pct(h500['worthwhile10'])}.")
    cross=next(v for v in r['crossover'] if v['policy']=='budget4')
    horizon='undefined' if cross['median_finite_horizon'] is None else f"{cross['median_finite_horizon']:.0f}"
    crossover=(f"For Guided 4, {cross['finite_cases']} of {cross['total_cases']} paired runs "
               f"have both a tuning saving and a positive payload mean gap to full search. Their median estimated finite "
               f"crossover is {horizon} useful executions. "
               "This summarizes only runs with a positive gap; it is not a universal operating cutoff.")
    reuse50=a[('budget4',50)];reuse500=a[('budget4',500)]
    amort=(f"For Guided 4 at horizon 50, the estimated break-even is "
           f"{reuse(reuse50['wall_reuses'])} deployments for wall time and "
           f"{reuse(reuse50['cpu_reuses'])} for CPU time. "
           f"At horizon 500 the estimates are {reuse(reuse500['wall_reuses'])} "
           f"and {reuse(reuse500['cpu_reuses'])}, respectively. "
           "When both resources matter, the larger finite count is the relevant lower bound.")
    sensitivity=(f"Under the cross-fitted reference, Guided 4's geometric payload loss becomes "
                 f"{pct(quality['cross_geomean_residual'])}; its within-5\\% and within-10\\% "
                 f"rates become {pct(quality['cross_within5'])} and {pct(quality['cross_within10'])}. "
                 "The difference from the primary reference quantifies sensitivity to choosing a minimum "
                 "among noisy same-block timings.")
    controls=(f"Random 4 has a geometric payload loss of {pct(q['random4']['geomean_residual'])} "
              f"and a horizon-50 wall-cost ratio of {num(d[('random4',50)]['wall_speedup'])}. "
              f"The trained fixed arm has a loss of {pct(q['bestfixed']['geomean_residual'])} "
              f"and ratio {num(d[('bestfixed',50)]['wall_speedup'])}, with no online calibration. "
              "Thus the value of prediction must be considered alongside the simpler ways to spend less on search.")
    decision=(f"For the four-candidate policy, the measured exchange is "
              f"{b['wall_saved_pct']:.1f}\\% less tuning wall time and {b['cpu_saved_pct']:.1f}\\% "
              f"less tuning CPU time for {pct(quality['geomean_residual'])} aggregate residual payload loss. "
              f"Its horizon-50 total wall ratio is {num(h50['wall_speedup'])}, whereas its horizon-500 "
              f"ratio is {num(h500['wall_speedup'])}. "
              "These measurements make the trade-off explicit; the tolerance hit rate and prior cost determine "
              "whether it is acceptable for a particular deployment.")
    conclusion=(f"On the measured four-core system, Guided 4 avoids two thirds of calibration "
                f"evaluations and saves {b['wall_saved_pct']:.1f}\\% tuning wall time "
                f"and {b['cpu_saved_pct']:.1f}\\% tuning CPU time. "
                f"Its geometric payload penalty is {pct(quality['geomean_residual'])}. "
                f"For an available prior, its total wall-cost ratio is {num(h50['wall_speedup'])} "
                f"at 50 useful executions and {num(h500['wall_speedup'])} at 500. "
                "Prior acquisition and tail losses remain part of the decision rather than being hidden costs.")
    insitu_rows=insitu['comparisons']
    insitu4={v['horizon']:v for v in insitu_rows if v['policy']=='budget4'}
    abstract+=(f"With calibration counted as useful work, the four-candidate wall ratios are "
               f"{num(insitu4[50]['wall_speedup'])} at 50 executions and "
               f"{num(insitu4[500]['wall_speedup'])} at 500, limiting the savings claim "
               "to the extra-calibration operating mode. ")
    insitu_text=[]
    for value in insitu_rows:
        if value['policy']=='budget4':
            insitu_text.append(f"For {value['horizon']} equal useful executions, Guided 4's "
                               f"wall-cost ratio is {num(value['wall_speedup'])} "
                               f"(95\\% CI {ratio(value['wall_ci'])}) and its CPU-cost ratio "
                               f"is {num(value['cpu_speedup'])} "
                               f"(95\\% CI {ratio(value['cpu_ci'])}).")
    insitu_decision=(f"the four-candidate wall-cost ratios are {num(insitu4[50]['wall_speedup'])} "
                     f"at 50 useful calls and {num(insitu4[500]['wall_speedup'])} at 500. "
                     'These do not establish a time/CPU saving from reduced search in that mode. '
                     'Avoided candidate tests cannot be counted as avoided necessary executions; '
                     'the primary extra-calibration savings apply only when calibration is additional work.')
    conclusion+=(f" The separate equal-useful-work ratios of {num(insitu4[50]['wall_speedup'])} "
                 f"and {num(insitu4[500]['wall_speedup'])} do not establish an in-situ benefit. ")
    macros=dict(OnlineRuns=f"{r['online_runs']:,}",TotalProcesses=f"{r['processes']:,}",
                TotalRows=f"{r['logged_instances']:,}",UsefulInstances=f"{r['useful_online_instances']:,}",
                BestFixedArm=prior['best_fixed_name'],PriorWall=f"{r['prior_cost']['wall_s']:.2f}",
                PriorCPU=f"{r['prior_cost']['cpu_s']:.2f}",AbstractResults=abstract,
                SelectionResults=selections,QualityResults=qualities,DeploymentResults=deployment,
                WorthResults=worth,CrossoverResults=crossover,AmortizationResults=amort,
                SensitivityResults=sensitivity,ControlResults=controls,DecisionResults=decision,
                ConclusionResults=conclusion,InsituRuns=str(insitu['processes']),
                InsituInstances=f"{insitu['logged_instances']:,}",
                InsituResults=' '.join(insitu_text),InsituDecision=insitu_decision)
    text='% Generated only from audited measured results.\n'
    for k,v in macros.items():text+='\\newcommand{\\'+k+'}{'+v+'}\n'
    (HERE/'paper/results.tex').write_text(text)
    rows=[[LABELS[p],str(s[p]['evaluations']),f"{s[p]['median_wall_ms']:.2f}",
           f"{s[p]['wall_saved_pct']:.1f}",f"{s[p]['cpu_saved_pct']:.1f}"] for p in ORDER]
    table(HERE/'paper/selection_table.tex','Measured tuning cost relative to Full 12. Savings are paired geometric effects; median wall milliseconds are descriptive.',
          'lrrrr','Policy & Evaluations & Median wall (ms) & Wall saved (\\%) & CPU saved (\\%)',rows,'tab:selection')
    rows=[[LABELS[p],f"{100*q[p]['geomean_residual']:.1f}",f"{100*q[p]['p90_residual']:.1f}",
           f"{100*q[p]['within5']:.1f}",f"{100*q[p]['within10']:.1f}"] for p in ORDER]
    table(HERE/'paper/quality_table.tex','Independent payload-quality measurements. Geometric mean and 90th-percentile residual slowdowns are relative to the same-block empirical best. Acceptance rates are observed run fractions.',
          'lrrrr','Policy & Mean loss (\\%) & P90 loss (\\%) & Within 5\\% & Within 10\\%',rows,'tab:quality')
    rows=[[LABELS[p],*[num(d[(p,h)]['wall_speedup']) for h in [10,50,100,500]]] for p in ORDER]
    table(HERE/'paper/deployment_table.tex','Total wall-cost ratios: Full 12 cost divided by policy cost, including tuning and H useful executions. Values above one favor the policy. Prior acquisition is excluded here and charged separately.',
          'lrrrr','Policy & H=10 & H=50 & H=100 & H=500',rows,'tab:deployment')
    rows=[[v['kind'].capitalize(),f"{v['selection_wall_saved_pct']:.1f}",f"{100*v['payload_residual']:.1f}",
           num(v['wall_speedup_50']),num(v['wall_speedup_500'])] for v in r['families'] if v['policy']=='budget4']
    table(HERE/'paper/family_table.tex','Four-candidate screening by workload family: calibration wall saving, payload loss to the empirical best, and complete deployment wall-cost ratios. Each family contains four input configurations at two thread counts.',
          'lrrrr','Family & Tuning saved (\\%) & Payload loss (\\%) & H=50 ratio & H=500 ratio',rows,'tab:family')
    rows=[[LABELS[v['policy']],str(v['horizon']),num(v['wall_speedup']),ratio(v['wall_ci']),
           num(v['cpu_speedup'])] for v in insitu_rows]
    table(HERE/'paper/insitu_table.tex','Secondary equal-useful-work results. Both tuning and committed calls count toward H; cost ratios are Full 12 divided by the policy. All intervals use input-cluster resampling.',
          'lrrrr','Policy & H & Wall ratio & Wall 95\\% CI & CPU ratio',rows,'tab:insitu')
    print('Rendered measured numbers and three tables.')

if __name__=='__main__':main()
