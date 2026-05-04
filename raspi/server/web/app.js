/* ─── Constants ─────────────────────────────────────────────────────────── */
const DEVICE_TYPES = ['TV', 'AC', 'Light', 'Fan', 'PC'];

const DEVICE_META = {
  TV:    { emoji: '📺', bg: 'rgba(59,130,246,0.18)',  accent: '#3b82f6' },
  AC:    { emoji: '❄️', bg: 'rgba(34,197,94,0.18)',   accent: '#22c55e' },
  Light: { emoji: '💡', bg: 'rgba(245,158,11,0.18)',  accent: '#f59e0b' },
  Fan:   { emoji: '🌀', bg: 'rgba(168,85,247,0.18)',  accent: '#a855f7' },
  PC:    { emoji: '💻', bg: 'rgba(99,102,241,0.18)',  accent: '#6366f1' },
};

const GESTURES = [
  { id: 'Index+Thumb',  label: 'Index + Thumb',  icon: '🤏' },
  { id: 'Middle+Thumb', label: 'Middle + Thumb', icon: '✌️' },
  { id: 'Open Palm',    label: 'Open Palm',      icon: '✋' },
  { id: 'Fist',         label: 'Fist',           icon: '✊' },
];

const HANDS = [
  { id: 'Left Hand',  label: 'Left',  icon: '🫲' },
  { id: 'Right Hand', label: 'Right', icon: '🫱' },
  { id: 'Both Hands', label: 'Both',  icon: '👐' },
];

const ACTIONS_BY_TYPE = {
  TV:    ['Turn on', 'Turn off', 'Increase volume', 'Decrease volume'],
  AC:    ['Turn on', 'Turn off', 'Increase volume', 'Decrease volume'],
  Light: ['Turn on', 'Turn off', 'Increase volume', 'Decrease volume'],
  Fan:   ['Turn on', 'Turn off', 'Increase volume', 'Decrease volume'],
  PC:    ['Open Spotify', 'Open YouTube', 'Close Window', 'Open Browser'],
};

const BRANDS_BY_TYPE = {
  TV:    ['Samsung', 'LG', 'Sony', 'TCL', 'Hisense', 'Philips', 'Panasonic', 'Sharp', 'Vizio', 'Toshiba'],
  AC:    ['Daikin', 'Carrier', 'LG', 'Samsung', 'Mitsubishi', 'Panasonic', 'Hitachi', 'Fujitsu', 'Toshiba', 'Gree'],
  Light: ['Philips Hue', 'Wyze', 'LIFX', 'GE', 'Sengled', 'Nanoleaf', 'Govee', 'Kasa'],
  Fan:   ['Dyson', 'Honeywell', 'Lasko', 'Hunter', 'Vornado', 'Minka Aire', 'Hampton Bay'],
  PC:    ['Custom'],
};

/* ─── State ─────────────────────────────────────────────────────────────── */
const state = {
  configs: [],          // [{id,connectionType,entityId,brand,action,gesture,sound,hand,isSynced}]
  view: 'dashboard',    // current top-level view
  subView: null,        // e.g. 'ha-settings', 'gesture-settings', 'camera-settings'
  serverOnline: null,   // true | false | null
  syncInFlight: false,
  pollTimer: null,
  connectTimer: null,
};

// IDs deleted locally but not yet confirmed gone from server — ignore server echoes for these
const pendingDeletedIds = new Set();
let lastDashboardHash = '';

function normalizeId(id) {
  if (id === null || id === undefined) return '';
  const text = String(id).trim();
  if (!text) return '';
  const lowered = text.toLowerCase();
  if (lowered === 'nan' || lowered === 'undefined' || lowered === 'null') return '';
  return text;
}

function sanitizeConfigForSync(config) {
  return {
    id: normalizeId(config.id),
    connectionType: String(config.connectionType ?? 'ir'),
    entityId: String(config.entityId ?? ''),
    brand: String(config.brand ?? ''),
    action: String(config.action ?? ''),
    gesture: String(config.gesture ?? ''),
    sound: String(config.sound ?? 'TV'),
    hand: String(config.hand ?? 'Right Hand'),
  };
}

/* ─── API ───────────────────────────────────────────────────────────────── */
const api = {
  base: '',   // same origin
  async get(path) {
    const r = await fetch(this.base + path);
    if (!r.ok) throw new Error(`GET ${path} → ${r.status}`);
    return r.json();
  },
  async post(path, body) {
    const r = await fetch(this.base + path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!r.ok) throw new Error(`POST ${path} → ${r.status}`);
    return r.json();
  },
};

/* ─── Toast ─────────────────────────────────────────────────────────────── */
function toast(msg, type = 'info') {
  const root = document.getElementById('toast-root');
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  const icons = { success: '✓', error: '✕', info: 'ℹ' };
  el.textContent = (icons[type] || '') + ' ' + msg;
  root.appendChild(el);
  setTimeout(() => {
    el.classList.add('out');
    el.addEventListener('animationend', () => el.remove(), { once: true });
  }, 3000);
}

