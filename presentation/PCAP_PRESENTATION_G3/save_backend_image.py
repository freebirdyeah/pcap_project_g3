"""Save an image backend's base64 bytes from a raw PTY without echoing them."""
import base64
import os
from pathlib import Path
import sys
import tty

target = Path(sys.argv[1])
remaining = int(sys.argv[2])
tty.setraw(sys.stdin.fileno())
print('READY', flush=True)
chunks = []
while remaining:
    chunk = os.read(sys.stdin.fileno(), min(remaining, 65536))
    if not chunk:
        raise SystemExit('Image transfer ended early')
    chunks.append(chunk)
    remaining -= len(chunk)
data = base64.b64decode(b''.join(chunks), validate=True)
target.parent.mkdir(parents=True, exist_ok=True)
temporary = target.with_suffix(target.suffix + '.tmp')
temporary.write_bytes(data)
temporary.replace(target)
print('\nSAVED ' + str(target) + ' (' + str(len(data)) + ' bytes)', flush=True)
