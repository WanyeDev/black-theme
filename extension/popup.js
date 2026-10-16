const KEY = 'btState';
const DEFAULT = { enabled: true, siteOff: [], brightness: 1, contrast: 1, sepia: false, lang: 'auto' };

// Popup UI strings. Manifest metadata goes through _locales (chrome.i18n);
// a manual language switch needs this in-page dictionary because
// chrome.i18n.getMessage() only reads the browser locale.
const MESSAGES = {
  zh: {
    title: '纯黑主题',
    modeOff: '关闭', modeDark: '黑暗', modeSepia: '护眼',
    brightness: '亮度', contrast: '对比',
    siteGroup: '站点过滤', siteToggle: '当前网站保持原样',
    inputPlaceholder: '输入网址，如 github.com', add: '添加',
    emptyList: '暂无过滤网站', remove: '移除',
    reset: '恢复默认设置', resetConfirm: '恢复默认设置并清空网站过滤名单？',
    notWeb: '非网页',
  },
  en: {
    title: 'Pure Black',
    modeOff: 'Off', modeDark: 'Dark', modeSepia: 'Sepia',
    brightness: 'Brightness', contrast: 'Contrast',
    siteGroup: 'Site filter', siteToggle: 'Keep this site as-is',
    inputPlaceholder: 'e.g. github.com', add: 'Add',
    emptyList: 'No filtered sites yet', remove: 'Remove',
    reset: 'Reset to defaults', resetConfirm: 'Reset all settings and clear the site filter list?',
    notWeb: 'Not a web page',
  },
};

let t = MESSAGES.zh; // active dictionary, refreshed by applyLang()

/** Resolve the UI language: explicit choice wins, otherwise follow the browser. */
function uiLang(state) {
  if (state.lang === 'zh' || state.lang === 'en') return state.lang;
  return chrome.i18n.getUILanguage().toLowerCase().startsWith('zh') ? 'zh' : 'en';
}

/** Translate all [data-i18n] / [data-i18n-ph] nodes to the active language. */
function applyLang(state) {
  const lang = uiLang(state);
  t = MESSAGES[lang];
  document.documentElement.lang = lang === 'zh' ? 'zh-CN' : 'en';
  for (const el of document.querySelectorAll('[data-i18n]')) el.textContent = t[el.dataset.i18n];
  for (const el of document.querySelectorAll('[data-i18n-ph]')) el.placeholder = t[el.dataset.i18nPh];
}

/** Read the persisted state merged over defaults (missing fields tolerated). */
const getState = async () => ({ ...DEFAULT, ...((await chrome.storage.local.get(KEY))[KEY] ?? {}) });

/** Persist a shallow patch on top of the current state. */
async function save(patch) {
  await chrome.storage.local.set({ [KEY]: { ...(await getState()), ...patch } });
}

/** Normalize user input to a hostname: "github.com" and "https://github.com/x" both yield "github.com". */
function toHost(text) {
  const s = text.trim();
  if (!s) return '';
  try {
    return new URL(/^https?:\/\//i.test(s) ? s : 'https://' + s).hostname;
  } catch { return ''; }
}

init();

async function init() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  let host = '';
  try {
    if (tab?.url?.startsWith('http')) host = new URL(tab.url).hostname;
  } catch { /* not a regular web page: site controls stay disabled */ }

  const $ = (id) => document.getElementById(id);
  const seg = { off: $('mode-off'), dark: $('mode-dark'), sepia: $('mode-sepia') };
  const brightness = $('brightness');
  const contrast = $('contrast');
  const site = $('site');
  const list = $('list');

  /** Wire a range slider: live label update, persist on release. */
  function bindSlider(slider, valEl, key) {
    const show = () => { valEl.textContent = `${slider.value}%`; };
    slider.oninput = show;
    slider.onchange = () => save({ [key]: Number(slider.value) / 100 }).then(render);
    return show;
  }
  const showBrightness = bindSlider(brightness, $('bval'), 'brightness');
  const showContrast = bindSlider(contrast, $('cval'), 'contrast');

  function renderList(siteOff) {
    list.textContent = '';
    if (!siteOff.length) {
      const empty = document.createElement('div');
      empty.className = 'empty';
      empty.textContent = t.emptyList;
      list.append(empty);
      return;
    }
    for (const h of siteOff) {
      const item = document.createElement('div');
      item.className = 'item';
      const name = document.createElement('span');
      name.textContent = h;
      const del = document.createElement('button');
      del.textContent = '✕';
      del.title = t.remove;
      del.onclick = async () => {
        const cur = await getState();
        await save({ siteOff: cur.siteOff.filter((x) => x !== h) });
        render();
      };
      item.append(name, del);
      list.append(item);
    }
  }

  /** Re-render the whole popup from storage; single source of truth. */
  async function render() {
    const st = await getState();
    applyLang(st);
    const mode = st.enabled ? (st.sepia ? 'sepia' : 'dark') : 'off';
    for (const [m, btn] of Object.entries(seg)) btn.classList.toggle('active', m === mode);
    document.body.dataset.mode = mode;
    const isOff = mode === 'off';
    brightness.disabled = isOff;
    contrast.disabled = isOff;
    brightness.value = Math.round((Number(st.brightness) || 1) * 100);
    contrast.value = Math.round((Number(st.contrast) || 1) * 100);
    showBrightness();
    showContrast();
    site.checked = !!host && st.siteOff.includes(host);
    site.disabled = !host;
    $('host').textContent = host || t.notWeb;
    $('lang').value = st.lang || 'auto';
    renderList(st.siteOff);
  }

  seg.off.onclick = () => save({ enabled: false }).then(render);
  seg.dark.onclick = () => save({ enabled: true, sepia: false }).then(render);
  seg.sepia.onclick = () => save({ enabled: true, sepia: true }).then(render);
  $('lang').onchange = () => save({ lang: $('lang').value }).then(render);

  site.onchange = async () => {
    const off = new Set((await getState()).siteOff);
    off[site.checked ? 'add' : 'delete'](host);
    await save({ siteOff: [...off] });
    render();
  };

  $('add').onsubmit = async (e) => {
    e.preventDefault();
    const input = $('input');
    const h = toHost(input.value);
    if (!h) { input.value = ''; return; }
    const off = new Set((await getState()).siteOff);
    off.add(h);
    await save({ siteOff: [...off] });
    input.value = '';
    render();
  };

  $('reset').onclick = async () => {
    if (!confirm(t.resetConfirm)) return;
    await chrome.storage.local.set({ [KEY]: DEFAULT });
    render();
  };

  await render();
}