/* ─── Context Menu ──────────────────────────────────────────────────────── */
function showCtxMenu(items, x, y) {
  closeCtxMenu();
  const root = document.getElementById('ctx-menu-root');
  const menu = document.createElement('div');
  menu.className = 'ctx-menu';
  menu.style.left = x + 'px';
  menu.style.top = y + 'px';
  items.forEach(item => {
    const el = document.createElement('div');
    el.className = 'ctx-item' + (item.danger ? ' danger' : '');
    el.textContent = item.icon + ' ' + item.label;
    el.addEventListener('click', () => { closeCtxMenu(); item.action(); });
    menu.appendChild(el);
  });
  root.appendChild(menu);
  // Close on outside click
  setTimeout(() => document.addEventListener('click', closeCtxMenu, { once: true }), 0);
}
function closeCtxMenu() {
  document.getElementById('ctx-menu-root').innerHTML = '';
}

/* ─── Modal ─────────────────────────────────────────────────────────────── */
const modalStack = [];
function showModal(renderFn) {
  const root = document.getElementById('modal-root');
  const overlay = document.createElement('div');
  overlay.className = 'modal-overlay';
  const content = renderFn(closeModal);
  overlay.appendChild(content);
  overlay.addEventListener('click', e => { if (e.target === overlay) closeModal(); });
  root.appendChild(overlay);
  modalStack.push(overlay);
}
function closeModal() {
  const root = document.getElementById('modal-root');
  const last = root.lastChild;
  if (last) { last.remove(); modalStack.pop(); }
}
function closeAllModals() {
  document.getElementById('modal-root').innerHTML = '';
  modalStack.length = 0;
}

/* ─── Router / Navigation ───────────────────────────────────────────────── */
function navigate(view, subView = null) {
  state.view = view;
  state.subView = subView;
  document.querySelectorAll('.nav-item').forEach(el => {
    el.classList.toggle('active', el.dataset.view === view);
  });
  render();
}

/* ─── Server Status Polling ─────────────────────────────────────────────── */
async function checkServer() {
  const dot = document.getElementById('status-dot');
  const txt = document.getElementById('status-text');
  if (!dot) return;
  dot.className = 'status-dot checking';
  txt.textContent = 'Connecting…';
  try {
    await api.get('/ping');
    const wasOffline = state.serverOnline === false;
    state.serverOnline = true;
    dot.className = 'status-dot connected';
    txt.textContent = 'Connected';
    if (wasOffline) pullConfigs();
  } catch {
    state.serverOnline = false;
    dot.className = 'status-dot disconnected';
    txt.textContent = 'Disconnected';
  }
}

function startPolling() {
  clearInterval(state.pollTimer);
  clearInterval(state.connectTimer);
  checkServer();
  pullConfigs();
  state.connectTimer = setInterval(checkServer, 5000);
  state.pollTimer = setInterval(async () => {
    if (!state.syncInFlight && state.serverOnline) await pullConfigs();
  }, 2000);
}

/* ─── Config Sync ───────────────────────────────────────────────────────── */
async function pullConfigs() {
  if (state.syncInFlight) return;
  state.syncInFlight = true;
  try {
    const data = await api.get('/configuration');
    if (Array.isArray(data)) {
      const serverConfigs = data
        .map(sc => ({ ...sc, id: normalizeId(sc.id) }))
        .filter(sc => sc.id);
      const serverIds = new Set(serverConfigs.map(c => c.id));
      // Remove synced configs no longer on server
      state.configs = state.configs.filter(c => !c.isSynced || serverIds.has(normalizeId(c.id)));
      // Merge server configs, skipping any IDs we just deleted
      serverConfigs.forEach(sc => {
        if (pendingDeletedIds.has(sc.id)) return;
        const local = state.configs.find(c => normalizeId(c.id) === sc.id);
        if (!local) {
          state.configs.push({ ...sc, isSynced: true });
        } else if (local.isSynced) {
          Object.assign(local, sc, { id: sc.id, isSynced: true });
        }
      });
      if (state.view === 'dashboard') renderDashboardIfChanged();
    }
  } catch { /* server offline */ }
  finally { state.syncInFlight = false; }
}

async function pushConfigs(silent = false) {
  try {
    const payload = state.configs
      .map(sanitizeConfigForSync)
      .filter(c => c.id);
    await api.post('/configuration', payload);
    state.configs.forEach(c => c.isSynced = true);
    pendingDeletedIds.clear();
    if (state.view === 'dashboard') renderDashboardIfChanged();
    if (!silent) toast('Mappings synced', 'success');
  } catch (e) {
    toast('Sync failed: ' + e.message, 'error');
  }
}

function nextId() {
  const usedIds = new Set(state.configs.map(c => normalizeId(c.id)).filter(Boolean));
  const numericIds = state.configs
    .map(c => Number.parseInt(normalizeId(c.id), 10))
    .filter(Number.isFinite);
  let next = numericIds.length ? Math.max(...numericIds) + 1 : 1;
  while (usedIds.has(String(next))) next += 1;
  return String(next);
}

function saveConfig(cfg) {
  const normalized = { ...cfg, id: normalizeId(cfg.id) || nextId(), isSynced: false };
  const idx = state.configs.findIndex(c => normalizeId(c.id) === normalized.id);
  if (idx >= 0) state.configs[idx] = normalized;
  else state.configs.push(normalized);
  pushConfigs(true);
}

function deleteConfig(id) {
  const normalizedId = normalizeId(id);
  if (!normalizedId) return;
  pendingDeletedIds.add(normalizedId);
  state.configs = state.configs.filter(c => normalizeId(c.id) !== normalizedId);
  lastDashboardHash = ''; // force re-render immediately
  if (state.view === 'dashboard') renderDashboard();
  pushConfigs(true);
}

