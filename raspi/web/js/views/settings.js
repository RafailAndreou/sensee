import { t } from '../i18n.js';
import { GESTURES } from '../constants.js';
import { api } from '../api.js';
import { escHtml, escAttr } from '../utils.js';
import { showModal, toast } from '../ui.js';
import { navigate } from '../router.js';

/* ─── Settings Hub ──────────────────────────────────────────────────────── */
export function renderSettingsHub() {
  const main = document.getElementById('main-content');
  main.innerHTML = `
    <div class="view">
      <div class="page-header">
        <div>
          <div class="page-title">${escHtml(t('Settings'))}</div>
          <div class="page-sub">${escHtml(t('Configure your Sensee hub'))}</div>
        </div>
      </div>
      <div class="settings-grid">
        <div class="settings-card" data-sub="ha">
          <div class="settings-card-icon" style="background:rgba(79,158,255,.15)">🏠</div>
          <div class="settings-card-body">
            <div class="settings-card-title">${escHtml(t('Home Assistant'))}</div>
            <div class="settings-card-sub">${escHtml(t('URL and access token'))}</div>
          </div>
          <div class="settings-card-arrow">›</div>
        </div>
        <div class="settings-card" data-sub="gesture">
          <div class="settings-card-icon" style="background:rgba(139,92,246,.15)">✋</div>
          <div class="settings-card-body">
            <div class="settings-card-title">${escHtml(t('Gesture Settings'))}</div>
            <div class="settings-card-sub">${escHtml(t('Wake gesture, hold duration, active window'))}</div>
          </div>
          <div class="settings-card-arrow">›</div>
        </div>
        <div class="settings-card" data-sub="camera-cfg">
          <div class="settings-card-icon" style="background:rgba(34,197,94,.15)">📹</div>
          <div class="settings-card-body">
            <div class="settings-card-title">${escHtml(t('Camera Settings'))}</div>
            <div class="settings-card-sub">${escHtml(t('Network camera and stream URL'))}</div>
          </div>
          <div class="settings-card-arrow">›</div>
        </div>
      </div>
    </div>`;

  main.querySelectorAll('.settings-card').forEach(card => {
    card.addEventListener('click', () => navigate('settings', card.dataset.sub));
  });
}

/* ─── HA Settings ───────────────────────────────────────────────────────── */
export async function renderHASettings() {
  const main = document.getElementById('main-content');
  main.innerHTML = `
    <div class="view">
      <button class="back-btn" id="back-btn">${escHtml(t('‹ Settings'))}</button>
      <div class="page-header">
        <div><div class="page-title">${escHtml(t('Home Assistant'))}</div></div>
      </div>
      <div class="loading-row"><div class="spinner"></div> ${escHtml(t('Loading…'))}</div>
    </div>`;
  document.getElementById('back-btn').addEventListener('click', () => navigate('settings'));

  let cfg = { url: '', token: '' };
  try { cfg = await api.get('/ha/config'); } catch {}

  main.innerHTML = `
    <div class="view">
      <button class="back-btn" id="back-btn">${escHtml(t('‹ Settings'))}</button>
      <div class="page-header"><div><div class="page-title">${escHtml(t('Home Assistant'))}</div></div></div>
      <div class="settings-form">
        <div class="field-group">
          <div class="field-label">${escHtml(t('Server URL'))}</div>
          <input class="field-input" id="ha-url" type="url" placeholder="http://homeassistant.local:8123"
            value="${escAttr(cfg.url)}" />
        </div>
        <div class="field-group">
          <div class="field-label">${escHtml(t('Long-Lived Access Token'))}</div>
          <input class="field-input" id="ha-token" type="password"
            placeholder="${escAttr(cfg.token ? t('Token saved — enter new to replace') : t('Paste token here'))}" />
          ${cfg.token ? `<div style="font-size:12px;color:var(--t3);margin-top:4px">${escHtml(t('Current'))}: ${escHtml(cfg.token)}</div>` : ''}
        </div>
        <button class="btn btn-primary" id="ha-save">${escHtml(t('Save Configuration'))}</button>
      </div>
    </div>`;

  document.getElementById('back-btn').addEventListener('click', () => navigate('settings'));
  document.getElementById('ha-save').addEventListener('click', async () => {
    const url = document.getElementById('ha-url').value.trim();
    const token = document.getElementById('ha-token').value.trim();
    if (!url) { toast(t('URL is required'), 'error'); return; }
    const btn = document.getElementById('ha-save');
    btn.disabled = true; btn.textContent = t('Saving…');
    try {
      await api.post('/ha/config', { url, token: token || cfg.token });
      toast(t('Home Assistant configured'), 'success');
      navigate('settings');
    } catch (e) { toast(t('Failed') + ': ' + e.message, 'error'); btn.disabled = false; btn.textContent = t('Save Configuration'); }
  });
}

