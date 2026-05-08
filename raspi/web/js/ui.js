/* ─── Toast ─────────────────────────────────────────────────────────────── */
export function toast(msg, type = 'info') {
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
export function showCtxMenu(items, x, y) {
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

export function closeCtxMenu() {
  document.getElementById('ctx-menu-root').innerHTML = '';
}

/* ─── Modal ─────────────────────────────────────────────────────────────── */
const modalStack = [];

export function showModal(renderFn) {
  const root = document.getElementById('modal-root');
  const overlay = document.createElement('div');
  overlay.className = 'modal-overlay';
  const content = renderFn(closeModal);
  overlay.appendChild(content);
  overlay.addEventListener('click', e => { if (e.target === overlay) closeModal(); });
  root.appendChild(overlay);
  modalStack.push(overlay);
}

export function closeModal() {
  const root = document.getElementById('modal-root');
  const last = root.lastChild;
  if (last) { last.remove(); modalStack.pop(); }
}

export function closeAllModals() {
  document.getElementById('modal-root').innerHTML = '';
  modalStack.length = 0;
}