function hasConflict(gesture, hand, excludeId = null) {
  const normalizedExcludeId = normalizeId(excludeId);
  return state.configs.some(c => {
    if (normalizeId(c.id) === normalizedExcludeId) return false;
    if (c.gesture !== gesture) return false;
    if (c.hand === hand) return true;
    if (hand === 'Both Hands' && (c.hand === 'Left Hand' || c.hand === 'Right Hand')) return true;
    if ((hand === 'Left Hand' || hand === 'Right Hand') && c.hand === 'Both Hands') return true;
    return false;
  });
}

/* ─── Main Render Dispatcher ────────────────────────────────────────────── */
function render() {
  const main = document.getElementById('main-content');
  if (state.view === 'dashboard') renderDashboard();
  else if (state.view === 'camera') renderCamera();
  else if (state.view === 'settings') {
    if (state.subView === 'ha') renderHASettings();
    else if (state.subView === 'gesture') renderGestureSettings();
    else if (state.subView === 'camera-cfg') renderCameraSettings();
    else renderSettingsHub();
  }
}

/* ─── Dashboard View ────────────────────────────────────────────────────── */
function renderDashboardIfChanged() {
  const hash = JSON.stringify(state.configs.map(c => ({ ...c, isSynced: c.isSynced })));
  if (hash === lastDashboardHash) return;
  lastDashboardHash = hash;
  renderDashboard();
}

function renderDashboard() {
  lastDashboardHash = JSON.stringify(state.configs.map(c => ({ ...c, isSynced: c.isSynced })));

  const main = document.getElementById('main-content');
  const configs = state.configs;

  const grid = configs.length === 0
    ? `<div class="empty-state">
        <div class="empty-icon">🖐</div>
        <div class="empty-title">No gesture mappings yet</div>
        <div class="empty-sub">Tap the + button to connect a device and assign a gesture.</div>
       </div>`
    : `<div class="gesture-grid">${configs.map(renderGestureCard).join('')}</div>`;

  main.innerHTML = `
    <div class="view">
      <div class="page-header">
        <div>
          <div class="page-title">Gesture Mappings</div>
          <div class="page-sub">${configs.length} mapping${configs.length !== 1 ? 's' : ''} configured</div>
        </div>
        ${configs.length > 0 ? `<button class="btn btn-ghost btn-sm" id="sync-btn">↻ Sync</button>` : ''}
      </div>
      ${grid}
    </div>
    <button class="fab" id="add-fab" title="Add mapping">+</button>
  `;

  document.getElementById('add-fab').addEventListener('click', openAddWizard);
  document.getElementById('sync-btn')?.addEventListener('click', () => pushConfigs(false));

  // Card menus
  main.querySelectorAll('.card-menu-btn').forEach(btn => {
    btn.addEventListener('click', e => {
      e.stopPropagation();
      const id = normalizeId(btn.closest('.gesture-card').dataset.id);
      const rect = btn.getBoundingClientRect();
      showCtxMenu([
        { icon: '✏️', label: 'Edit',   action: () => openEditWizard(id) },
        { icon: '🗑', label: 'Delete', danger: true, action: () => {
          deleteConfig(id);
          toast('Mapping deleted', 'info');
        }},
      ], rect.left, rect.bottom + 4);
    });
  });

  // Card click = edit
  main.querySelectorAll('.gesture-card').forEach(card => {
    card.addEventListener('click', () => openEditWizard(normalizeId(card.dataset.id)));
  });
}

function renderGestureCard(cfg) {
  const dtype = cfg.sound || 'TV';
  const meta = DEVICE_META[dtype] || DEVICE_META.TV;
  const g = GESTURES.find(g => g.id === cfg.gesture) || GESTURES[0];
  const h = HANDS.find(h => h.id === cfg.hand) || HANDS[0];
  const synced = cfg.isSynced !== false;
  const brandLabel = cfg.connectionType === 'pc'
    ? 'Local PC'
    : cfg.connectionType === 'smart'
      ? (cfg.entityId || dtype)
      : (cfg.brand || dtype);

  return `
    <div class="gesture-card" data-id="${cfg.id}"
      style="--card-accent:${meta.accent}">
      <div class="card-header">
        <div class="card-device-icon" style="background:${meta.bg}">${meta.emoji}</div>
        <button class="card-menu-btn" title="Options">⋯</button>
      </div>
      <div class="card-body">
        <div class="card-action-label">${escHtml(cfg.action)}</div>
        <div class="card-brand">${escHtml(brandLabel)}</div>
        <div class="card-badges">
          <span class="badge badge-gesture">${g.icon} ${g.label}</span>
          <span class="badge badge-hand">${h.icon} ${h.label}</span>
        </div>
      </div>
      <div class="sync-indicator">
        <div class="sync-dot ${synced ? '' : 'unsynced'}"></div>
        <span>${synced ? 'Synced' : 'Pending sync'}</span>
      </div>
    </div>`;
}

