import { api } from './api.js';
import { state } from './state.js';
import { t } from './i18n.js';
import { pullConfigs } from './config-sync.js';

export async function checkServer() {
  const dot = document.getElementById('status-dot');
  const txt = document.getElementById('status-text');
  if (!dot) return;
  dot.className = 'status-dot checking';
  txt.textContent = t('Connecting…');
  try {
    await api.get('/ping');
    const wasOffline = state.serverOnline === false;
    state.serverOnline = true;
    dot.className = 'status-dot connected';
    txt.textContent = t('Connected');
    if (wasOffline) pullConfigs();
  } catch {
    state.serverOnline = false;
    dot.className = 'status-dot disconnected';
    txt.textContent = t('Disconnected');
  }
}

export function startPolling() {
  clearInterval(state.pollTimer);
  clearInterval(state.connectTimer);
  checkServer();
  pullConfigs();
  state.connectTimer = setInterval(checkServer, 5000);
  state.pollTimer = setInterval(async () => {
    if (!state.syncInFlight && state.serverOnline) await pullConfigs();
  }, 2000);
}
