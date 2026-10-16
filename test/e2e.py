"""End-to-end regression: loads the real extension into Chromium via Playwright
and drives the popup like a user. Covers 11 scenarios: default-on, global off,
per-site exclusion and restore, URL filter add/remove, sepia mode, brightness,
contrast, reset-to-defaults, and language switching.

Run: python test/e2e.py  (requires playwright + bundled chromium)
"""
import json
import tempfile
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

TEST = Path(__file__).resolve().parent
EXT = str(TEST.parent / 'extension')
PAGE_URL = 'http://black.test/page.html'
HOST = 'black.test'


def get_ext_id(ctx):
    """Find the unpacked extension ID via chrome://extensions internals
    (the MV3 service worker list is unreliable for this)."""
    page = ctx.new_page()
    page.goto('chrome://extensions')
    page.wait_for_load_state('networkidle')
    infos = page.evaluate("new Promise(res => chrome.developerPrivate.getExtensionsInfo(res))")
    page.close()
    for info in infos:
        if info.get('location') == 'UNPACKED':
            return info['id']
    raise RuntimeError('unpacked extension not found: --load-extension failed')


def shot(page, name):
    page.screenshot(path=str(TEST / name))
    print('screenshot:', name)


def set_slider(popup, slider_id, value):
    """Set a range input and dispatch input/change (Playwright cannot fill ranges)."""
    popup.evaluate(
        f"const s = document.getElementById('{slider_id}');"
        f"s.value = {value};"
        "s.dispatchEvent(new Event('input', {bubbles: true}));"
        "s.dispatchEvent(new Event('change', {bubbles: true}));"
    )


def wait_mode(page, expected):
    page.wait_for_function(
        f"document.documentElement.getAttribute('data-bt') === '{expected}'", timeout=5000)


def main():
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=tempfile.mkdtemp(prefix='bt-e2e-'),
            headless=False,
            args=[
                f'--disable-extensions-except={EXT}',
                f'--load-extension={EXT}',
                '--proxy-server=direct://',  # bypass corporate proxies
                '--proxy-bypass-list=*',
            ],
            viewport={'width': 900, 'height': 700},
        )
        try:
            # Serve test pages locally via route interception (no real network).
            def serve(route):
                url = route.request.url
                if url.endswith('dot.svg'):
                    route.fulfill(content_type='image/svg+xml',
                                  body=(TEST / 'dot.svg').read_text(encoding='utf-8'))
                else:
                    route.fulfill(content_type='text/html',
                                  body=(TEST / 'page.html').read_text(encoding='utf-8'))

            # Only intercept the test domain: catching chrome-extension:// URLs
            # would replace popup.js with HTML ("Unexpected token '<'").
            ctx.route('http://black.test/**', serve)

            ext_id = get_ext_id(ctx)
            print('extension id:', ext_id)

            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            page.goto(PAGE_URL)
            page.wait_for_load_state('networkidle')

            # 1. Default-on (regression: fresh profile + empty storage must not crash)
            wait_mode(page, 'on')
            flt = page.evaluate("getComputedStyle(document.documentElement).filter")
            assert 'invert' in flt, f'filter not applied: {flt}'
            print('PASS 1 default on, filter =', flt)
            shot(page, 'shot-1-on.png')

            # 2. Global off propagates live to already-open pages
            popup = ctx.new_page()
            popup.goto(f'chrome-extension://{ext_id}/popup.html')
            popup.wait_for_load_state('networkidle')
            popup.locator('#mode-off').click()
            wait_mode(page, 'off')
            assert 'invert' not in page.evaluate("getComputedStyle(document.documentElement).filter")
            print('PASS 2 global off applies live')
            shot(page, 'shot-2-off.png')

            # 3. Per-site exclusion via siteOff
            popup.locator('#mode-dark').click()
            popup.evaluate(f"chrome.storage.local.set({{btState: {{enabled: true, siteOff: ['{HOST}']}}}})")
            wait_mode(page, 'off')
            print('PASS 3 per-site exclusion')

            # 4. Removing the exclusion restores the theme
            popup.evaluate("chrome.storage.local.set({btState: {enabled: true, siteOff: []}})")
            wait_mode(page, 'on')
            print('PASS 4 exclusion removed')

            # 5. URL input normalizes to hostname and persists
            popup.locator('#input').fill('https://github.com/whatever')
            popup.locator('#add button').click()
            time.sleep(0.3)
            saved = popup.evaluate("chrome.storage.local.get('btState').then(d => d.btState.siteOff)")
            assert 'github.com' in saved, f'not saved: {saved}'
            assert popup.locator('#list .item', has_text='github.com').count() == 1, 'list not rendered'
            print("PASS 5 URL filter (github.com) persisted:", saved)

            # 6. Removing from the list works
            popup.locator('#list .item', has_text='github.com').locator('button').click()
            time.sleep(0.3)
            saved = popup.evaluate("chrome.storage.local.get('btState').then(d => d.btState.siteOff)")
            assert 'github.com' not in saved, f'removal failed: {saved}'
            print('PASS 6 list removal')

            # 7. Sepia mode appends sepia() to the filter chain
            popup.locator('#mode-sepia').click()
            page.wait_for_function(
                "getComputedStyle(document.documentElement).filter.includes('sepia')", timeout=5000)
            print('PASS 7 sepia mode')
            shot(page, 'shot-3-sepia.png')

            # 8. Brightness slider
            popup.locator('#mode-dark').click()
            page.wait_for_function(
                "!getComputedStyle(document.documentElement).filter.includes('sepia')", timeout=5000)
            set_slider(popup, 'brightness', 80)
            page.wait_for_function(
                "getComputedStyle(document.documentElement).filter.includes('brightness(0.8)')", timeout=5000)
            print('PASS 8 brightness 80%')

            # 9. Contrast slider
            set_slider(popup, 'contrast', 80)
            page.wait_for_function(
                "getComputedStyle(document.documentElement).filter.includes('contrast(0.8)')", timeout=5000)
            print('PASS 9 contrast 80%')

            # 10. Reset to defaults (clears the list, restores filters)
            popup.on('dialog', lambda d: d.accept())
            popup.locator('#reset').click()
            time.sleep(0.3)
            final = popup.evaluate("chrome.storage.local.get('btState').then(d => JSON.stringify(d.btState))")
            assert json.loads(final) == {
                'enabled': True, 'siteOff': [], 'brightness': 1, 'contrast': 1,
                'sepia': False, 'lang': 'auto',
            }, final
            page.wait_for_function(
                "!getComputedStyle(document.documentElement).filter.includes('brightness')", timeout=5000)
            print('PASS 10 reset to defaults')

            # 11. Language switch persists and translates the popup
            popup.select_option('#lang', 'en')
            time.sleep(0.3)
            assert popup.locator('label[for="brightness"]').inner_text() == 'Brightness'
            saved_lang = popup.evaluate("chrome.storage.local.get('btState').then(d => d.btState.lang)")
            assert saved_lang == 'en', saved_lang
            shot(popup, 'shot-popup-en.png')
            popup.select_option('#lang', 'auto')
            print('PASS 11 language switch (en) persisted')

            # Final popup screenshot with one list entry
            popup.locator('#input').fill('github.com')
            popup.locator('#add button').click()
            time.sleep(0.3)
            shot(popup, 'shot-popup.png')
        finally:
            ctx.close()


if __name__ == '__main__':
    main()
    print('ALL PASS')
