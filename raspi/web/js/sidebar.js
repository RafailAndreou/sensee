export function setSidebarCollapsed(collapsed) {
  document.getElementById('app').classList.toggle('sidebar-collapsed', collapsed);
  try { localStorage.setItem('sensee.sidebarCollapsed', collapsed ? '1' : '0'); } catch {}
}
