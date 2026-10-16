# 代码导读（中文注释版）

> 对应 v1.0.0 快照；源码以 `extension/` 目录为准，本文件用于中文阅读理解。
> 源码使用英文注释（国际化规范），这里保留一份中文注释版本。

## content.js — 页面侧开关

```js
// 根据 storage 给 <html> 打开关标记；护眼/亮度/对比度以内联 filter 叠加，
// dark.css 提供兜底（JS 未执行时也有基本暗色）
const KEY = 'btState';

function apply(state = {}) {
  const root = document.documentElement;
  if (!root) return;
  // 开关条件：全局启用，且当前域名不在过滤名单里
  const on = state.enabled !== false && !(state.siteOff || []).includes(location.hostname);
  root.setAttribute('data-bt', on ? 'on' : 'off');
  if (!on) {
    root.style.removeProperty('filter'); // 关闭时彻底清除内联滤镜，页面回到原样
    return;
  }
  // 滤镜链：反转 + 色相旋转是基础；护眼加 sepia；滑杆非默认值时追加
  const filters = ['invert(1)', 'hue-rotate(180deg)'];
  if (state.sepia) filters.push('sepia(0.35)');
  const brightness = Number(state.brightness) || 1;
  if (brightness !== 1) filters.push(`brightness(${brightness})`);
  const contrast = Number(state.contrast) || 1;
  if (contrast !== 1) filters.push(`contrast(${contrast})`);
  root.style.setProperty('filter', filters.join(' '), 'important');
}

function boot(state) {
  // document_start 时 documentElement 理论上已存在，兜底等 DOM 就绪
  if (document.documentElement) apply(state);
  else document.addEventListener('DOMContentLoaded', () => apply(state), { once: true });
}

// 首次读取 + 监听变化：弹窗里的任何改动实时传播到已打开页面，无需刷新
chrome.storage.local.get(KEY, ({ [KEY]: state }) => boot(state));
chrome.storage.onChanged.addListener((changes, area) => {
  if (area === 'local' && changes[KEY]) apply(changes[KEY].newValue);
});
```

## dark.css — 预失真标定的滤镜样式

```css
/* 观感对齐 GitHub Primer Dark：底色 #0d1117、正文 #e6edf3。
   原理是预失真：输入 rgb(232,238,242) 经 invert+hue-rotate(180)
   恰好落在 GitHub 底色上，避免死黑；R/B 与直觉相反是 hue-rotate 的色相补偿 */
/* shortcut: filter 会改变 position:fixed/sticky 的定位基准，
   个别网站的悬浮元素会跟着页面滚动 */
:root[data-bt="on"] {
  filter: invert(1) hue-rotate(180deg) !important;
  background-color: rgb(232, 238, 242) !important; /* 反相后 = #0d1117 */
  color: rgb(25, 18, 12) !important; /* 反相后 = #e6edf3 */
}

:root[data-bt="on"] body { /* 同样预置，覆盖大多数白底站点 */ }

/* 媒体内容反转回来，图片视频保持原色（image 覆盖 SVG 内嵌位图） */
:root[data-bt="on"] :is(img, video, picture, canvas, image) {
  filter: invert(1) hue-rotate(180deg) !important;
}
```

## sw.js — 快捷键处理（service worker）

```js
// Alt+Shift+D：把当前站点的域名在过滤名单里进出切换；
// content script 通过 storage 事件自动响应，无需消息通信
const KEY = 'btState';
const DEFAULT = { enabled: true, siteOff: [], brightness: 1, contrast: 1, sepia: false, lang: 'auto' };

chrome.commands.onCommand.addListener(async (command) => {
  if (command !== 'toggle-site') return;
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab?.url?.startsWith('http')) return; // 命令触发即授予 activeTab，可读 url
  let host = '';
  try { host = new URL(tab.url).hostname; } catch { return; }
  // 读改写：展开默认值再覆盖，保证不丢已有字段
  const state = { ...DEFAULT, ...((await chrome.storage.local.get(KEY))[KEY] ?? {}) };
  const off = new Set(state.siteOff);
  off.has(host) ? off.delete(host) : off.add(host);
  await chrome.storage.local.set({ [KEY]: { ...state, siteOff: [...off] } });
});
```

## popup.js — 设置弹窗（关键部分）

```js
const KEY = 'btState';
const DEFAULT = { enabled: true, siteOff: [], brightness: 1, contrast: 1, sepia: false, lang: 'auto' };

// 弹窗文案字典。manifest 元数据走 _locales（chrome.i18n 标准机制）；
// 手动切换语言需要页内字典，因为 chrome.i18n.getMessage() 只认浏览器语言
const MESSAGES = { zh: { /* ... */ }, en: { /* ... */ } };
let t = MESSAGES.zh; // 当前字典，applyLang() 刷新

// 语言解析：显式选择优先，否则跟随浏览器
function uiLang(state) {
  if (state.lang === 'zh' || state.lang === 'en') return state.lang;
  return chrome.i18n.getUILanguage().toLowerCase().startsWith('zh') ? 'zh' : 'en';
}

// 翻译所有带 data-i18n / data-i18n-ph 的节点（文本 / 输入框占位符）
function applyLang(state) { /* 遍历节点赋值 */ }

// 读状态：默认值打底合并，容忍旧版本缺字段
const getState = async () => ({ ...DEFAULT, ...((await chrome.storage.local.get(KEY))[KEY] ?? {}) });

// 写状态：浅合并补丁
async function save(patch) { /* ... */ }

// 输入归一化：github.com 和 https://github.com/x 都得到 github.com
function toHost(text) { /* 补协议后取 hostname */ }

async function init() {
  // 当前标签页域名（activeTab 授权），非网页时站点控件禁用
  // ...
  // render() 是唯一渲染入口：从 storage 读全量状态重画
  // 模式按钮 → save({enabled/sepia})；滑杆松手才写库；语言切换即存
  // reset：confirm 确认后直接写 DEFAULT（清空名单）
}
```

## manifest.json — 要点

- `"default_locale": "zh_CN"` + `__MSG_extName__`：名称与描述按浏览器语言显示中/英文（Chrome i18n 标准机制）
- `"commands"`：注册 `Alt+Shift+D`（suggested_key 是建议值，用户可在 chrome://extensions/shortcuts 改键）
- 权限仅 `storage` + `activeTab`（点击图标/快捷键时才临时授予当前标签页访问）

## test/e2e.py — 回归测试思路

- `launch_persistent_context` + `--load-extension` 加载真实扩展（Playwright 自带 Chromium）
- `ctx.route` 只拦测试域供页面内容（拦 `chrome-extension://` 会把 popup.js 换成 HTML）
- 扩展 ID 从 `chrome://extensions` 的 `chrome.developerPrivate.getExtensionsInfo` 获取（MV3 service worker 列表不可靠）
- 11 条链路覆盖：默认开启（含首装空 storage 回归）、全局开关实时传播、本站排除/恢复、URL 过滤增删、护眼、亮度、对比度、恢复默认、语言切换
