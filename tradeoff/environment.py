#!/usr/bin/env python3
"""Record the observed build/analysis environment without changing measurements."""
import json
import os
from pathlib import Path
import platform
import subprocess
import time
import numpy,pandas,scipy,matplotlib

HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
commands={'cpu':['lscpu'],'topology':['lscpu','-e=CPU,CORE,SOCKET,NODE'],
          'kernel':['uname','-a'],'compiler':['clang++-16','--version'],
          'runtime_commit':['git','-C',os.environ['LB4OMP_SOURCE'],'rev-parse','HEAD']}
info={name:subprocess.check_output(cmd,text=True) for name,cmd in commands.items()}
info.update(captured_unix=time.time(),capture_note='Captured after measurement; run settings are frozen separately in protocol.json',
            python=platform.python_version(),numpy=numpy.__version__,pandas=pandas.__version__,
            scipy=scipy.__version__,matplotlib=matplotlib.__version__)
(HERE/'data/environment.json').write_text(json.dumps(info,indent=2)+'\n')
print('Recorded hardware, runtime, compiler, and package versions.')
