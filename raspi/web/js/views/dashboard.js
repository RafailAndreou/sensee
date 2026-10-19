import { bindCardReorder } from '../card-reorder.js';
import { state, normalizeId, setDashboardRefreshFn } from '../state.js';
import { t } from '../i18n.js';
import { DEVICE_META, GESTURES, HANDS } from '../constants.js';
import { escHtml, escAttr } from '../utils.js';
import { showCtxMenu, toast } from '../ui.js';
import { pushConfigs, deleteConfig, swapConfigs } from '../config-sync.js';
import { openAddWizard, openEditWizard } from '../wizard.js';

let disposeReorder = () => {};

export function renderDashboardIfChanged() {
  const hash = JSON.stringify({ lang: state.lang, configs: state.configs.map(c => ({ ...c, isSynced: c.isSynced })) });
  if (hash === state.dashboardHash) return;
  state.dashboardHash = hash;
  renderDashboard();
}

export function renderDashboard() {
  state.dashboardHash = JSON.stringify({ lang: state.lang, configs: state.configs.map(c => ({ ...c, isSynced: c.isSynced })) });

  const main = document.getElementById('main-content');
  const focused = main.contains(document.activeElement) ? document.activeElement : null;
  const focusedId = focused?.closest('.gesture-card')?.dataset.id;
  const focusSelector = focused?.matches('.card-move-btn') ? `[data-direction="${focused.dataset.direction}"]`
    : focused?.matches('.card-drag-handle') ? '.card-drag-handle' : '.card-menu-btn';
  const configs = state.configs;
  const countLabel = configs.length === 1 ? t('mapping configured') : t('mappings configured');

  const grid = configs.length === 0
    ? `<div class="empty-state">
        <div class="empty-icon">🖐</div>
        <div class="empty-title">${escHtml(t('No gesture mappings yet'))}</div>
        <div class="empty-sub">${escHtml(t('Tap the + button to connect a device and assign a gesture.'))}</div>
       </div>`
    : `<div class="gesture-grid">${configs.map(renderGestureCard).join('')}</div>`;

  disposeReorder();
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

  disposeReorder = bindCardReorder(main, swapConfigs);

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

  main.querySelectorAll('.card-move-btn').forEach(button => {
    button.addEventListener('click', event => {
      event.stopPropagation();
      const id = normalizeId(button.closest('.gesture-card').dataset.id);
      const index = state.configs.findIndex(config => normalizeId(config.id) === id);
      const other = state.configs[index + Number(button.dataset.direction)];
      if (!other) return;
      const direction = button.dataset.direction;
      swapConfigs(id, other.id);
      // The swap rerenders the grid. Keep keyboard focus on the moved card.
      const moved = [...main.querySelectorAll('.gesture-card')].find(card => card.dataset.id === id);
      const control = moved?.querySelector(`[data-direction="${direction}"]:not(:disabled)`)
        || moved?.querySelector('.card-move-btn:not(:disabled)') || moved?.querySelector('.card-menu-btn');
      control?.focus();
    });
  });
  main.querySelectorAll('.gesture-card').forEach(card => {
    card.addEventListener('click', () => openEditWizard(normalizeId(card.dataset.id)));
  });
  if (focusedId) {
    const card = [...main.querySelectorAll('.gesture-card')].find(card => card.dataset.id === focusedId);
    const control = card?.querySelector(`${focusSelector}:not(:disabled)`)
      || card?.querySelector('.card-move-btn:not(:disabled)') || card?.querySelector('.card-menu-btn');
    control?.focus();
  }
}

function renderGestureCard(cfg, index, configs) {
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
    <div class="gesture-card" data-id="${escAttr(cfg.id)}"
      style="--card-accent:${meta.accent}">
      <div class="card-header">
        <div class="card-device-icon" style="background:${meta.bg}">${meta.emoji}</div>
        <div class="card-controls">
          <button class="card-drag-handle" type="button" aria-label="${escAttr(t('Drag to swap positions'))}" title="${escAttr(t('Drag to swap positions'))}" ${configs.length < 2 ? 'disabled' : ''}>⠿</button>
          <button class="card-menu-btn" type="button" aria-label="${escAttr(t('Edit'))}" title="${escAttr(t('Edit'))}">⋯</button>
        </div>
      </div>
      <div class="card-body">
        <div class="card-action-label">${escHtml(t(cfg.action))}</div>
        <div class="card-brand">${escHtml(brandLabel)}</div>
        <div class="card-badges">
          <span class="badge badge-gesture">${g.icon} ${escHtml(t(g.label))}</span>
          <span class="badge badge-hand">${h.icon} ${escHtml(t(h.label))}</span>
        </div>
      </div>
      <div class="card-order-controls">
        <button class="card-move-btn" type="button" data-direction="-1" ${index === 0 ? 'disabled' : ''}>↑ ${escHtml(t('Move up'))}</button>
        <button class="card-move-btn" type="button" data-direction="1" ${index === configs.length - 1 ? 'disabled' : ''}>↓ ${escHtml(t('Move down'))}</button>
      </div>
      <div class="sync-indicator">
        <div class="sync-dot ${synced ? '' : 'unsynced'}"></div>
        <span>${escHtml(synced ? t('Synced') : t('Pending sync'))}</span>
      </div>
    </div>`;
}

// Register this module's refresh function so config-sync.js can trigger
// dashboard re-renders without importing from this file (breaks circular dep).
setDashboardRefreshFn(renderDashboardIfChanged);
