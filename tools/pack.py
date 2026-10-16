"""Pack the extension into a CRX: python tools/pack.py

Reuses black-theme.pem when present so upgrades keep the same extension ID.
A fresh run generates a new private key -- back it up (losing it changes the ID).

Note: Windows Chrome refuses to install CRX files from outside the Web Store;
either keep using "Load unpacked" or publish via the Chrome Web Store.
"""
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXT = ROOT / 'extension'
CHROME = Path(r'C:\Program Files\Google\Chrome\Application\chrome.exe')
KEY = ROOT / 'black-theme.pem'

if not CHROME.exists():
    raise SystemExit(f'Chrome not found: {CHROME}')

cmd = [
    str(CHROME),
    f'--pack-extension={EXT}',
    # A throwaway profile avoids forwarding args to an already-running instance
    f'--user-data-dir={tempfile.mkdtemp(prefix="bt-pack-")}',
    '--no-first-run',
]
if KEY.exists():
    cmd.append(f'--pack-extension-key={KEY}')

subprocess.run(cmd, check=True)
for name in ('extension.crx', 'extension.pem'):
    src = ROOT / name
    if src.exists():
        shutil.move(src, ROOT / f'black-theme{src.suffix}')

print('packed:', ROOT / 'black-theme.crx')
print('key:', KEY, '(reused)' if KEY.exists() else '(new -- back it up)')