/* ─── Camera View ───────────────────────────────────────────────────────── */
function renderCamera() {
  const main = document.getElementById('main-content');
  main.innerHTML = `
    <div class="view">
      <div class="page-header">
        <div>
          <div class="page-title">Live Camera</div>
          <div class="page-sub">Gesture recognition feed</div>
        </div>
        <button class="btn btn-ghost btn-sm" id="cam-refresh">↻ Refresh</button>
      </div>
      <div class="camera-container">
        <div class="camera-frame">
          <img id="cam-img" src="/video" alt="Camera feed"
            onerror="this.style.display='none';document.getElementById('cam-no-feed').style.display='flex'"
          />
          <div id="cam-no-feed" class="camera-no-feed" style="display:none;flex-direction:column;align-items:center;gap:8px;padding:40px">
            <span style="font-size:40px">📷</span>
            <span>No feed available</span>
            <span style="font-size:12px;color:var(--t3)">Make sure the gesture engine is running</span>
          </div>
        </div>
      </div>
    </div>`;

  document.getElementById('cam-refresh').addEventListener('click', () => {
    const img = document.getElementById('cam-img');
    img.src = '/video?' + Date.now();
  });
}

/* ─── Settings Hub ──────────────────────────────────────────────────────── */
function renderSettingsHub() {
  const main = document.getElementById('main-content');
  main.innerHTML = `
    <div class="view">
      <div class="page-header">
        <div>
          <div class="page-title">Settings</div>
          <div class="page-sub">Configure your Sensee hub</div>
        </div>
      </div>
      <div class="settings-grid">
        <div class="settings-card" data-sub="ha">
          <div class="settings-card-icon" style="background:rgba(79,158,255,.15)">🏠</div>
          <div class="settings-card-body">
            <div class="settings-card-title">Home Assistant</div>
            <div class="settings-card-sub">URL and access token</div>
          </div>
          <div class="settings-card-arrow">›</div>
        </div>
        <div class="settings-card" data-sub="gesture">
          <div class="settings-card-icon" style="background:rgba(139,92,246,.15)">✋</div>
          <div class="settings-card-body">
            <div class="settings-card-title">Gesture Settings</div>
            <div class="settings-card-sub">Wake gesture, hold duration, active window</div>
          </div>
          <div class="settings-card-arrow">›</div>
        </div>
        <div class="settings-card" data-sub="camera-cfg">
          <div class="settings-card-icon" style="background:rgba(34,197,94,.15)">📹</div>
          <div class="settings-card-body">
            <div class="settings-card-title">Camera Settings</div>
            <div class="settings-card-sub">Network camera and stream URL</div>
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
async function renderHASettings() {
  const main = document.getElementById('main-content');
  main.innerHTML = `
    <div class="view">
      <button class="back-btn" id="back-btn">‹ Settings</button>
      <div class="page-header">
        <div><div class="page-title">Home Assistant</div></div>
      </div>
      <div class="loading-row"><div class="spinner"></div> Loading…</div>
    </div>`;
  document.getElementById('back-btn').addEventListener('click', () => navigate('settings'));

  let cfg = { url: '', token: '' };
  try { cfg = await api.get('/ha/config'); } catch {}

  main.innerHTML = `
    <div class="view">
      <button class="back-btn" id="back-btn">‹ Settings</button>
      <div class="page-header"><div><div class="page-title">Home Assistant</div></div></div>
      <div class="settings-form">
        <div class="field-group">
          <div class="field-label">Server URL</div>
          <input class="field-input" id="ha-url" type="url" placeholder="http://homeassistant.local:8123"
            value="${escAttr(cfg.url)}" />
        </div>
        <div class="field-group">
          <div class="field-label">Long-Lived Access Token</div>
          <input class="field-input" id="ha-token" type="password"
            placeholder="${cfg.token ? 'Token saved — enter new to replace' : 'Paste token here'}" />
          ${cfg.token ? `<div style="font-size:12px;color:var(--t3);margin-top:4px">Current: ${escHtml(cfg.token)}</div>` : ''}
        </div>
        <button class="btn btn-primary" id="ha-save">Save Configuration</button>
      </div>
    </div>`;

  document.getElementById('back-btn').addEventListener('click', () => navigate('settings'));
  document.getElementById('ha-save').addEventListener('click', async () => {
    const url = document.getElementById('ha-url').value.trim();
    const token = document.getElementById('ha-token').value.trim();
    if (!url) { toast('URL is required', 'error'); return; }
    const btn = document.getElementById('ha-save');
    btn.disabled = true; btn.textContent = 'Saving…';
    try {
      await api.post('/ha/config', { url, token: token || cfg.token });
      toast('Home Assistant configured', 'success');
      navigate('settings');
    } catch (e) { toast('Failed: ' + e.message, 'error'); btn.disabled = false; btn.textContent = 'Save Configuration'; }
  });
}

/* ─── Gesture Settings ──────────────────────────────────────────────────── */
async function renderGestureSettings() {
  const main = document.getElementById('main-content');
  main.innerHTML = `<div class="view"><button class="back-btn" id="back-btn">‹ Settings</button>
    <div class="loading-row"><div class="spinner"></div> Loading…</div></div>`;
  document.getElementById('back-btn').addEventListener('click', () => navigate('settings'));

  let s = { wakeEnabled: false, holdDurationSeconds: 1.0, activeWindowSeconds: 10, selectedGesture: 'Fist' };
  try { const d = await api.get('/gesture-settings'); if (d && typeof d === 'object') Object.assign(s, d); } catch {}

  main.innerHTML = `
    <div class="view">
      <button class="back-btn" id="back-btn">‹ Settings</button>
      <div class="page-header"><div><div class="page-title">Gesture Settings</div></div></div>
      <div class="settings-form">
        <div class="toggle-row">
          <div class="toggle-info">
            <div class="toggle-title">Wake Gesture</div>
            <div class="toggle-sub">Require a wake gesture before commands</div>
          </div>
          <div class="toggle ${s.wakeEnabled ? 'on' : ''}" id="wake-toggle"></div>
        </div>

        <div id="wake-options" style="display:${s.wakeEnabled ? 'flex' : 'none'};flex-direction:column;gap:14px">
          <div class="range-wrap">
            <div class="range-header">
              <div class="field-label">Hold Duration</div>
              <div class="range-val" id="hold-val">${s.holdDurationSeconds.toFixed(1)}s</div>
            </div>
            <input type="range" id="hold-range" min="0" max="5" step="0.5"
              value="${s.holdDurationSeconds}" />
          </div>

          <div class="range-wrap">
            <div class="range-header">
              <div class="field-label">Active Window</div>
              <div class="range-val" id="active-val">${s.activeWindowSeconds}s</div>
            </div>
            <input type="range" id="active-range" min="5" max="20" step="1"
              value="${s.activeWindowSeconds}" />
          </div>

          <div class="field-group">
            <div class="field-label">Wake Gesture</div>
            <select class="field-select" id="wake-gesture">
              ${GESTURES.map(g => `<option value="${g.id}" ${g.id === s.selectedGesture ? 'selected' : ''}>${g.icon} ${g.label}</option>`).join('')}
            </select>
          </div>
        </div>

        <button class="btn btn-primary" id="gs-save">Save Settings</button>
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
    btn.disabled = true; btn.textContent = 'Saving…';
    try {
      await api.post('/gesture-settings', {
        wakeEnabled: document.getElementById('wake-toggle').classList.contains('on'),
        holdDurationSeconds: +document.getElementById('hold-range').value,
        activeWindowSeconds: +document.getElementById('active-range').value,
        selectedGesture: document.getElementById('wake-gesture').value,
      });
      toast('Gesture settings saved', 'success');
      navigate('settings');
    } catch (e) { toast('Failed: ' + e.message, 'error'); btn.disabled = false; btn.textContent = 'Save Settings'; }
  });
}

