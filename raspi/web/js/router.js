import { state } from './state.js';
import { t } from './i18n.js';
import { closeAllModals } from './ui.js';
import { renderDashboard, invalidateDashboardCache } from './views/dashboard.js';
import { renderCamera } from './views/camera.js';
import { renderSettingsHub, renderHASettings, renderGestureSettings, renderCameraSettings } from './views/settings.js';

export function navigate(view, subView = null) {
  state.view = view;
  state.subView = subView;
  document.querySelectorAll('.nav-item').forEach(el => {
    el.classList.toggle('active', el.dataset.view === view);
  });
  render();
}

export function render() {
  if (state.view === 'dashboard') renderDashboard();
  else if (state.view === 'camera') renderCamera();
  else if (state.view === 'settings') {
    if (state.subView === 'ha') renderHASettings();
    else if (state.subView === 'gesture') renderGestureSettings();
    else if (state.subView === 'camera-cfg') renderCameraSettings();
    else renderSettingsHub();
  }
}

export function applyStaticTranslations() {
  document.querySelectorAll('[data-i18n]').forEach(el => {
    el.textContent = t(el.getAttribute('data-i18n'));
  });
  document.querySelectorAll('.lang-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.lang === state.lang);
  });
  // Refresh current status text in user's language
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
  render();
}
