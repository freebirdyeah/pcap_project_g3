#!/usr/bin/env python3
"""Package the fresh study without modifying the older paper/artifact."""
import hashlib
import json
from pathlib import Path
import zipfile

HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
OUTPUT=ROOT/'deliverables/current'
OUTPUT.mkdir(parents=True,exist_ok=True)
paths=[p for p in HERE.rglob('*') if p.is_file()
       and '__pycache__' not in p.parts and p.suffix not in ['.aux','.log','.out']]
paths.extend(ROOT/p for p in ['src/experiment.cpp','scripts/build.sh','scripts/study.py',
                              'scripts/fit.py','scripts/analyze.py','requirements.txt',
                              'patches/lb4omp-clang16.patch'])
manifest={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}
manifest_path=OUTPUT/'PCAP_TRADEOFF_SHA256_G3.json'
manifest_path.write_text(json.dumps(manifest,indent=2)+'\n');paths.append(manifest_path)
with zipfile.ZipFile(OUTPUT/'PCAP_TRADEOFF_ARTIFACT_G3.zip','w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in sorted(paths):
        z.write(p,manifest_path.name if p==manifest_path else p.relative_to(ROOT))
print('Packaged',len(paths),'files, including fresh raw data and hashes, in',OUTPUT)
