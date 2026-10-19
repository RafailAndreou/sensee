import { t } from './i18n.js';

// Mobile drawer state is separate from the saved desktop collapse preference.
export function initSidebar(root = document, view = root.defaultView) {
  const app = root.getElementById('app');
  const sidebar = root.getElementById('app-sidebar');
  const main = root.getElementById('main-content');
  const openButton = root.getElementById('sidebar-open-btn');
  const closeButton = root.getElementById('sidebar-toggle');
  const backdrop = root.getElementById('sidebar-backdrop');
  const mobile = view.matchMedia('(max-width: 640px)');
  let collapsed = false;
  let drawerOpen = false;
  try { collapsed = view.localStorage.getItem('sensee.sidebarCollapsed') === '1'; } catch {}

  function render() {
    const modal = mobile.matches && drawerOpen;
    const visible = mobile.matches ? drawerOpen : !collapsed;
    app.classList.toggle('sidebar-collapsed', collapsed);
    app.classList.toggle('sidebar-drawer-open', modal);
    backdrop.hidden = !modal;
    sidebar.toggleAttribute('inert', !visible);
    main.toggleAttribute('inert', modal);
    openButton.setAttribute('aria-expanded', String(visible));
    openButton.setAttribute('aria-label', t('Open navigation'));
    closeButton.setAttribute('aria-label', t(mobile.matches ? 'Close navigation' : 'Collapse sidebar'));
    backdrop.setAttribute('aria-label', t('Close navigation'));
    if (modal) {
      sidebar.setAttribute('role', 'dialog');
      sidebar.setAttribute('aria-modal', 'true');
    } else {
      sidebar.removeAttribute('role');
      sidebar.removeAttribute('aria-modal');
    }
  }

  function closeDrawer(focus = openButton) {
    drawerOpen = false;
    render();
    focus.focus();
  }
  function saveCollapsed(value) {
    collapsed = value;
    try { view.localStorage.setItem('sensee.sidebarCollapsed', value ? '1' : '0'); } catch {}
    render();
  }
  function open() {
    if (mobile.matches) {
      drawerOpen = true;
      render();
      closeButton.focus();
    } else {
      saveCollapsed(false);
      closeButton.focus();
    }
  }
  function close() {
    if (mobile.matches) closeDrawer();
    else { saveCollapsed(true); openButton.focus(); }
  }
  function resize() {
    drawerOpen = false;
    render();
    if (sidebar.hasAttribute('inert') && sidebar.contains(root.activeElement)) openButton.focus();
  }
  function keydown(event) {
    if (!mobile.matches || !drawerOpen) return;
    if (event.key === 'Escape') {
      event.preventDefault();
      closeDrawer();
    } else if (event.key === 'Tab') {
      const buttons = [...sidebar.querySelectorAll('button:not([disabled]), a[href], [tabindex="0"]')];
      const first = buttons[0], last = buttons.at(-1);
      if (!sidebar.contains(root.activeElement) || event.shiftKey && root.activeElement === first) {
        event.preventDefault();
        (event.shiftKey ? last : first).focus();
      } else if (!event.shiftKey && root.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    }
  }
  function navigated(event) {
    if (mobile.matches && event.target.closest('[data-view]')) closeDrawer(main);
  }
  function dismiss() { closeDrawer(); }
  openButton.addEventListener('click', open);
  closeButton.addEventListener('click', close);
  backdrop.addEventListener('click', dismiss);
  sidebar.addEventListener('click', navigated);
  root.addEventListener('keydown', keydown);
  mobile.addEventListener('change', resize);
  const languages = sidebar.querySelectorAll('[data-lang]');
  languages.forEach(button => button.addEventListener('click', render));
  render();
  return () => {
    openButton.removeEventListener('click', open);
    closeButton.removeEventListener('click', close);
    backdrop.removeEventListener('click', dismiss);
    sidebar.removeEventListener('click', navigated);
    root.removeEventListener('keydown', keydown);
    mobile.removeEventListener('change', resize);
    languages.forEach(button => button.removeEventListener('click', render));
  };
}
