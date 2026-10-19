// A route change or newer render must invalidate an outstanding settings load.
export function settingsLoadGuard(main) {
  const loadingView = main.firstElementChild;
  return () => main.firstElementChild === loadingView;
}
