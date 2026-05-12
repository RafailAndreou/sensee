import { t } from '../i18n.js';
import { GESTURES } from '../constants.js';
import { api } from '../api.js';
import { escHtml, escAttr } from '../utils.js';
import { showModal, toast } from '../ui.js';
import { navigate } from '../navigate.js';

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
        <div class="settings-card" data-sub="ironman">
          <div class="settings-card-icon" style="background:rgba(79,158,255,.15)">⚡</div>
          <div class="settings-card-body">
            <div class="settings-card-title">${escHtml(t('Ironman Mode'))}</div>
            <div class="settings-card-sub">${escHtml(t('Gesture-controlled cursor & keyboard'))}</div>
          </div>
          <div class="settings-card-arrow">›</div>
        </div>
        <div class="settings-card" data-sub="voice">
          <div class="settings-card-icon" style="background:rgba(34,197,94,.15)">🎤</div>
          <div class="settings-card-body">
            <div class="settings-card-title">${escHtml(t('Voice Control'))}</div>
            <div class="settings-card-sub">${escHtml(t('Whisper-powered voice commands'))}</div>
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

/* ─── Ironman Mode Settings ─────────────────────────────────────────────── */
const _IM_GESTURES = [
  '', 'Open Palm', 'Closed Fist', 'Thumb Up', 'Thumb Down',
  'Victory', 'ILoveYou', 'Pointing Up',
  'Thumb+Index', 'Thumb+Middle', 'Thumb+Ring', 'Thumb+Pinky',
];

const _IM_ACTIONS = [
  ['move_cursor',    'Move Cursor'],
  ['scroll_up',      'Scroll Up'],
  ['scroll_down',    'Scroll Down'],
  ['left_click',     'Left Click'],
  ['right_click',    'Right Click'],
  ['tab_forward',    'Tab Forward'],
  ['tab_backward',   'Tab Backward'],
  ['new_tab',        'New Tab'],
  ['close_tab',      'Close Tab'],
  ['task_view',      'Task View'],
  ['browser_forward','Browser Forward'],
  ['browser_back',   'Browser Back'],
  ['browser_search', 'Browser Search'],
  ['screenshot',     'Screenshot'],
];

