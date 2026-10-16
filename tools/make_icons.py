"""Rasterize icons/icon.svg into 16/32/48/128 PNGs under extension/icons/
(Chrome manifests only accept bitmaps). Re-run after editing the SVG."""
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / 'icons' / 'icon.svg'
OUT = ROOT / 'extension' / 'icons'
OUT.mkdir(exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={'width': 128, 'height': 128}, device_scale_factor=2)
    page.set_content(f'<body style="margin:0">{SRC.read_text(encoding="utf-8")}</body>')
    # omit_background keeps the area outside the circle transparent
    page.locator('#bt-icon').screenshot(path=str(OUT / '128.png'), omit_background=True)
    browser.close()

source = Image.open(OUT / '128.png').convert('RGBA')
for size in (16, 32, 48, 128):
    source.resize((size, size), Image.LANCZOS).save(OUT / f'{size}.png')
print('icons written to extension/icons/:', sorted(f.name for f in OUT.glob('*.png')))
