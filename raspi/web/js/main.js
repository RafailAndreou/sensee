import { applyStaticTranslations, navigate, setLanguage } from './router.js';
import { setSidebarCollapsed } from './sidebar.js';
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

  // Sidebar collapse toggle
  let savedCollapsed = false;
  try { savedCollapsed = localStorage.getItem('sensee.sidebarCollapsed') === '1'; } catch {}
  setSidebarCollapsed(savedCollapsed);
  document.getElementById('sidebar-toggle').addEventListener('click', () => setSidebarCollapsed(true));
  document.getElementById('sidebar-open-btn').addEventListener('click', () => setSidebarCollapsed(false));

  applyStaticTranslations();
  navigate('dashboard');
  startPolling();
});