/* ─── Camera Settings ───────────────────────────────────────────────────── */
async function renderCameraSettings() {
  const main = document.getElementById('main-content');
  main.innerHTML = `<div class="view"><button class="back-btn" id="back-btn">‹ Settings</button>
    <div class="loading-row"><div class="spinner"></div> Loading…</div></div>`;
  document.getElementById('back-btn').addEventListener('click', () => navigate('settings'));

  let s = { useNetwork: false, streamUrl: '' };
  try { const d = await api.get('/camera-settings'); if (d) Object.assign(s, d); } catch {}

  main.innerHTML = `
    <div class="view">
      <button class="back-btn" id="back-btn">‹ Settings</button>
      <div class="page-header"><div><div class="page-title">Camera Settings</div></div></div>
      <div class="settings-form">
        <div class="toggle-row">
          <div class="toggle-info">
            <div class="toggle-title">Use Network Camera</div>
            <div class="toggle-sub">Stream from RTSP/HTTP instead of local camera</div>
          </div>
          <div class="toggle ${s.useNetwork ? 'on' : ''}" id="net-toggle"></div>
        </div>

        <div id="stream-url-wrap" style="display:${s.useNetwork ? 'flex' : 'none'};flex-direction:column;gap:12px">
          <div class="field-group">
            <div class="field-label">Stream URL</div>
            <input class="field-input" id="stream-url" type="url"
              placeholder="rtsp://... or http://..."
              value="${escAttr(s.streamUrl)}" />
          </div>
          <button class="btn btn-ghost btn-sm" id="browse-ha-cams">📷 Browse HA Cameras</button>
        </div>

        <button class="btn btn-primary" id="cs-save">Save Settings</button>
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
    btn.textContent = 'Loading…'; btn.disabled = true;
    try {
      const { cameras } = await api.get('/ha/cameras');
      showCameraPickerModal(cameras, url => {
        document.getElementById('stream-url').value = url;
      });
    } catch (e) { toast('Could not load HA cameras: ' + e.message, 'error'); }
    finally { btn.textContent = '📷 Browse HA Cameras'; btn.disabled = false; }
  });

  document.getElementById('cs-save').addEventListener('click', async () => {
    const btn = document.getElementById('cs-save');
    btn.disabled = true; btn.textContent = 'Saving…';
    try {
      await api.post('/camera-settings', {
        useNetwork: netToggle.classList.contains('on'),
        streamUrl: document.getElementById('stream-url').value.trim(),
      });
      toast('Camera settings saved', 'success');
      navigate('settings');
    } catch (e) { toast('Failed: ' + e.message, 'error'); btn.disabled = false; btn.textContent = 'Save Settings'; }
  });
}

function showCameraPickerModal(cameras, onSelect) {
  showModal(close => {
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.innerHTML = `
      <div class="modal-header">
        <div class="modal-title">Select Camera</div>
        <button class="modal-close" id="cam-modal-close">✕</button>
      </div>
      <div class="modal-body">
        ${cameras.length === 0
          ? `<div class="empty-state" style="padding:32px"><div class="empty-title">No cameras found</div></div>`
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
        toast('Camera selected', 'success');
      });
    });
    return modal;
  });
}

/* ─── Add / Edit Wizard ─────────────────────────────────────────────────── */
function openAddWizard() {
  const draft = { id: nextId(), connectionType: 'smart', entityId: '', brand: '',
    action: '', gesture: 'Index+Thumb', sound: '', hand: 'Right Hand', isSynced: false };
  showDeviceTypeStep(draft, false);
}

