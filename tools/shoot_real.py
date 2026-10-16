"""Capture README screenshots on real websites: dark / sepia / off per site.

Run: python tools/shoot_real.py   (needs playwright + network access)
Writes docs/screenshots/real-<site>-<mode>.png
"""
import tempfile
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
EXT = str(ROOT / 'extension')
OUT = ROOT / 'docs' / 'screenshots'
OUT.mkdir(parents=True, exist_ok=True)

SITES = [
    ('bing', 'https://www.bing.com/search?q=chrome+dark+theme'),
    ('baidu', 'https://www.baidu.com/s?wd=chrome%20%E9%BB%91%E8%89%B2%E4%B8%BB%E9%A2%98'),
]
MODES = [('dark', 'btDark'), ('sepia', 'btSepia'), ('off', 'btOff')]


def get_ext_id(ctx):
    page = ctx.new_page()
    page.goto('chrome://extensions')
    page.wait_for_load_state('networkidle')
    infos = page.evaluate("new Promise(res => chrome.developerPrivate.getExtensionsInfo(res))")
    page.close()
    for info in infos:
        if info.get('location') == 'UNPACKED':
            return info['id']
    raise RuntimeError('unpacked extension not found')


with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        user_data_dir=tempfile.mkdtemp(prefix='bt-shot-'),
        headless=False,
        args=[f'--disable-extensions-except={EXT}', f'--load-extension={EXT}'],
        viewport={'width': 1200, 'height': 800},
        locale='zh-CN',
    )
    try:
        ext_id = get_ext_id(ctx)
        console = ctx.new_page()
        console.goto(f'chrome-extension://{ext_id}/popup.html')
        console.wait_for_load_state('networkidle')

        def set_mode(mode):
            state = {'dark': {'enabled': True, 'sepia': False},
                     'sepia': {'enabled': True, 'sepia': True},
                     'off': {'enabled': False}}[mode]
            console.evaluate(
                "(patch) => chrome.storage.local.set({btState: Object.assign("
                "{enabled: true, siteOff: [], brightness: 1, contrast: 1, sepia: false, lang: 'auto'},"
                " patch)})",
                state)
            time.sleep(0.5)

        page = ctx.new_page()
        for site_name, url in SITES:
            page.goto(url, timeout=60000)
            page.wait_for_load_state('networkidle')
            time.sleep(2.5)
            for mode, _ in MODES:
                set_mode(mode)
                time.sleep(1.0)  # storage change propagates and repaints
                path = OUT / f'real-{site_name}-{mode}.png'
                page.screenshot(path=str(path))
                print('captured:', path.name)
    finally:
        ctx.close()
