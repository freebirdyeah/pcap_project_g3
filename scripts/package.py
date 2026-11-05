#!/usr/bin/env python3
"""Create a portable artifact and a hash manifest; exclude build dependencies."""
from pathlib import Path
import hashlib
import json
import zipfile
ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/'deliverables/previous'
OUTPUT.mkdir(parents=True,exist_ok=True)
paths=[]
for dirname in ['src','scripts','tests','patches','paper','results']:
    paths.extend(p for p in (ROOT/dirname).rglob('*') if p.is_file()
                 and '__pycache__' not in p.parts and p.suffix not in ['.aux','.log','.out'])
for dirname in ['calibration','reference','online','audit','ablation','transfer']:
    if (ROOT/'data'/dirname).exists():paths.extend(p for p in (ROOT/'data'/dirname).rglob('*') if p.is_file())
paths.extend(p for p in (ROOT/'data').glob('*') if p.is_file())
paths.extend(ROOT/p for p in ['README.md','docs/ORGANIZATION.md',
                             'docs/original-study/README.md',
                             'docs/original-study/RESEARCH_LOG.md','requirements.txt'])
manifest={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(paths))}
manifest_path=OUTPUT/'ARTIFACT_SHA256.json'
manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
with zipfile.ZipFile(OUTPUT/'PCAP_RESEARCH_ARTIFACT_G3.zip','w',zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
    for p in sorted(set(paths)):archive.write(p,p.relative_to(ROOT))
    archive.write(manifest_path,'ARTIFACT_SHA256.json')
print('Packaged',len(set(paths))+1,'files; SHA-256 manifest included in',OUTPUT)
