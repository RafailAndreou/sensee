import { state } from './state.js';

// Renderer is injected by router.js at init time — kept separate so that
// wizard.js can import navigate without pulling in the entire router/view graph.
let _renderFn = null;
export function setRenderer(fn) { _renderFn = fn; }

export function navigate(view, subView = null) {
  state.view = view;
  state.subView = subView;
  document.querySelectorAll('.nav-item').forEach(el => {
    el.classList.toggle('active', el.dataset.view === view);
  });
  _renderFn?.();
}
