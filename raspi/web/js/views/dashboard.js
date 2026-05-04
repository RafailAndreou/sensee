import { state, normalizeId } from '../state.js';
import { t } from '../i18n.js';
import { DEVICE_META, GESTURES, HANDS } from '../constants.js';
import { escHtml, escAttr } from '../utils.js';
import { showCtxMenu, toast } from '../ui.js';
import { pushConfigs, deleteConfig, swapConfigs } from '../config-sync.js';
import { openAddWizard, openEditWizard } from '../wizard.js';

let lastDashboardHash = '';

export function invalidateDashboardCache() {
  lastDashboardHash = '';
}

export function renderDashboardIfChanged() {
  const hash = JSON.stringify({ lang: state.lang, configs: state.configs.map(c => ({ ...c, isSynced: c.isSynced })) });
  if (hash === lastDashboardHash) return;
  lastDashboardHash = hash;
  renderDashboard();
}

export function renderDashboard() {
  lastDashboardHash = JSON.stringify({ lang: state.lang, configs: state.configs.map(c => ({ ...c, isSynced: c.isSynced })) });

  const main = document.getElementById('main-content');
  const configs = state.configs;
  const countLabel = configs.length === 1 ? t('mapping configured') : t('mappings configured');

  const grid = configs.length === 0
    ? `<div class="empty-state">
        <div class="empty-icon">🖐</div>
        <div class="empty-title">${escHtml(t('No gesture mappings yet'))}</div>
        <div class="empty-sub">${escHtml(t('Tap the + button to connect a device and assign a gesture.'))}</div>
       </div>`
    : `<div class="gesture-grid">${configs.map(renderGestureCard).join('')}</div>`;

  main.innerHTML = `
    <div class="view">
      <div class="page-header">
        <div>
          <div class="page-title">${escHtml(t('Gesture Mappings'))}</div>
          <div class="page-sub">${configs.length} ${escHtml(countLabel)}</div>
        </div>
        ${configs.length > 0 ? `<button class="btn btn-ghost btn-sm" id="sync-btn">${escHtml(t('↻ Sync'))}</button>` : ''}
      </div>
      ${grid}
    </div>
    <button class="fab" id="add-fab" title="${escAttr(t('Add Mapping'))}">+</button>
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
        { icon: '✏️', label: t('Edit'),   action: () => openEditWizard(id) },
        { icon: '🗑', label: t('Delete'), danger: true, action: () => {
          deleteConfig(id);
          toast(t('Mapping deleted'), 'info');
        }},
      ], rect.left, rect.bottom + 4);
    });
  });

  // Card click = edit (suppressed if a drag just happened)
  let dragSourceId = null;
  let currentDropTargetEl = null;
  let suppressClickUntil = 0;

  main.querySelectorAll('.gesture-card').forEach(card => {
    card.addEventListener('click', () => {
      if (Date.now() < suppressClickUntil) return;
      openEditWizard(normalizeId(card.dataset.id));
    });

    card.draggable = true;

    card.addEventListener('dragstart', e => {
      if (e.target.closest('.card-menu-btn')) { e.preventDefault(); return; }
      dragSourceId = normalizeId(card.dataset.id);
      try {
        e.dataTransfer.effectAllowed = 'move';
        e.dataTransfer.setData('text/plain', dragSourceId);
      } catch {}
      card.classList.add('dragging');
    });

    card.addEventListener('dragend', () => {
      card.classList.remove('dragging');
      if (currentDropTargetEl) currentDropTargetEl.classList.remove('drop-target');
      currentDropTargetEl = null;
      dragSourceId = null;
      suppressClickUntil = Date.now() + 250;
    });

    card.addEventListener('dragover', e => {
      if (!dragSourceId) return;
      const targetId = normalizeId(card.dataset.id);
      if (targetId === dragSourceId) return;
      e.preventDefault();
      e.dataTransfer.dropEffect = 'move';
      if (currentDropTargetEl !== card) {
        if (currentDropTargetEl) currentDropTargetEl.classList.remove('drop-target');
        currentDropTargetEl = card;
        card.classList.add('drop-target');
      }
    });

    card.addEventListener('dragleave', e => {
      if (currentDropTargetEl === card && !card.contains(e.relatedTarget)) {
        card.classList.remove('drop-target');
        currentDropTargetEl = null;
      }
    });

    card.addEventListener('drop', e => {
      e.preventDefault();
      const targetId = normalizeId(card.dataset.id);
      card.classList.remove('drop-target');
      currentDropTargetEl = null;
      if (!dragSourceId || targetId === dragSourceId) return;
      const sourceId = dragSourceId;
      dragSourceId = null;
      suppressClickUntil = Date.now() + 250;
      swapConfigs(sourceId, targetId);
    });
  });
}

function renderGestureCard(cfg) {
  const dtype = cfg.sound || 'TV';
  const meta = DEVICE_META[dtype] || DEVICE_META.TV;
  const g = GESTURES.find(g => g.id === cfg.gesture) || GESTURES[0];
  const h = HANDS.find(h => h.id === cfg.hand) || HANDS[0];
  const synced = cfg.isSynced !== false;
  const brandLabel = cfg.connectionType === 'pc'
    ? t('Local PC')
    : cfg.connectionType === 'smart'
      ? (cfg.entityId || dtype)
      : (cfg.brand || dtype);

  return `
    <div class="gesture-card" data-id="${cfg.id}"
      style="--card-accent:${meta.accent}">
      <div class="card-header">
        <div class="card-device-icon" style="background:${meta.bg}">${meta.emoji}</div>
        <button class="card-menu-btn" title="${escAttr(t('Edit'))}">⋯</button>
      </div>
      <div class="card-body">
        <div class="card-action-label">${escHtml(t(cfg.action))}</div>
        <div class="card-brand">${escHtml(brandLabel)}</div>
        <div class="card-badges">
          <span class="badge badge-gesture">${g.icon} ${escHtml(t(g.label))}</span>
          <span class="badge badge-hand">${h.icon} ${escHtml(t(h.label))}</span>
        </div>
      </div>
      <div class="sync-indicator">
        <div class="sync-dot ${synced ? '' : 'unsynced'}"></div>
        <span>${escHtml(synced ? t('Synced') : t('Pending sync'))}</span>
      </div>
    </div>`;
}
