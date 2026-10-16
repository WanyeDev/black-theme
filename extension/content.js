// Marks <html> with the on/off flag from storage; sepia/brightness/contrast are
// applied as an inline filter on top of the dark.css baseline.
const KEY = 'btState';

function apply(state = {}) {
  const root = document.documentElement;
  if (!root) return;
  const on = state.enabled !== false && !(state.siteOff || []).includes(location.hostname);
  root.setAttribute('data-bt', on ? 'on' : 'off');
  if (!on) {
    root.style.removeProperty('filter');
    return;
  }
  const filters = ['invert(1)', 'hue-rotate(180deg)'];
  if (state.sepia) filters.push('sepia(0.35)');
  const brightness = Number(state.brightness) || 1;
  if (brightness !== 1) filters.push(`brightness(${brightness})`);
  const contrast = Number(state.contrast) || 1;
  if (contrast !== 1) filters.push(`contrast(${contrast})`);
  root.style.setProperty('filter', filters.join(' '), 'important');
}

function boot(state) {
  if (document.documentElement) apply(state);
  else document.addEventListener('DOMContentLoaded', () => apply(state), { once: true });
}

chrome.storage.local.get(KEY, ({ [KEY]: state }) => boot(state));
chrome.storage.onChanged.addListener((changes, area) => {
  if (area === 'local' && changes[KEY]) apply(changes[KEY].newValue);
});