/* ─── Gesture Settings ──────────────────────────────────────────────────── */
export async function renderGestureSettings() {
  const main = document.getElementById('main-content');
  main.innerHTML = `<div class="view"><button class="back-btn" id="back-btn">${escHtml(t('‹ Settings'))}</button>
    <div class="loading-row"><div class="spinner"></div> ${escHtml(t('Loading…'))}</div></div>`;
  document.getElementById('back-btn').addEventListener('click', () => navigate('settings'));

  let s = { wakeEnabled: false, holdDurationSeconds: 1.0, activeWindowSeconds: 10, selectedGesture: 'Fist' };
  try { const d = await api.get('/gesture-settings'); if (d && typeof d === 'object') Object.assign(s, d); } catch {}

  main.innerHTML = `
    <div class="view">
      <button class="back-btn" id="back-btn">${escHtml(t('‹ Settings'))}</button>
      <div class="page-header"><div><div class="page-title">${escHtml(t('Gesture Settings'))}</div></div></div>
      <div class="settings-form">
        <div class="toggle-row">
          <div class="toggle-info">
            <div class="toggle-title">${escHtml(t('Wake Gesture'))}</div>
            <div class="toggle-sub">${escHtml(t('Require a wake gesture before commands'))}</div>
          </div>
          <div class="toggle ${s.wakeEnabled ? 'on' : ''}" id="wake-toggle"></div>
        </div>

        <div id="wake-options" style="display:${s.wakeEnabled ? 'flex' : 'none'};flex-direction:column;gap:14px">
          <div class="range-wrap">
            <div class="range-header">
              <div class="field-label">${escHtml(t('Hold Duration'))}</div>
              <div class="range-val" id="hold-val">${s.holdDurationSeconds.toFixed(1)}s</div>
            </div>
            <input type="range" id="hold-range" min="0" max="5" step="0.5"
              value="${s.holdDurationSeconds}" />
          </div>

          <div class="range-wrap">
            <div class="range-header">
              <div class="field-label">${escHtml(t('Active Window'))}</div>
              <div class="range-val" id="active-val">${s.activeWindowSeconds}s</div>
            </div>
            <input type="range" id="active-range" min="5" max="20" step="1"
              value="${s.activeWindowSeconds}" />
          </div>

          <div class="field-group">
            <div class="field-label">${escHtml(t('Wake Gesture'))}</div>
            <select class="field-select" id="wake-gesture">
              ${GESTURES.map(g => `<option value="${g.id}" ${g.id === s.selectedGesture ? 'selected' : ''}>${g.icon} ${escHtml(t(g.label))}</option>`).join('')}
            </select>
          </div>
        </div>

        <button class="btn btn-primary" id="gs-save">${escHtml(t('Save Settings'))}</button>
      </div>
    </div>`;

  document.getElementById('back-btn').addEventListener('click', () => navigate('settings'));
  const toggle = document.getElementById('wake-toggle');
  toggle.addEventListener('click', () => {
    toggle.classList.toggle('on');
    document.getElementById('wake-options').style.display = toggle.classList.contains('on') ? 'flex' : 'none';
  });
  document.getElementById('hold-range').addEventListener('input', e =>
    document.getElementById('hold-val').textContent = (+e.target.value).toFixed(1) + 's');
  document.getElementById('active-range').addEventListener('input', e =>
    document.getElementById('active-val').textContent = e.target.value + 's');

  document.getElementById('gs-save').addEventListener('click', async () => {
    const btn = document.getElementById('gs-save');
    btn.disabled = true; btn.textContent = t('Saving…');
    try {
      await api.post('/gesture-settings', {
        wakeEnabled: document.getElementById('wake-toggle').classList.contains('on'),
        holdDurationSeconds: +document.getElementById('hold-range').value,
        activeWindowSeconds: +document.getElementById('active-range').value,
        selectedGesture: document.getElementById('wake-gesture').value,
      });
      toast(t('Gesture settings saved'), 'success');
      navigate('settings');
    } catch (e) { toast(t('Failed') + ': ' + e.message, 'error'); btn.disabled = false; btn.textContent = t('Save Settings'); }
  });
}