export async function renderIronmanSettings() {
  const main = document.getElementById('main-content');
  main.innerHTML = `<div class="view"><button class="back-btn" id="back-btn">${escHtml(t('‹ Settings'))}</button>
    <div class="loading-row"><div class="spinner"></div> ${escHtml(t('Loading…'))}</div></div>`;
  document.getElementById('back-btn').addEventListener('click', () => navigate('settings'));

  let s = { enabled: false, always_track: false, gain: 5000, damp: 50, sensitivity: 3, steps: 10, delay: 0.001, scroll: 10, gesture_map: {} };
  try { const d = await api.get('/ironman-params'); if (d && typeof d === 'object') Object.assign(s, d); } catch {}

  const delayMs = +(s.delay * 1000).toFixed(1);
  const gmap = { ...(s.gesture_map || {}) };
  if (!gmap.scroll_up && gmap.scroll) gmap.scroll_up = gmap.scroll;
  if (!Object.prototype.hasOwnProperty.call(gmap, 'scroll_down')) gmap.scroll_down = '';
  delete gmap.scroll;

  const gestureSelectsHtml = _IM_ACTIONS.map(([key, label]) => {
    const cur = gmap[key] || '';
    const opts = _IM_GESTURES.map(g =>
      `<option value="${escAttr(g)}" ${g === cur ? 'selected' : ''}>${g || '— None —'}</option>`
    ).join('');
    return `
      <div class="im-gesture-row">
        <span class="im-gesture-label">${escHtml(label)}</span>
        <select class="field-select im-gesture-select" data-action="${escAttr(key)}" style="width:auto;padding:4px 8px;font-size:12px">${opts}</select>
      </div>`;
  }).join('');

  main.innerHTML = `
    <div class="view">
      <button class="back-btn" id="back-btn">${escHtml(t('‹ Settings'))}</button>
      <div class="page-header"><div><div class="page-title">⚡ ${escHtml(t('Ironman Mode'))}</div></div></div>
      <div class="settings-form">
        <div class="toggle-row">
          <div class="toggle-info">
            <div class="toggle-title">${escHtml(t('Ironman Mode'))}</div>
            <div class="toggle-sub">${escHtml(t('Gesture-controlled cursor & keyboard'))}</div>
          </div>
          <div class="toggle ${s.enabled ? 'on' : ''}" id="im-toggle"></div>
        </div>

        <div class="ironman-params-panel ${s.enabled ? 'open' : ''}" id="im-panel">
          <div class="im-section-label">${escHtml(t('Motion Parameters'))}</div>
          <div class="toggle-row im-always-track-row">
            <div class="toggle-info">
              <div class="toggle-title">${escHtml(t('Always Track Hand'))}</div>
              <div class="toggle-sub">${escHtml(t('Cursor follows your hand without needing a gesture'))}</div>
            </div>
            <div class="toggle ${s.always_track ? 'on' : ''}" id="im-always-track"></div>
          </div>
          ${_rangeRow('im-gain',        t('Gain'),        t('Cursor speed'),            s.gain,        100, 10000, 100, String(s.gain))}
          ${_rangeRow('im-damp',        t('Damp'),        t('Jitter reduction'),         s.damp,        1,   200,   1,   String(s.damp))}
          ${_rangeRow('im-sensitivity', t('Sensitivity'), t('Movement dead-zone'),       s.sensitivity, 1,   20,    1,   String(s.sensitivity))}
          ${_rangeRow('im-steps',       t('Steps'),       t('Interpolation smoothness'), s.steps,       1,   100,   1,   String(s.steps))}
          ${_rangeRow('im-delay',       t('Delay'),       t('Step interval (ms)'),       delayMs,       0.1, 10,    0.1, delayMs.toFixed(1) + ' ms')}
          ${_rangeRow('im-scroll',      t('Scroll'),      t('Scroll sensitivity'),       s.scroll,      1,   50,    1,   String(s.scroll))}

          <div class="im-section-label" style="margin-top:8px">${escHtml(t('Gesture Assignments'))}</div>
          <div class="im-gesture-grid">${gestureSelectsHtml}</div>
        </div>
      </div>
    </div>`;

  document.getElementById('back-btn').addEventListener('click', () => navigate('settings'));

  let saveTimer = null;
  function scheduleSave() {
    clearTimeout(saveTimer);
    saveTimer = setTimeout(async () => {
      const newGmap = {};
      document.querySelectorAll('.im-gesture-select').forEach(sel => {
        newGmap[sel.dataset.action] = sel.value;
      });
      try {
        await api.post('/ironman-params', {
          enabled:      document.getElementById('im-toggle').classList.contains('on'),
          always_track: document.getElementById('im-always-track').classList.contains('on'),
          gain:        +document.getElementById('im-gain').value,
          damp:        +document.getElementById('im-damp').value,
          sensitivity: +document.getElementById('im-sensitivity').value,
          steps:       +document.getElementById('im-steps').value,
          delay:       +(+document.getElementById('im-delay').value / 1000).toFixed(4),
          scroll:      +document.getElementById('im-scroll').value,
          gesture_map: newGmap,
        });
      } catch {}
    }, 400);
  }

  const toggle = document.getElementById('im-toggle');
  const panel  = document.getElementById('im-panel');
  toggle.addEventListener('click', () => {
    toggle.classList.toggle('on');
    panel.classList.toggle('open', toggle.classList.contains('on'));
    scheduleSave();
  });

  const alwaysTrack = document.getElementById('im-always-track');
  alwaysTrack.addEventListener('click', () => {
    alwaysTrack.classList.toggle('on');
    scheduleSave();
  });

  ['im-gain','im-damp','im-sensitivity','im-steps','im-delay','im-scroll'].forEach(id => {
    const input = document.getElementById(id);
    const valEl = document.getElementById(id + '-val');
    input.addEventListener('input', () => {
      valEl.textContent = id === 'im-delay' ? (+input.value).toFixed(1) + ' ms' : input.value;
      scheduleSave();
    });
  });

  document.querySelectorAll('.im-gesture-select').forEach(sel => {
    sel.addEventListener('change', scheduleSave);
  });
}

function _rangeRow(id, label, hint, value, min, max, step, display) {
  return `
    <div class="range-wrap">
      <div class="range-header">
        <div>
          <span class="field-label">${escHtml(label)}</span>
          <span style="font-size:11px;color:var(--t3);margin-left:6px">${escHtml(hint)}</span>
        </div>
        <div class="range-val" id="${escAttr(id)}-val">${escHtml(display)}</div>
      </div>
      <input type="range" id="${escAttr(id)}" min="${min}" max="${max}" step="${step}" value="${value}" />
    </div>`;
}

