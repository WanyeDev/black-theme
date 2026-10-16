# Pure Black Theme

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Chrome Manifest V3](https://img.shields.io/badge/Chrome-Manifest_V3-34a853.svg)
![e2e tests](https://img.shields.io/badge/e2e-11%20passed-brightgreen.svg)

English | [简体中文](README.zh-CN.md)

A pure black theme for Chrome that covers **both** web pages and the browser UI. Pages get a filter-based dark theme calibrated to the GitHub Primer Dark palette; the browser chrome gets a companion black theme.

> Chrome platform constraint: an extension cannot restyle the browser UI, and a theme cannot ship scripts or a popup — hence one extension for pages plus one companion theme for the UI.

## Features

- **Three modes**: Off (pages untouched) / Dark / Sepia (warm, low blue light)
- **Brightness & contrast sliders** (60%–140%, applied live, persisted)
- **Permanent site filter**: type `github.com` or paste any URL — normalized to the hostname, kept in a manageable list, survives restarts
- **Keyboard shortcut** `Alt+Shift+D` toggles the theme for the current site
- **Bilingual UI** (中文 / English), follows the browser language by default
- **Reset to defaults** with one click
- Zero network requests, no analytics, settings stored only in `chrome.storage.local`

## Screenshots

Settings popup (Chinese / English):

| 中文 | English |
|---|---|
| ![popup zh](docs/screenshots/shot-popup.png) | ![popup en](docs/screenshots/shot-popup-en.png) |

Real websites (Bing / Baidu search, live captures) — dark / sepia / off:

| Site | Dark | Sepia | Off |
|---|---|---|---|
| Bing | ![bing dark](docs/screenshots/real-bing-dark.png) | ![bing sepia](docs/screenshots/real-bing-sepia.png) | ![bing off](docs/screenshots/real-bing-off.png) |
| Baidu | ![baidu dark](docs/screenshots/real-baidu-dark.png) | ![baidu sepia](docs/screenshots/real-baidu-sepia.png) | ![baidu off](docs/screenshots/real-baidu-off.png) |

## Install (unpacked)

1. Open `chrome://extensions`, enable **Developer mode**.
2. **Load unpacked** → select the `extension` folder.
3. Load unpacked again → select the `browser-theme` folder (the UI turns black immediately).

Windows Chrome refuses to install CRX files from outside the Web Store; to distribute, publish to the [Chrome Web Store](https://chrome.google.com/webstore/devconsole) (packing: `python tools/pack.py`).

## Usage

- Click the moon icon for settings; dark mode highlights in blue, sepia in amber.
- Already-dark sites get washed out by the inversion — exclude them via the site filter or `Alt+Shift+D`.
- Restore Chrome's default look: reset the theme in `chrome://settings/appearance`, or disable the extension.

## Project structure

```
black-theme/
├─ extension/          # page extension
│  ├─ manifest.json
│  ├─ dark.css         # filter styles, calibrated to #0d1117 / #e6edf3
│  ├─ content.js       # page flag + filter parameters
│  ├─ popup.html / popup.js
│  ├─ sw.js            # keyboard shortcut handler
│  ├─ _locales/        # zh_CN / en messages
│  └─ icons/           # rasterized icons
├─ browser-theme/      # companion theme for the Chrome UI
├─ icons/icon.svg      # icon source
├─ tools/
│  ├─ make_icons.py    # SVG → PNGs (re-run after editing the SVG)
│  └─ pack.py          # CRX packing (reuses the .pem to keep the ID)
└─ test/
   ├─ e2e.py           # 11-scenario Playwright regression
   └─ page.html etc.   # fixtures and screenshots
```

## Development

```bash
python tools/make_icons.py   # regenerate icons after editing icons/icon.svg
python test/e2e.py           # end-to-end regression (needs playwright)
python tools/pack.py         # pack black-theme.crx
```

## Known limitations

- Filter approach: background images may shift color; `position: fixed/sticky` elements can scroll with the page on some sites.
- Canvas-based apps (Google Docs, Figma) render as bitmaps and cannot be selectively themed — exclude them.
- Already-dark sites get inverted light — that is what the site filter is for.

## Privacy

No data collection, no network requests, no analytics. All settings live in `chrome.storage.local` on your machine.

## Security

Audited attack surface (2026-10):

- **Minimal permissions**: only `storage` + `activeTab`; no host permissions, no `<all_urls>` data access, no devtools access.
- **Zero network activity**: no fetch/XHR/WebSocket; MV3 default CSP forbids remote code and none is used.
- **No injection sinks**: no `innerHTML`, no `eval`/`new Function`; all dynamic DOM writes go through `textContent`.
- **Untrusted values hardened**: filter parameters are coerced via `Number()` with fallbacks; hostnames are normalized through `new URL()` before storage; attribute values are fixed strings.
- **Key hygiene**: the signing `.pem` is git-ignored and never distributed.

Known inherent caveat (same class as any dark-mode extension): content scripts run on all http(s) pages, so a page can technically detect the `data-bt` attribute or the filter effect. No page content is ever read or transmitted.

## Disclaimer

This extension is provided "as is" under the MIT License, without warranty of any kind, express or implied. The authors accept no liability for any display issues, misrendered content, or losses arising from its use. Theme filters may alter how some websites appear — exclude any site via the site filter when its exact presentation matters. Use on production workflows (e.g. design QA, color-sensitive work) is at your own discretion.

## License

[MIT](LICENSE)