function openEditWizard(id) {
  const normalizedId = normalizeId(id);
  const cfg = state.configs.find(c => normalizeId(c.id) === normalizedId);
  if (!cfg) return;
  const draft = { ...cfg };
  showActionStep(draft, true);
}

/* STEP 1 — Device Type */
function showDeviceTypeStep(draft, editing) {
  showModal(close => {
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.innerHTML = `
      <div class="modal-header">
        <div class="modal-title">Select Device Type</div>
        <button class="modal-close" id="step1-close">✕</button>
      </div>
      <div class="step-indicator">
        <div class="step-dot active">1</div>
        <div class="step-line"></div>
        <div class="step-dot">2</div>
        <div class="step-line"></div>
        <div class="step-dot">3</div>
        <div class="step-line"></div>
        <div class="step-dot">4</div>
      </div>
      <div class="modal-body">
        <div class="select-grid" id="dtype-grid">
          ${DEVICE_TYPES.map(dt => {
            const m = DEVICE_META[dt];
            return `<div class="select-card ${draft.sound === dt ? 'selected' : ''}" data-type="${dt}">
              <div class="select-card-icon">${m.emoji}</div>
              <div class="select-card-label">${dt}</div>
            </div>`;
          }).join('')}
        </div>
      </div>`;
    modal.querySelector('#step1-close').addEventListener('click', close);
    modal.querySelectorAll('.select-card').forEach(card => {
      card.addEventListener('click', () => {
        draft.sound = card.dataset.type;
        draft.action = ACTIONS_BY_TYPE[draft.sound][0];
        close();
        // PC runs directly on the gesture engine host — no HA or brand needed
        if (draft.sound === 'PC') {
          draft.connectionType = 'pc';
          draft.entityId = '';
          draft.brand = 'PC';
          showActionStep(draft, editing);
        } else {
          showConnectionMethodStep(draft, editing);
        }
      });
    });
    return modal;
  });
}

/* STEP 2 — Connection Method */
function showConnectionMethodStep(draft, editing) {
  showModal(close => {
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.innerHTML = `
      <div class="modal-header">
        <div class="modal-title">Connection Method</div>
        <button class="modal-close" id="step2-close">✕</button>
      </div>
      <div class="step-indicator">
        <div class="step-dot done">✓</div>
        <div class="step-line done"></div>
        <div class="step-dot active">2</div>
        <div class="step-line"></div>
        <div class="step-dot">3</div>
        <div class="step-line"></div>
        <div class="step-dot">4</div>
      </div>
      <div class="modal-body">
        <div class="method-grid">
          <div class="method-card" id="method-smart">
            <div class="method-card-icon">🏠</div>
            <div class="method-card-body">
              <div class="method-card-title">Smart Home Device</div>
              <div class="method-card-sub">Connect via Home Assistant</div>
            </div>
            <div class="method-card-arrow">›</div>
          </div>
          <div class="method-card" id="method-ir">
            <div class="method-card-icon">📡</div>
            <div class="method-card-body">
              <div class="method-card-title">Classic / IR Device</div>
              <div class="method-card-sub">Select brand from library</div>
            </div>
            <div class="method-card-arrow">›</div>
          </div>
          ${draft.sound === 'TV' ? `<div class="method-card" id="method-pair">
            <div class="method-card-icon">🔗</div>
            <div class="method-card-body">
              <div class="method-card-title">Pair New TV</div>
              <div class="method-card-sub">Discover and pair via Home Assistant</div>
            </div>
            <div class="method-card-arrow">›</div>
          </div>` : ''}
        </div>
      </div>`;

    modal.querySelector('#step2-close').addEventListener('click', close);
    modal.querySelector('#method-smart').addEventListener('click', () => {
      draft.connectionType = 'smart'; close(); showSmartDeviceStep(draft, editing);
    });
    modal.querySelector('#method-ir').addEventListener('click', () => {
      draft.connectionType = 'ir'; close(); showBrandStep(draft, editing);
    });
    modal.querySelector('#method-pair')?.addEventListener('click', () => {
      close(); showPairingWizard(draft);
    });
    return modal;
  });
}

