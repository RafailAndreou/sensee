export const state = {
  configs: [],          // [{id,connectionType,entityId,brand,action,gesture,sound,hand,isSynced}]
  view: 'dashboard',    // current top-level view
  subView: null,        // e.g. 'ha-settings', 'gesture-settings', 'camera-settings'
  serverOnline: null,   // true | false | null
  syncInFlight: false,
  pollTimer: null,
  connectTimer: null,
  lang: (typeof localStorage !== 'undefined' && localStorage.getItem('sensee.lang')) || 'en',
  dashboardHash: '',    // cache key for renderDashboardIfChanged
};

// Dashboard refresh callback — set by views/dashboard.js at module init to
// avoid a circular dep between config-sync.js and views/dashboard.js.
let _dashboardRefreshFn = null;
export function setDashboardRefreshFn(fn) { _dashboardRefreshFn = fn; }
export function triggerDashboardRefresh() { _dashboardRefreshFn?.(); }
export function invalidateDashboardCache() { state.dashboardHash = ''; }

// IDs deleted locally but not yet confirmed gone from server — ignore server echoes for these
export const pendingDeletedIds = new Set();

export function normalizeId(id) {
  if (id === null || id === undefined) return '';
  const text = String(id).trim();
  if (!text) return '';
  const lowered = text.toLowerCase();
  if (lowered === 'nan' || lowered === 'undefined' || lowered === 'null') return '';
  return text;
}

export function sanitizeConfigForSync(config) {
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
