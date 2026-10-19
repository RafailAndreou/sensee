// Desktop cards retain native drag/drop. Touch/pen drags start only on the handle,
// leaving the rest of a card available for normal scrolling and editing.
const suppressedClicks = new WeakMap();

export function bindCardReorder(main, swap) {
  const root = main.ownerDocument;
  const view = root.defaultView;
  let sourceId = null, target = null, pointer = null, frame = null;
  const cleanups = [];
  const listen = (node, type, fn) => {
    node.addEventListener(type, fn);
    cleanups.push(() => node.removeEventListener(type, fn));
  };
  function clearTarget() {
    target?.classList.remove('drop-target');
    target = null;
  }
  function highlight(card) {
    if (!card || !main.contains(card) || card.dataset.id === sourceId) card = null;
    if (card === target) return;
    clearTarget();
    target = card;
    target?.classList.add('drop-target');
  }
  function hitTest(x, y) {
    highlight(root.elementFromPoint(x, y)?.closest('.gesture-card'));
  }
  function finish() {
    const previous = pointer;
    if (sourceId) suppressedClicks.set(root, Date.now() + 350);
    pointer = null;
    sourceId = null;
    clearTarget();
    main.querySelectorAll('.dragging').forEach(card => card.classList.remove('dragging'));
    if (frame !== null) view.cancelAnimationFrame(frame);
    frame = null;
    if (previous?.handle.hasPointerCapture?.(previous.id)) previous.handle.releasePointerCapture(previous.id);
  }
  function autoScroll() {
    frame = null;
    if (!pointer?.dragging) return;
    if (!main.contains(pointer.card)) { finish(); return; }
    const rect = main.getBoundingClientRect();
    const edge = 48;
    const step = pointer.y < rect.top + edge ? -12 : pointer.y > rect.bottom - edge ? 12 : 0;
    if (step) {
      main.scrollTop += step;
      hitTest(pointer.x, pointer.y);
    }
    frame = view.requestAnimationFrame(autoScroll);
  }
  for (const card of main.querySelectorAll('.gesture-card')) {
    card.draggable = true;
    listen(card, 'click', event => {
      if (Date.now() < (suppressedClicks.get(root) || 0) || event.target.closest('button')) event.stopImmediatePropagation();
    });
    listen(card, 'dragstart', event => {
      if (pointer || event.target.closest('.card-menu-btn, .card-move-btn')) { event.preventDefault(); return; }
      sourceId = card.dataset.id;
      if (event.dataTransfer) {
        event.dataTransfer.effectAllowed = 'move';
        event.dataTransfer.setData('text/plain', sourceId);
      }
      card.classList.add('dragging');
    });
    listen(card, 'dragover', event => {
      if (!sourceId || pointer || sourceId === card.dataset.id) return;
      event.preventDefault();
      if (event.dataTransfer) event.dataTransfer.dropEffect = 'move';
      highlight(card);
    });
    listen(card, 'dragleave', event => {
      if (!card.contains(event.relatedTarget) && target === card) clearTarget();
    });
    listen(card, 'drop', event => {
      event.preventDefault();
      if (pointer) return;
      const source = sourceId, destination = card.dataset.id;
      finish();
      if (source && source !== destination) swap(source, destination);
    });
    listen(card, 'dragend', finish);
    const handle = card.querySelector('.card-drag-handle');
    if (!handle || handle.disabled) continue;
    listen(handle, 'click', event => event.stopPropagation());
    listen(handle, 'pointerdown', event => {
      if (!['touch', 'pen'].includes(event.pointerType) || event.isPrimary === false || event.button !== 0 || pointer) return;
      event.preventDefault();
      sourceId = card.dataset.id;
      pointer = {id:event.pointerId, card, handle, x:event.clientX, y:event.clientY,
        startX:event.clientX, startY:event.clientY, dragging:false};
      handle.setPointerCapture(event.pointerId);
    });
    listen(handle, 'pointermove', event => {
      if (!pointer || pointer.id !== event.pointerId) return;
      event.preventDefault();
      pointer.x = event.clientX; pointer.y = event.clientY;
      if (!pointer.dragging && Math.hypot(pointer.x-pointer.startX, pointer.y-pointer.startY) < 8) return;
      pointer.dragging = true;
      card.classList.add('dragging');
      hitTest(pointer.x, pointer.y);
      if (frame === null) frame = view.requestAnimationFrame(autoScroll);
    });
    listen(handle, 'pointerup', event => {
      if (!pointer || pointer.id !== event.pointerId) return;
      event.preventDefault();
      if (pointer.dragging) hitTest(event.clientX, event.clientY);
      const source = sourceId, destination = pointer.dragging && target?.dataset.id;
      finish();
      if (destination) swap(source, destination);
    });
    const cancel = event => { if (pointer?.id === event.pointerId) finish(); };
    listen(handle, 'pointercancel', cancel);
    listen(handle, 'lostpointercapture', cancel);
  }
  listen(root, 'keydown', event => { if (event.key === 'Escape' && sourceId) finish(); });
  return () => { finish(); cleanups.forEach(cleanup => cleanup()); };
}
