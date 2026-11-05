#!/usr/bin/env python3
"""Final study-wide counts, frozen files, CPU accounting, and prior checks."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    report=json.loads((HERE/'results/report.json').read_text())
    insitu=json.loads((HERE/'results/insitu_report.json').read_text())
    protocol=json.loads((HERE/'data/protocol.json').read_text())
    prior=json.loads((HERE/'data/prior_cost.json').read_text())
    assert digest(HERE/'src/tradeoff.cpp')==protocol['source_sha256']
    assert digest(ROOT/'src/experiment.cpp')==protocol['shared_source_sha256']
    assert digest(ROOT/'build/tradeoff')==protocol['executable_sha256']
    assert digest(HERE/'data/model.txt')==prior['model_sha256']
    counts={};rows=0;hashes=0;cal_wall=0.;cal_cpu=0.
    for stage,expected in [('calibration',432),('reference',1440),('online',840),('insitu',432)]:
        paths=list((HERE/'data'/stage).glob('*.csv'));assert len(paths)==expected
        counts[stage]=len(paths)
        for path in paths:
            meta=json.loads(Path(str(path)+'.meta.json').read_text())
            s=json.loads(Path(str(path)+'.summary.json').read_text())
            assert meta['csv_sha256']==digest(path)
            assert meta['summary_sha256']==digest(Path(str(path)+'.summary.json'))
            assert meta['returncode']==0 and 'CHECK ' in meta['stderr']
            assert meta['process_wall_s']>0 and meta['process_cpu_s']>0
            assert s['selection_wall_s']>=0 and s['selection_cpu_s']>=0
            assert s['payload_wall_s']>0 and s['payload_cpu_s']>0
            rows+=sum(1 for _ in path.open())-1;hashes+=2
            if stage=='calibration':cal_wall+=meta['process_wall_s'];cal_cpu+=meta['process_cpu_s']
    assert abs(cal_wall-prior['calibration_wall_s'])<1e-8
    assert abs(cal_cpu-prior['calibration_cpu_s'])<1e-8
    assert sum(counts.values())==report['processes']+insitu['processes']==3144
    assert rows==report['logged_instances']+insitu['logged_instances']==595896
    audit=dict(processes=sum(counts.values()),logged_instances=rows,stage_counts=counts,
               raw_and_summary_hashes_verified=hashes,all_output_checks_passed=True,
               frozen_source_binary_model_intact=True,prior_cost_recomputed=True,
               primary_useful_executions=report['useful_online_instances'],
               insitu_useful_executions=insitu['logged_instances'],
               source_sha256=protocol['source_sha256'],model_sha256=prior['model_sha256'])
    (HERE/'results/final_audit.json').write_text(json.dumps(audit,indent=2)+'\n')
    print(json.dumps(audit,indent=2))

if __name__=='__main__':main()