/* ─── Camera Settings ───────────────────────────────────────────────────── */
export async function renderCameraSettings() {
  const main = document.getElementById('main-content');
  main.innerHTML = `<div class="view"><button class="back-btn" id="back-btn">${escHtml(t('‹ Settings'))}</button>
    <div class="loading-row"><div class="spinner"></div> ${escHtml(t('Loading…'))}</div></div>`;
  document.getElementById('back-btn').addEventListener('click', () => navigate('settings'));

  let s = { useNetwork: false, streamUrl: '' };
  try { const d = await api.get('/camera-settings'); if (d) Object.assign(s, d); } catch {}

  main.innerHTML = `
    <div class="view">
      <button class="back-btn" id="back-btn">${escHtml(t('‹ Settings'))}</button>
      <div class="page-header"><div><div class="page-title">${escHtml(t('Camera Settings'))}</div></div></div>
      <div class="settings-form">
        <div class="toggle-row">
          <div class="toggle-info">
            <div class="toggle-title">${escHtml(t('Use Network Camera'))}</div>
            <div class="toggle-sub">${escHtml(t('Stream from RTSP/HTTP instead of local camera'))}</div>
          </div>
          <div class="toggle ${s.useNetwork ? 'on' : ''}" id="net-toggle"></div>
        </div>

        <div id="stream-url-wrap" style="display:${s.useNetwork ? 'flex' : 'none'};flex-direction:column;gap:12px">
          <div class="field-group">
            <div class="field-label">${escHtml(t('Stream URL'))}</div>
            <input class="field-input" id="stream-url" type="url"
              placeholder="rtsp://... or http://..."
              value="${escAttr(s.streamUrl)}" />
          </div>
          <button class="btn btn-ghost btn-sm" id="browse-ha-cams">${escHtml(t('📷 Browse HA Cameras'))}</button>
        </div>

        <button class="btn btn-primary" id="cs-save">${escHtml(t('Save Settings'))}</button>
      </div>
    </div>`;

  document.getElementById('back-btn').addEventListener('click', () => navigate('settings'));
  const netToggle = document.getElementById('net-toggle');
  netToggle.addEventListener('click', () => {
    netToggle.classList.toggle('on');
    document.getElementById('stream-url-wrap').style.display = netToggle.classList.contains('on') ? 'flex' : 'none';
  });

  document.getElementById('browse-ha-cams').addEventListener('click', async () => {
    const btn = document.getElementById('browse-ha-cams');
    btn.textContent = t('Loading…'); btn.disabled = true;
    try {
      const { cameras } = await api.get('/ha/cameras');
      showCameraPickerModal(cameras, url => {
        document.getElementById('stream-url').value = url;
      });
    } catch (e) { toast(t('Could not load HA cameras') + ': ' + e.message, 'error'); }
    finally { btn.textContent = t('📷 Browse HA Cameras'); btn.disabled = false; }
  });

  document.getElementById('cs-save').addEventListener('click', async () => {
    const btn = document.getElementById('cs-save');
    btn.disabled = true; btn.textContent = t('Saving…');
    try {
      await api.post('/camera-settings', {
        useNetwork: netToggle.classList.contains('on'),
        streamUrl: document.getElementById('stream-url').value.trim(),
      });
      toast(t('Camera settings saved'), 'success');
      navigate('settings');
    } catch (e) { toast(t('Failed') + ': ' + e.message, 'error'); btn.disabled = false; btn.textContent = t('Save Settings'); }
  });
}

function showCameraPickerModal(cameras, onSelect) {
  showModal(close => {
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.innerHTML = `
      <div class="modal-header">
        <div class="modal-title">${escHtml(t('Select Camera'))}</div>
        <button class="modal-close" id="cam-modal-close">✕</button>
      </div>
      <div class="modal-body">
        ${cameras.length === 0
          ? `<div class="empty-state" style="padding:32px"><div class="empty-title">${escHtml(t('No cameras found'))}</div></div>`
          : `<div class="item-list">${cameras.map(cam => `
              <div class="list-item" data-url="${escAttr(cam.stream_url)}">
                <div class="list-item-icon">📹</div>
                <div>
                  <div class="list-item-title">${escHtml(cam.friendly_name)}</div>
                  <div class="list-item-sub">${escHtml(cam.entity_id)}</div>
                </div>
              </div>`).join('')}
            </div>`}
      </div>`;
    modal.querySelector('#cam-modal-close').addEventListener('click', close);
    modal.querySelectorAll('.list-item').forEach(item => {
      item.addEventListener('click', () => {
        onSelect(item.dataset.url);
        close();
        toast(t('Camera selected'), 'success');
      });
    });
    return modal;
  });
}