/* STEP 3a — Smart HA Device List */
async function showSmartDeviceStep(draft, editing) {
  showModal(close => {
    const modal = document.createElement('div');
    modal.className = 'modal modal-wide';
    modal.innerHTML = `
      <div class="modal-header">
        <div class="modal-title">Select HA Device</div>
        <button class="modal-close" id="step3s-close">✕</button>
      </div>
      <div class="step-indicator">
        <div class="step-dot done">✓</div><div class="step-line done"></div>
        <div class="step-dot done">✓</div><div class="step-line done"></div>
        <div class="step-dot active">3</div><div class="step-line"></div>
        <div class="step-dot">4</div>
      </div>
      <div class="modal-body">
        <div class="loading-row"><div class="spinner"></div> Loading devices…</div>
      </div>`;
    modal.querySelector('#step3s-close').addEventListener('click', close);

    api.get('/smart-devices').then(({ devices }) => {
      const filtered = devices.filter(d => d.type?.toLowerCase() === draft.sound?.toLowerCase() || !d.type);
      const body = modal.querySelector('.modal-body');
      if (filtered.length === 0) {
        body.innerHTML = `<div class="empty-state" style="padding:24px">
          <div class="empty-title">No ${draft.sound} devices found</div>
          <div class="empty-sub">Make sure Home Assistant is configured and devices are added.</div>
        </div>`;
        return;
      }
      body.innerHTML = `
        <div class="list-search">
          <span>🔍</span>
          <input id="device-search" placeholder="Search devices…" />
        </div>
        <div class="item-list" id="device-list">
          ${filtered.map(d => `
            <div class="list-item" data-id="${escAttr(d.entity_id)}" data-name="${escAttr(d.friendly_name)}">
              <div class="list-item-icon">${DEVICE_META[draft.sound]?.emoji || '📱'}</div>
              <div>
                <div class="list-item-title">${escHtml(d.friendly_name)}</div>
                <div class="list-item-sub">${escHtml(d.entity_id)}</div>
              </div>
            </div>`).join('')}
        </div>`;

      const listEl = body.querySelector('#device-list');
      body.querySelector('#device-search').addEventListener('input', e => {
        const q = e.target.value.toLowerCase();
        listEl.querySelectorAll('.list-item').forEach(item => {
          item.style.display = item.dataset.name.toLowerCase().includes(q) ? '' : 'none';
        });
      });
      listEl.querySelectorAll('.list-item').forEach(item => {
        item.addEventListener('click', () => {
          draft.entityId = item.dataset.id;
          draft.brand = '';
          close();
          showActionStep(draft, editing);
        });
      });
    }).catch(e => {
      modal.querySelector('.modal-body').innerHTML =
        `<div class="banner banner-error">Failed to load devices: ${escHtml(e.message)}</div>`;
    });

    return modal;
  });
}

/* STEP 3b — Brand Selection */
function showBrandStep(draft, editing) {
  const brands = BRANDS_BY_TYPE[draft.sound] || [];
  showModal(close => {
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.innerHTML = `
      <div class="modal-header">
        <div class="modal-title">Select Brand</div>
        <button class="modal-close" id="step3b-close">✕</button>
      </div>
      <div class="step-indicator">
        <div class="step-dot done">✓</div><div class="step-line done"></div>
        <div class="step-dot done">✓</div><div class="step-line done"></div>
        <div class="step-dot active">3</div><div class="step-line"></div>
        <div class="step-dot">4</div>
      </div>
      <div class="modal-body">
        <div class="list-search">
          <span>🔍</span>
          <input id="brand-search" placeholder="Search brands…" />
        </div>
        <div class="item-list" id="brand-list">
          ${brands.map(b => `
            <div class="list-item ${draft.brand === b ? 'selected' : ''}" data-brand="${escAttr(b)}">
              <div class="list-item-icon">${DEVICE_META[draft.sound]?.emoji || '📦'}</div>
              <div class="list-item-title">${escHtml(b)}</div>
            </div>`).join('')}
        </div>
      </div>`;

    modal.querySelector('#step3b-close').addEventListener('click', close);
    const listEl = modal.querySelector('#brand-list');
    modal.querySelector('#brand-search').addEventListener('input', e => {
      const q = e.target.value.toLowerCase();
      listEl.querySelectorAll('.list-item').forEach(item => {
        item.style.display = item.dataset.brand.toLowerCase().includes(q) ? '' : 'none';
      });
    });
    listEl.querySelectorAll('.list-item').forEach(item => {
      item.addEventListener('click', () => {
        draft.brand = item.dataset.brand;
        draft.entityId = '';
        close();
        showActionStep(draft, editing);
      });
    });
    return modal;
  });
}

