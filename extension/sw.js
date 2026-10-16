// Keyboard shortcut (Alt+Shift+D): toggles the theme for the current site by
// flipping its hostname in storage; content scripts react via storage events.
const KEY = 'btState';
const DEFAULT = { enabled: true, siteOff: [], brightness: 1, contrast: 1, sepia: false, lang: 'auto' };

chrome.commands.onCommand.addListener(async (command) => {
  if (command !== 'toggle-site') return;
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab?.url?.startsWith('http')) return; // firing the command grants activeTab
  let host = '';
  try { host = new URL(tab.url).hostname; } catch { return; }
  const state = { ...DEFAULT, ...((await chrome.storage.local.get(KEY))[KEY] ?? {}) };
  const off = new Set(state.siteOff);
  off.has(host) ? off.delete(host) : off.add(host);
  await chrome.storage.local.set({ [KEY]: { ...state, siteOff: [...off] } });
});