/* ─── Voice Control Settings ─────────────────────────────────────────────── */
export async function renderVoiceSettings() {
  const main = document.getElementById('main-content');
  main.innerHTML = `<div class="view"><button class="back-btn" id="back-btn">${escHtml(t('‹ Settings'))}</button>
    <div class="loading-row"><div class="spinner"></div> ${escHtml(t('Loading…'))}</div></div>`;
  document.getElementById('back-btn').addEventListener('click', () => navigate('settings'));

  let s = { enabled: false, model: 'tiny', language: 'en' };
  try { const d = await api.get('/voice-settings'); if (d && typeof d === 'object') Object.assign(s, d); } catch {}

  let vs = { status: 'idle', model: null };
  try { vs = await api.get('/voice-status'); } catch {}

  main.innerHTML = `
    <div class="view">
      <button class="back-btn" id="back-btn">${escHtml(t('‹ Settings'))}</button>
      <div class="page-header"><div><div class="page-title">🎤 ${escHtml(t('Voice Control'))}</div></div></div>
      <div class="settings-form">

        <div class="toggle-row">
          <div class="toggle-info">
            <div class="toggle-title">${escHtml(t('Voice Control'))}</div>
            <div class="toggle-sub">${escHtml(t('Speak to type — Whisper transcribes into any text field'))}</div>
          </div>
          <div class="toggle ${s.enabled ? 'on' : ''}" id="vc-toggle"></div>
        </div>

        <div class="field-group">
          <div class="field-label">${escHtml(t('Whisper Model'))}</div>
          <select class="field-select" id="vc-model">
            <option value="tiny"  ${s.model === 'tiny'  ? 'selected' : ''}>${escHtml(t('Tiny — fastest (~39 MB)'))}</option>
            <option value="base"  ${s.model === 'base'  ? 'selected' : ''}>${escHtml(t('Base (~74 MB)'))}</option>
            <option value="small" ${s.model === 'small' ? 'selected' : ''}>${escHtml(t('Small — best accuracy (~244 MB)'))}</option>
          </select>
          <div id="vc-model-status" class="vc-model-status"></div>
        </div>

        <div class="field-group">
          <div class="field-label">${escHtml(t('Language'))}</div>
          <select class="field-select" id="vc-lang">
            <option value="en"   ${s.language === 'en'   ? 'selected' : ''}>${escHtml(t('English'))}</option>
            <option value="el"   ${s.language === 'el'   ? 'selected' : ''}>${escHtml(t('Greek'))}</option>
            <option value="auto" ${s.language === 'auto' ? 'selected' : ''}>${escHtml(t('Auto-detect'))}</option>
          </select>
        </div>

        <div class="vc-how-it-works">
          <div class="vc-tip">🖱️ ${escHtml(t('Click inside any text field (search bar, address bar, chat…)'))}</div>
          <div class="vc-tip">🎤 ${escHtml(t('Speak — Whisper transcribes after you stop talking'))}</div>
          <div class="vc-tip">⌨️ ${escHtml(t('The transcribed text is pasted at the cursor position'))}</div>
        </div>
      </div>
    </div>`;

  document.getElementById('back-btn').addEventListener('click', () => navigate('settings'));

  // ── Model status badge ─────────────────────────────────────────────────────
  function updateStatusBadge(status, model) {
    const el = document.getElementById('vc-model-status');
    if (!el) return;
    const selected = document.getElementById('vc-model')?.value;
    if (status === 'loading' && model === selected) {
      el.innerHTML = `<span class="vc-status-badge vc-status-loading"><span class="spinner-xs"></span> ${escHtml(t('Downloading'))} ${escHtml(model)}…</span>`;
    } else if (status === 'ready' && model === selected) {
      el.innerHTML = `<span class="vc-status-badge vc-status-ready">✓ ${escHtml(model)} ${escHtml(t('ready'))}</span>`;
    } else {
      el.innerHTML = '';
    }
  }

  updateStatusBadge(vs.status, vs.model);

  // ── Poll while loading ─────────────────────────────────────────────────────
  let pollInterval = null;
  function startPolling() {
    stopPolling();
    pollInterval = setInterval(async () => {
      try {
        const st = await api.get('/voice-status');
        updateStatusBadge(st.status, st.model);
        if (st.status === 'ready' && st.model === document.getElementById('vc-model')?.value) {
          stopPolling();
        }
      } catch {}
    }, 2000);
  }
  function stopPolling() {
    if (pollInterval) { clearInterval(pollInterval); pollInterval = null; }
  }

  if (vs.status === 'loading') startPolling();

  // ── Save ───────────────────────────────────────────────────────────────────
  let saveTimer = null;
  function scheduleSave() {
    clearTimeout(saveTimer);
    saveTimer = setTimeout(async () => {
      try {
        await api.post('/voice-settings', {
          enabled:  document.getElementById('vc-toggle').classList.contains('on'),
          model:    document.getElementById('vc-model').value,
          language: document.getElementById('vc-lang').value,
        });
        // Server triggers preload on POST — start polling
        startPolling();
      } catch {}
    }, 400);
  }

  document.getElementById('vc-toggle').addEventListener('click', () => {
    document.getElementById('vc-toggle').classList.toggle('on');
    scheduleSave();
  });
  document.getElementById('vc-model').addEventListener('change', scheduleSave);
  document.getElementById('vc-lang').addEventListener('change', scheduleSave);
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
