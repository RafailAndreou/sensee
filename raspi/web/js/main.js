import { applyStaticTranslations, navigate, setLanguage } from './router.js';
import { initSidebar } from './sidebar.js';
import { startPolling } from './server-status.js';
import { ensurePaired } from './auth.js';

document.addEventListener('DOMContentLoaded', async () => {
  try {
    await ensurePaired();
  } catch (error) {
    document.getElementById('main-content').textContent = error.message;
    return;
  }
  window.addEventListener('sensee-unpaired', () => {
    ensurePaired().then(() => navigate('dashboard')).catch(error => console.error('Pairing failed', error));
  });
  // Sidebar nav
  document.querySelectorAll('.nav-item[data-view]').forEach(el => {
    el.addEventListener('click', () => navigate(el.dataset.view));
  });

  // Language switcher
  document.querySelectorAll('.lang-btn').forEach(btn => {
    btn.addEventListener('click', () => setLanguage(btn.dataset.lang));
  });

  initSidebar();

  applyStaticTranslations();
  navigate('dashboard');
  startPolling();
});
