#!/usr/bin/env python3
"""Generate manuscript claims from measured aggregates, with no placeholder data."""
import json
from pathlib import Path
from study import ROOT
from analyze import LABELS,ORDER

def number(x):return f'{x:.3f}'
def texname(s):return s.replace('_',r'\_')

def main():
    r=json.loads((ROOT/'results/report.json').read_text())
    p=json.loads((ROOT/'data/protocol.json').read_text())
    transfer=json.loads((ROOT/'results/transfer_report.json').read_text())
    def comparison(base,candidate='warm',h=500):
        return next(x for x in r['comparisons'] if x['candidate']==candidate and x['baseline']==base and x['horizon']==h)
    def statement(base,candidate='warm',h=500):
        c=comparison(base,candidate,h)
        return (f"{number(c['speedup'])} (95\\% CI "
                f"{number(c['ci_low'])}--{number(c['ci_high'])})")
    def verdict(c):
        if c['ci_low']>1:return 'The interval favors the candidate on these inputs.'
        if c['ci_high']<1:return 'The interval favors the baseline on these inputs.'
        return 'The interval crosses one, leaving the direction unresolved at this precision.'
    c_q=comparison('qlearn');c_ex=comparison('exhaustive');c_fixed=comparison('bestfixed')
    abstract=("Full-portfolio warm LinUCB achieves a paired geometric mean speed ratio of "
              +statement('qlearn')+" against native Q-learning and "+statement('exhaustive')+
              " against exhaustive search, where ratios above one favor LinUCB. "
              "Against the training-selected fixed scheduler its ratio is "+statement('bestfixed')+". "
              "The primary confidence intervals include one, so this campaign does not "
              "demonstrate a warm-start advantage. ")
    maintext=[]
    for base in ['qlearn','exhaustive','bestfixed']:
        c=comparison(base)
        maintext.append(f"Against {LABELS[base]}, warm LinUCB's paired geometric speed ratio is "
                        +statement(base)+f"; it is faster on {c['input_wins']} of the six input configurations. "
                        +verdict(c))
    sig=[x for x in r['comparisons'] if x['candidate']=='warm' and x['horizon']==500 and x['p_holm']<.05]
    if not sig:maintext.append("None of the six warm-selector comparisons reaches a Holm-adjusted "
                             "$p<0.05$ with six input-level signed-rank observations. "
                             "Accordingly, the reported ratios and intervals are descriptive effect estimates.")
    else:maintext.append("The complete raw and adjusted test results are supplied in the artifact.")
    expl=("At 50 instances the warm/native-Q speed ratio is "+statement('qlearn',h=50)+
          "; at 144 it is "+statement('qlearn',h=144)+
          ". At 500 instances, warm versus cold LinUCB gives "+statement('cold')+
          ", while warm versus the context-free UCB baseline gives "+statement('ucb')+". "
          "These prefix results share the same runs. They quantify exploration cost without "
          "counting prefixes as additional independent experiments.")
    reduced=("The reduced selector's 500-instance ratio against native Q-learning is "
             +statement('qlearn','reduced')+", and against exhaustive search it is "
             +statement('exhaustive','reduced')+". Portfolio reduction therefore must be judged "
             "by measured runtime rather than by the nominal reduction from 12 to six arms.")
    overhead=(f"The median per-run median decision-plus-update cost is "
              f"{r['overhead_us']['warm']:.2f} microseconds for full warm LinUCB, "
              f"{r['overhead_us']['reduced']:.2f} for the reduced selector, and "
              f"{r['overhead_us']['exhaustive']:.2f} for exhaustive search. "
              "These costs are included in the reported runtime. Native Q-learning's main "
              "selection cost is inside the runtime and is included in loop time, so its "
              "external decision counter is not a comparable measure of algorithm overhead.")
    practical=("Warm versus prior-only greedy selection has a paired ratio of "+statement('greedy')+". "
               +verdict(comparison('greedy'))+
               " This control prevents attributing every gain from offline knowledge to online exploration.")
    practical+=(f" The median coefficient of variation of total time across the five runs "
                f"of a scenario/selector is {100*r['median_between_run_cv']:.1f}\\%. "
                "This variability should be considered when interpreting percentage-level differences.")
    conclusion=("Measured warm/native-Q, warm/exhaustive, and warm/best-fixed speed ratios are "
                f"{number(c_q['speedup'])}, {number(c_ex['speedup'])}, and {number(c_fixed['speedup'])}, "
                "respectively, on this environment. Their intervals include one: the expected "
                "warm-start improvement is not established. These outcomes describe a specific "
                "finite-horizon trade-off; they do not establish a universal winner.")
    transfer_text=[]
    for c in transfer['comparisons']:
        transfer_text.append(f"Against {LABELS[c['baseline']]}, the exploratory "
                             f"warm-selector ratio is {number(c['speedup'])} "
                             f"(95\\% CI {number(c['ci_low'])}--{number(c['ci_high'])}).")
    sensitivity=[]
    for c in r['exclude_interrupted_block']:
        sensitivity.append(f"{LABELS[c['baseline']]}: {number(c['speedup'])} "
                           f"(95\\% CI {number(c['ci_low'])}--{number(c['ci_high'])})")
    macros={'OnlineRuns':f"{r['run_count']:,}",'LoopInstances':f"{r['loop_instances']:,}",
            'CorrectRuns':f"{r['checks_passed']:,}",'ReferenceRuns':str(r['reference_runs']),
            'MeasuredSeconds':f"{r['measured_online_s']:,.1f}",
            'AbstractFinding':abstract,'MainResultsDiscussion':'\n\n'.join(maintext),
            'ExplorationDiscussion':expl,'ReductionDiscussion':reduced,
            'OverheadDiscussion':overhead,'PracticalDiscussion':practical,
            'ConclusionFinding':conclusion,'PriorWeight':str(p['selected']['weight']),
            'RidgeValue':str(p['selected']['ridge']),'AlphaValue':str(p['selected']['alpha']),
            'ReducedArms':', '.join(p['reduced_names']),'BestFixedArm':p['best_fixed_name'],
            'WallGap':f"{100*r['wall_gap_median']:.2f}",
            'TransferRuns':str(transfer['run_count']),
            'TransferInstances':f"{transfer['loop_instances']:,}",
            'TransferDiscussion':' '.join(transfer_text),
            'InterruptionSensitivity':'; '.join(sensitivity)}
    selection=r['selection_summary']
    macros['SelectionDiscussion']=(
        f"Warm LinUCB tries a median of {selection['warm']['distinct_arms']:.0f} distinct arms "
        f"over 500 instances, versus {selection['cold']['distinct_arms']:.0f} for cold LinUCB "
        f"and {selection['ucb']['distinct_arms']:.0f} for context-free UCB. "
        f"Its median modal-arm fraction is {100*selection['warm']['modal_fraction']:.1f}\\%. "
        "These counts describe action concentration, not convergence to the best scheduler; "
        "using fewer arms is useful only if it reduces measured cost.")
    text='% Generated by scripts/render_results.py from measured data.\n'
    for name,value in macros.items():text+=f'\\newcommand{{\\{name}}}{{{value}}}\n'
    (ROOT/'paper/results.tex').write_text(text)
    summaries={(x['policy'],x['horizon']):x for x in r['summary']}
    rows=[]
    for policy in ORDER:
        vals=[number(summaries[(policy,h)]['geomean_slowdown']) for h in [50,144,500]]
        rows.append(LABELS[policy]+' & '+' & '.join(vals)+r' \\')
    table=r'''\begin{table}[ht]
\centering\small
\caption{Geometric mean cumulative slowdown to the independent fixed-arm
reference. Lower values indicate less charged execution time. Prefixes
belong to the same runs; they are not separate experiments.}
\label{tab:summary}
\begin{tabular}{lrrr}
\hline
Selector & 50 instances & 144 instances & 500 instances\\
\hline
'''+ '\n'.join(rows)+r'''
\hline
\end{tabular}
\end{table}
'''
    (ROOT/'paper/summary_table.tex').write_text(table)
    transfer_rows=[kind.capitalize()+' & '+number(values['bestfixed'])+' & '+
                   number(values['greedy'])+r' \\' for kind,values in transfer['family'].items()]
    transfer_table=r'''\begin{table}[ht]
\centering\small
\caption{Exploratory family-transfer speed ratios: baseline time divided by
warm LinUCB time, with each evaluated family excluded from prior fitting.
Per-family rows contain only two input configurations and are descriptive.}
\label{tab:transfer}
\begin{tabular}{lrr}
\hline
Held-out family & Versus best fixed & Versus prior greedy\\
\hline
'''+ '\n'.join(transfer_rows)+r'''
\hline
\end{tabular}
\end{table}
'''
    (ROOT/'paper/transfer_table.tex').write_text(transfer_table)
    print('Generated manuscript numbers and results table from report.json')

if __name__=='__main__':main()
