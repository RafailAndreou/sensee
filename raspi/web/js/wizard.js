import { state, normalizeId } from './state.js';
import { t } from './i18n.js';
import { DEVICE_TYPES, DEVICE_META, GESTURES, HANDS, ACTIONS_BY_TYPE, BRANDS_BY_TYPE } from './constants.js';
import { api } from './api.js';
import { escHtml, escAttr } from './utils.js';
import { showModal, toast } from './ui.js';
import { saveConfig, hasConflict, nextId } from './config-sync.js';
import { navigate } from './navigate.js';
import { showPairingWizard } from './pairing.js';

export function openAddWizard() {
  const draft = { id: nextId(), connectionType: 'smart', entityId: '', brand: '',
    action: '', gesture: 'Index+Thumb', sound: '', hand: 'Right Hand', isSynced: false };
  showDeviceTypeStep(draft, false);
}

export function openEditWizard(id) {
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
        <div class="modal-title">${escHtml(t('Select Device Type'))}</div>
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
              <div class="select-card-label">${escHtml(t(dt))}</div>
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
        <div class="modal-title">${escHtml(t('Connection Method'))}</div>
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
              <div class="method-card-title">${escHtml(t('Smart Home Device'))}</div>
              <div class="method-card-sub">${escHtml(t('Connect via Home Assistant'))}</div>
            </div>
            <div class="method-card-arrow">›</div>
          </div>
          <div class="method-card" id="method-ir">
            <div class="method-card-icon">📡</div>
            <div class="method-card-body">
              <div class="method-card-title">${escHtml(t('Classic / IR Device'))}</div>
              <div class="method-card-sub">${escHtml(t('Select brand from library'))}</div>
            </div>
            <div class="method-card-arrow">›</div>
          </div>
          ${draft.sound === 'TV' ? `<div class="method-card" id="method-pair">
            <div class="method-card-icon">🔗</div>
            <div class="method-card-body">
              <div class="method-card-title">${escHtml(t('Pair New TV'))}</div>
              <div class="method-card-sub">${escHtml(t('Discover and pair via Home Assistant'))}</div>
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
        <div class="modal-title">${escHtml(t('Select HA Device'))}</div>
        <button class="modal-close" id="step3s-close">✕</button>
      </div>
      <div class="step-indicator">
        <div class="step-dot done">✓</div><div class="step-line done"></div>
        <div class="step-dot done">✓</div><div class="step-line done"></div>
        <div class="step-dot active">3</div><div class="step-line"></div>
        <div class="step-dot">4</div>
      </div>
      <div class="modal-body">
        <div class="loading-row"><div class="spinner"></div> ${escHtml(t('Loading devices…'))}</div>
      </div>`;
    modal.querySelector('#step3s-close').addEventListener('click', close);

    api.get('/smart-devices').then(({ devices }) => {
      const filtered = devices.filter(d => d.type?.toLowerCase() === draft.sound?.toLowerCase() || !d.type);
      const body = modal.querySelector('.modal-body');
      if (filtered.length === 0) {
        const noneTitle = (state.lang === 'el')
          ? `Δεν βρέθηκαν συσκευές ${escHtml(t(draft.sound))}`
          : `No ${escHtml(t(draft.sound))} devices found`;
        body.innerHTML = `<div class="empty-state" style="padding:24px">
          <div class="empty-title">${noneTitle}</div>
          <div class="empty-sub">${escHtml(t('Make sure Home Assistant is configured and devices are added.'))}</div>
        </div>`;
        return;
      }
      body.innerHTML = `
        <div class="list-search">
          <span>🔍</span>
          <input id="device-search" placeholder="${escAttr(t('Search devices…'))}" />
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
        `<div class="banner banner-error">${escHtml(t('Failed to load devices'))}: ${escHtml(e.message)}</div>`;
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
        <div class="modal-title">${escHtml(t('Select Brand'))}</div>
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
          <input id="brand-search" placeholder="${escAttr(t('Search brands…'))}" />
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
        <div class="gesture-option-label">${escHtml(t(g.label))}</div>
      </div>`).join('');

    const handHTML = HANDS.map(h => `
      <div class="hand-option ${draft.hand === h.id ? 'selected' : ''}" data-hand="${h.id}">
        <div class="hand-option-icon">${h.icon}</div>
        <div class="hand-option-label">${escHtml(t(h.label))}</div>
      </div>`).join('');

    modal.innerHTML = `
      <div class="modal-header">
        <div class="modal-title">${escHtml(editing ? t('Edit Mapping') : t('Configure Action'))}</div>
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
            <div class="config-label">${escHtml(t('Action'))}</div>
            <select class="field-select" id="action-select">
              ${actions.map(a => `<option value="${a}" ${draft.action === a ? 'selected' : ''}>${escHtml(t(a))}</option>`).join('')}
            </select>
          </div>

          <div>
            <div class="config-label">${escHtml(t('Gesture'))}</div>
            <div class="gesture-picker" id="gesture-picker">${gestureHTML}</div>
          </div>

          <div>
            <div class="config-label">${escHtml(t('Hand'))}</div>
            <div class="hand-picker" id="hand-picker">${handHTML}</div>
          </div>

          <div id="conflict-msg" class="conflict-msg" style="display:none">
            ${escHtml(t('⚠ This gesture + hand combination is already assigned to another mapping.'))}
          </div>
        </div>
      </div>
      <div class="modal-footer">
        <button class="btn btn-ghost" id="step4-cancel">${escHtml(t('Cancel'))}</button>
        <button class="btn btn-primary" id="step4-save">
          ${escHtml(editing ? t('Save Changes') : t('Add Mapping'))}
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
      toast(editing ? t('Mapping updated') : t('Mapping added'), 'success');
    });

    checkConflict();
    return modal;
  });
}
