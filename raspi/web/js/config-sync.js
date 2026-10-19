import { normalizeGestureName } from './gestures.js';
import { api } from './api.js';
import { state, pendingDeletedIds, normalizeId, sanitizeConfigForSync,
         invalidateDashboardCache, triggerDashboardRefresh } from './state.js';
import { t } from './i18n.js';
import { toast } from './ui.js';

let mappingVersion = 0;
let pushesPending = 0;

export async function pullConfigs() {
  if (state.syncInFlight || pushesPending || document.hidden) return;
  state.syncInFlight = true;
  const version = mappingVersion;
  try {
    const data = await api.get('/configuration', () => version === mappingVersion && !pushesPending && !state.configs.some(c => !c.isSynced) && !pendingDeletedIds.size);
    if (version !== mappingVersion || pushesPending) return;
    if (Array.isArray(data)) {
      const serverConfigs = data
        .map(sc => ({ ...sc, id: normalizeId(sc.id) }))
        .filter(sc => sc.id);
      const serverIds = new Set(serverConfigs.map(c => c.id));
      const hasLocalEdits = state.configs.some(c => !c.isSynced) || pendingDeletedIds.size;
      if (!hasLocalEdits) {
        // Adopt the server's saved order, including swaps made on another client.
        state.configs = serverConfigs.map(c => ({...c, isSynced:true}));
        if (state.view === 'dashboard') triggerDashboardRefresh();
        return;
      }
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
      if (state.view === 'dashboard') triggerDashboardRefresh();
    }
  } catch { /* server offline */ }
  finally { state.syncInFlight = false; }
}

let pushTail = Promise.resolve();
export function pushConfigs(silent = false) {
  mappingVersion++;
  pushesPending++;
  pushTail = pushTail.catch(() => {}).then(() => performPush(silent)).finally(()=>{ pushesPending--; mappingVersion++; });
  return pushTail;
}

async function performPush(silent) {
  try {
    const payload = state.configs
      .map(sanitizeConfigForSync)
      .filter(c => c.id);
    const deleted = new Set(pendingDeletedIds);
    await api.post('/configuration', payload);
    const sameOrder = payload.length === state.configs.length &&
      payload.every((c, index) => c.id === normalizeId(state.configs[index].id));
    state.configs.forEach(c => {
      const sent = payload.find(p => p.id === normalizeId(c.id));
      if (sameOrder && sent && JSON.stringify(sanitizeConfigForSync(c)) === JSON.stringify(sent)) c.isSynced = true;
    });
    deleted.forEach(id => pendingDeletedIds.delete(id));
    if (state.view === 'dashboard') triggerDashboardRefresh();
    if (!silent) toast(t('Mappings synced'), 'success');
  } catch (e) {
    toast(t('Sync failed') + ': ' + e.message, 'error');
  }
}

export function nextId() {
  const usedIds = new Set(state.configs.map(c => normalizeId(c.id)).filter(Boolean));
  const numericIds = state.configs
    .map(c => Number.parseInt(normalizeId(c.id), 10))
    .filter(Number.isFinite);
  let next = numericIds.length ? Math.max(...numericIds) + 1 : 1;
  while (usedIds.has(String(next))) next += 1;
  return String(next);
}

export function saveConfig(cfg) {
  const normalized = { ...cfg, id: normalizeId(cfg.id) || nextId(), isSynced: false };
  const idx = state.configs.findIndex(c => normalizeId(c.id) === normalized.id);
  if (idx >= 0) state.configs[idx] = normalized;
  else state.configs.push(normalized);
  pushConfigs(true);
}

export function deleteConfig(id) {
  const normalizedId = normalizeId(id);
  if (!normalizedId) return;
  pendingDeletedIds.add(normalizedId);
  state.configs = state.configs.filter(c => normalizeId(c.id) !== normalizedId);
  invalidateDashboardCache();
  if (state.view === 'dashboard') triggerDashboardRefresh();
  pushConfigs(true);
}

export function swapConfigs(idA, idB) {
  const a = normalizeId(idA);
  const b = normalizeId(idB);
  if (!a || !b || a === b) return;
  const i = state.configs.findIndex(c => normalizeId(c.id) === a);
  const j = state.configs.findIndex(c => normalizeId(c.id) === b);
  if (i < 0 || j < 0 || i === j) return;
  [state.configs[i], state.configs[j]] = [state.configs[j], state.configs[i]];
  state.configs[i].isSynced = false;
  state.configs[j].isSynced = false;
  invalidateDashboardCache();
  if (state.view === 'dashboard') triggerDashboardRefresh();
  return pushConfigs(true);
}

export function hasConflict(gesture, hand, excludeId = null) {
  const normalizedExcludeId = normalizeId(excludeId);
  return state.configs.some(c => {
    if (normalizeId(c.id) === normalizedExcludeId) return false;
    if (normalizeGestureName(c.gesture) !== normalizeGestureName(gesture)) return false;
    if (c.hand === hand) return true;
    if (hand === 'Both Hands' && (c.hand === 'Left Hand' || c.hand === 'Right Hand')) return true;
    if ((hand === 'Left Hand' || hand === 'Right Hand') && c.hand === 'Both Hands') return true;
    return false;
  });
}