/* STEP 4 — Action + Gesture + Hand */
function showActionStep(draft, editing) {
  const actions = ACTIONS_BY_TYPE[draft.sound] || ACTIONS_BY_TYPE.TV;
  if (!draft.action || !actions.includes(draft.action)) draft.action = actions[0];
  if (!draft.gesture) draft.gesture = 'Index+Thumb';
  if (!draft.hand) draft.hand = 'Right Hand';

  showModal(close => {
    const modal = document.createElement('div');
    modal.className = 'modal modal-wide';

    const gestureHTML = GESTURES.map(g => `
      <div class="gesture-option ${draft.gesture === g.id ? 'selected' : ''}" data-gesture="${g.id}">
        <div class="gesture-option-icon">${g.icon}</div>
        <div class="gesture-option-label">${g.label}</div>
      </div>`).join('');

    const handHTML = HANDS.map(h => `
      <div class="hand-option ${draft.hand === h.id ? 'selected' : ''}" data-hand="${h.id}">
        <div class="hand-option-icon">${h.icon}</div>
        <div class="hand-option-label">${h.label}</div>
      </div>`).join('');

    modal.innerHTML = `
      <div class="modal-header">
        <div class="modal-title">${editing ? 'Edit Mapping' : 'Configure Action'}</div>
        <button class="modal-close" id="step4-close">✕</button>
      </div>
      ${editing ? '' : `<div class="step-indicator">
        <div class="step-dot done">✓</div><div class="step-line done"></div>
        <div class="step-dot done">✓</div><div class="step-line done"></div>
        <div class="step-dot done">✓</div><div class="step-line done"></div>
        <div class="step-dot active">4</div>
      </div>`}
      <div class="modal-body">
        <div class="config-section">
          <div class="field-group">
            <div class="config-label">Action</div>
            <select class="field-select" id="action-select">
              ${actions.map(a => `<option value="${a}" ${draft.action === a ? 'selected' : ''}>${a}</option>`).join('')}
            </select>
          </div>

          <div>
            <div class="config-label">Gesture</div>
            <div class="gesture-picker" id="gesture-picker">${gestureHTML}</div>
          </div>

          <div>
            <div class="config-label">Hand</div>
            <div class="hand-picker" id="hand-picker">${handHTML}</div>
          </div>

          <div id="conflict-msg" class="conflict-msg" style="display:none">
            ⚠ This gesture + hand combination is already assigned to another mapping.
          </div>
        </div>
      </div>
      <div class="modal-footer">
        <button class="btn btn-ghost" id="step4-cancel">Cancel</button>
        <button class="btn btn-primary" id="step4-save">
          ${editing ? 'Save Changes' : 'Add Mapping'}
        </button>
      </div>`;

    const checkConflict = () => {
      const conflict = hasConflict(draft.gesture, draft.hand, draft.id);
      modal.querySelector('#conflict-msg').style.display = conflict ? '' : 'none';
      modal.querySelector('#step4-save').disabled = conflict;
    };

    modal.querySelector('#step4-close').addEventListener('click', close);
    modal.querySelector('#step4-cancel').addEventListener('click', close);

    modal.querySelector('#action-select').addEventListener('change', e => { draft.action = e.target.value; });

    modal.querySelector('#gesture-picker').addEventListener('click', e => {
      const card = e.target.closest('.gesture-option');
      if (!card) return;
      modal.querySelectorAll('.gesture-option').forEach(c => c.classList.remove('selected'));
      card.classList.add('selected');
      draft.gesture = card.dataset.gesture;
      checkConflict();
    });

    modal.querySelector('#hand-picker').addEventListener('click', e => {
      const card = e.target.closest('.hand-option');
      if (!card) return;
      modal.querySelectorAll('.hand-option').forEach(c => c.classList.remove('selected'));
      card.classList.add('selected');
      draft.hand = card.dataset.hand;
      checkConflict();
    });

    modal.querySelector('#step4-save').addEventListener('click', () => {
      draft.action = modal.querySelector('#action-select').value;
      saveConfig({ ...draft });
      close();
      navigate('dashboard');
      toast(editing ? 'Mapping updated' : 'Mapping added', 'success');
    });

    checkConflict();
    return modal;
  });
}

/* ─── Pairing Wizard ────────────────────────────────────────────────────── */
async function showPairingWizard(draft) {
  showModal(close => {
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.innerHTML = `
      <div class="modal-header">
        <div class="modal-title">Pair New Device</div>
        <button class="modal-close" id="pair-close">✕</button>
      </div>
      <div class="modal-body">
        <div class="loading-row"><div class="spinner"></div> Discovering devices…</div>
      </div>`;
    modal.querySelector('#pair-close').addEventListener('click', close);

    api.get('/ha/discovered').then(({ flows }) => {
      const body = modal.querySelector('.modal-body');
      if (!flows || flows.length === 0) {
        body.innerHTML = `<div class="banner banner-warn">No devices discovered. Make sure devices are in pairing mode.</div>`;
        return;
      }
      body.innerHTML = `
        <div class="item-list" id="pair-list">
          ${flows.map(f => `
            <div class="list-item" data-handler="${escAttr(f.handler || f)}">
              <div class="list-item-icon">🔗</div>
              <div class="list-item-title">${escHtml(f.handler || f)}</div>
            </div>`).join('')}
        </div>`;

      body.querySelectorAll('.list-item').forEach(item => {
        item.addEventListener('click', async () => {
          body.innerHTML = `<div class="loading-row"><div class="spinner"></div> Starting pairing…</div>`;
          try {
            const { result } = await api.post('/ha/pair/start', { handler: item.dataset.handler });
            body.innerHTML = `
              <div class="field-group">
                <div class="field-label">Enter PIN shown on device</div>
                <input class="field-input" id="pair-pin" type="text" placeholder="e.g. 123456" />
              </div>
              <div class="modal-footer" style="padding:12px 0 0">
                <button class="btn btn-ghost" id="pair-cancel">Cancel</button>
                <button class="btn btn-primary" id="pair-submit">Pair</button>
              </div>`;
            body.querySelector('#pair-cancel').addEventListener('click', close);
            body.querySelector('#pair-submit').addEventListener('click', async () => {
              const pin = body.querySelector('#pair-pin').value.trim();
              try {
                const { result: res } = await api.post('/ha/pair/submit', {
                  flow_id: result.flow_id, user_input: { code: pin }
                });
                if (res.type === 'create_entry') {
                  toast('Device paired successfully!', 'success');
                  close();
                } else {
                  toast('Pairing failed — check PIN', 'error');
                }
              } catch (e) { toast('Error: ' + e.message, 'error'); }
            });
          } catch (e) { body.innerHTML = `<div class="banner banner-error">${escHtml(e.message)}</div>`; }
        });
      });
    }).catch(e => {
      modal.querySelector('.modal-body').innerHTML =
        `<div class="banner banner-error">Failed: ${escHtml(e.message)}</div>`;
    });

    return modal;
  });
}

/* ─── Utilities ─────────────────────────────────────────────────────────── */
function escHtml(str) {
  return String(str ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
function escAttr(str) { return escHtml(str); }

/* ─── Bootstrap ─────────────────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  // Sidebar nav
  document.querySelectorAll('.nav-item[data-view]').forEach(el => {
    el.addEventListener('click', () => navigate(el.dataset.view));
  });

  navigate('dashboard');
  startPolling();
});
