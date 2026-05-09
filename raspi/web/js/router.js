import { state, invalidateDashboardCache } from './state.js';
import { t } from './i18n.js';
import { closeAllModals } from './ui.js';
import { navigate, setRenderer } from './navigate.js';
import { renderDashboard } from './views/dashboard.js';
import { renderCamera } from './views/camera.js';
import { renderSettingsHub, renderHASettings, renderGestureSettings, renderCameraSettings, renderIronmanSettings } from './views/settings.js';

export { navigate };

function dispatch() {
  if (state.view === 'dashboard') renderDashboard();
  else if (state.view === 'camera') renderCamera();
  else if (state.view === 'settings') {
    if (state.subView === 'ha') renderHASettings();
    else if (state.subView === 'gesture') renderGestureSettings();
    else if (state.subView === 'camera-cfg') renderCameraSettings();
    else if (state.subView === 'ironman') renderIronmanSettings();
    else renderSettingsHub();
  }
}
setRenderer(dispatch);

export function render() { dispatch(); }

export function applyStaticTranslations() {
  document.querySelectorAll('[data-i18n]').forEach(el => {
    el.textContent = t(el.getAttribute('data-i18n'));
  });
  document.querySelectorAll('.lang-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.lang === state.lang);
  });
  const txt = document.getElementById('status-text');
  if (txt) {
    if (state.serverOnline === true) txt.textContent = t('Connected');
    else if (state.serverOnline === false) txt.textContent = t('Disconnected');
    else txt.textContent = t('Connecting…');
  }
}

export function setLanguage(lang) {
  if (lang !== 'en' && lang !== 'el') return;
  if (state.lang === lang) return;
  state.lang = lang;
  try { localStorage.setItem('sensee.lang', lang); } catch {}
  applyStaticTranslations();
  closeAllModals();
  invalidateDashboardCache();
  dispatch();
}
