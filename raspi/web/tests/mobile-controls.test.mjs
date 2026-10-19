import assert from 'node:assert/strict';
import { test } from 'node:test';
import { readFileSync } from 'node:fs';
import { JSDOM } from 'jsdom';
import { initSidebar } from '../js/sidebar.js';
import { bindCardReorder } from '../js/card-reorder.js';
const index = readFileSync(new URL('../index.html', import.meta.url), 'utf8');
const css = readFileSync(new URL('../style.css', import.meta.url), 'utf8');

function sidebar(mobile = true, collapsed = false) {
  const dom = new JSDOM(index.replace('</head>', `<style>${css}</style></head>`), {url:'https://sensee.test'});
  const view = dom.window, root = view.document;
  const media = new view.EventTarget();
  media.matches = mobile;
  view.matchMedia = () => media;
  view.localStorage.setItem('sensee.sidebarCollapsed', collapsed ? '1' : '0');
  const dispose = initSidebar(root, view);
  return {dom, view, root, media, dispose, open:root.getElementById('sidebar-open-btn'),
    close:root.getElementById('sidebar-toggle'), panel:root.getElementById('app-sidebar'),
    backdrop:root.getElementById('sidebar-backdrop'), main:root.getElementById('main-content')};
}

test('phone drawer opens over content and backdrop closes it, regardless of desktop preference', () => {
  for (const collapsed of [false, true]) {
    const s = sidebar(true, collapsed);
    try {
      assert.equal(s.panel.hasAttribute('inert'), true);
      assert.equal(s.open.getAttribute('aria-expanded'), 'false');
      s.open.click();
      assert.equal(s.panel.hasAttribute('inert'), false);
      assert.equal(s.panel.getAttribute('aria-modal'), 'true');
      assert.equal(s.main.hasAttribute('inert'), true);
      assert.equal(s.backdrop.hidden, false);
      assert.equal(s.open.getAttribute('aria-expanded'), 'true');
      s.backdrop.click();
      assert.equal(s.panel.hasAttribute('inert'), true);
      assert.equal(s.main.hasAttribute('inert'), false);
      assert.equal(s.backdrop.hidden, true);
      assert.equal(s.root.activeElement, s.open);
      assert.equal(s.view.localStorage.getItem('sensee.sidebarCollapsed'), collapsed ? '1' : '0');
      // Guard the original CSS regression: mobile navigation must not be display:none.
      const rules = [...s.root.styleSheets[0].cssRules].find(rule => rule.conditionText === '(max-width: 640px)').cssRules;
      assert.ok([...rules].some(rule => rule.selectorText.includes('.sidebar') && rule.style.display === 'flex'));
      assert.ok([...rules].some(rule => rule.selectorText.includes('.sidebar-open-btn') && rule.style.display === 'flex'));
    } finally {s.dispose();s.dom.window.close();}
  }
});

test('mobile drawer traps keyboard focus, closes with Escape, and closes after navigation', () => {
  const s = sidebar();
  try {
    s.open.click();
    assert.equal(s.root.activeElement, s.close);
    const buttons = s.panel.querySelectorAll('button');
    s.root.dispatchEvent(new s.view.KeyboardEvent('keydown',{key:'Tab',shiftKey:true,cancelable:true}));
    assert.equal(s.root.activeElement, buttons[buttons.length-1]);
    s.root.dispatchEvent(new s.view.KeyboardEvent('keydown',{key:'Tab',cancelable:true}));
    assert.equal(s.root.activeElement, s.close);
    s.root.dispatchEvent(new s.view.KeyboardEvent('keydown',{key:'Escape',cancelable:true}));
    assert.equal(s.backdrop.hidden, true);
    assert.equal(s.root.activeElement, s.open);
    s.open.click();
    s.panel.querySelector('[data-view="settings"] span').click();
    assert.equal(s.backdrop.hidden, true);
    assert.equal(s.root.activeElement, s.main);
  } finally {s.dispose();s.dom.window.close();}
});

test('crossing the mobile breakpoint restores desktop preference and never leaves content inert', () => {
  const s = sidebar(false, true);
  try {
    s.media.matches = true;s.media.dispatchEvent(new s.view.Event('change'));
    s.open.click();assert.equal(s.main.hasAttribute('inert'), true);
    s.media.matches = false;s.media.dispatchEvent(new s.view.Event('change'));
    assert.equal(s.main.hasAttribute('inert'), false);
    assert.equal(s.backdrop.hidden, true);
    assert.equal(s.panel.hasAttribute('inert'), true);
    s.open.click();assert.equal(s.panel.hasAttribute('inert'), false);
    s.close.click();assert.equal(s.view.localStorage.getItem('sensee.sidebarCollapsed'), '1');
  } finally {s.dispose();s.dom.window.close();}
});

function cards() {
  const dom = new JSDOM('<main><div class="gesture-card" data-id="1"><button class="card-drag-handle">drag</button><span>first</span></div><div class="gesture-card" data-id="2"><button class="card-drag-handle">drag</button></div></main>',{pretendToBeVisual:true});
  const root = dom.window.document, main = root.querySelector('main');
  const cards = [...main.querySelectorAll('.gesture-card')];
  const handle = cards[0].querySelector('button'), captured = new Set(), swaps = [];
  handle.setPointerCapture = id => captured.add(id);
  handle.hasPointerCapture = id => captured.has(id);
  handle.releasePointerCapture = id => captured.delete(id);
  root.elementFromPoint = () => cards[1];
  main.getBoundingClientRect = () => ({top:0,bottom:600});
  let dispose = bindCardReorder(main,(a,b) => swaps.push([a,b]));
  const pointer = (type, properties={}) => {
    const event = new dom.window.Event(type,{bubbles:true,cancelable:true});
    Object.assign(event,{pointerId:7,pointerType:'touch',isPrimary:true,button:0,clientX:20,clientY:100},properties);
    handle.dispatchEvent(event);return event;
  };
  return {dom,root,main,cards,handle,captured,swaps,pointer,dispose};
}

test('touch and pen handles swap cards, release capture, and suppress ghost edits after rerender', () => {
  for (const pointerType of ['touch','pen']) {
    const s = cards();let edits=0;
    try {
      s.cards[0].addEventListener('click',()=>edits++);
      s.pointer('pointerdown',{pointerType});assert.equal(s.captured.has(7),true);
      s.pointer('pointermove',{pointerType,clientY:240});
      assert.equal(s.cards[1].classList.contains('drop-target'),true);
      s.pointer('pointerup',{pointerType,clientY:240});
      assert.deepEqual(s.swaps,[['1','2']]);assert.equal(s.captured.size,0);
      s.dispose();
      s.main.innerHTML='<div class="gesture-card" data-id="2">moved card</div>';
      s.dispose=bindCardReorder(s.main,()=>assert.fail('Unexpected swap'));
      s.main.firstElementChild.addEventListener('click',()=>edits++);
      s.main.firstElementChild.click();assert.equal(edits,0);
    } finally {s.dispose();s.dom.window.close();}
  }
});

test('cancelled, lost, secondary and sub-threshold touch gestures do not reorder', () => {
  for (const end of ['pointercancel','lostpointercapture','pointerup']) {
    const s=cards();
    try {
      s.pointer('pointerdown',{isPrimary:false});assert.equal(s.captured.size,0);
      s.pointer('pointerdown');
      if(end!=='pointerup')s.pointer('pointermove',{clientY:240});
      s.pointer(end);assert.deepEqual(s.swaps,[]);assert.equal(s.captured.size,0);
      assert.equal(s.main.querySelector('.dragging, .drop-target'),null);
    } finally {s.dispose();s.dom.window.close();}
  }
});

test('touching the card body leaves page scrolling and ordinary editing available', () => {
  const s=cards();let edits=0;
  try {
    s.cards[0].addEventListener('click',()=>edits++);
    const event=new s.dom.window.Event('pointerdown',{bubbles:true,cancelable:true});
    Object.assign(event,{pointerType:'touch',pointerId:7,button:0});
    s.cards[0].querySelector('span').dispatchEvent(event);
    assert.equal(event.defaultPrevented,false);assert.equal(s.captured.size,0);
    s.cards[0].click();assert.equal(edits,1);
  } finally {s.dispose();s.dom.window.close();}
});

test('desktop card drag/drop still swaps positions and cancelled drags do not', () => {
  const s=cards();
  const drag=(type,card) => {
    const event=new s.dom.window.Event(type,{bubbles:true,cancelable:true});
    Object.assign(event,{dataTransfer:{setData(){}}});card.dispatchEvent(event);
  };
  try {
    drag('dragstart',s.cards[0]);drag('dragover',s.cards[1]);drag('drop',s.cards[1]);
    assert.deepEqual(s.swaps,[['1','2']]);
    drag('dragstart',s.cards[0]);drag('dragend',s.cards[0]);drag('drop',s.cards[1]);
    assert.equal(s.swaps.length,1);
  } finally {s.dispose();s.dom.window.close();}
});

test('dragging near the edge scrolls the card list and leaving the view cancels the drag', () => {
  const s=cards();let tick;
  s.dom.window.requestAnimationFrame=fn=>{tick=fn;return 1;};
  s.dom.window.cancelAnimationFrame=()=>{};
  try {
    s.pointer('pointerdown');s.pointer('pointermove',{clientY:590});
    tick();assert.equal(s.main.scrollTop,12);
    s.cards[0].remove();tick();
    assert.equal(s.captured.size,0);assert.deepEqual(s.swaps,[]);
  } finally {s.dispose();s.dom.window.close();}
});

test('Move up/down saves the card order, keeps keyboard focus after acknowledgement, and avoids opening Edit', async () => {
  const { renderDashboard } = await import('../js/views/dashboard.js');
  const { state } = await import('../js/state.js');
  const { api } = await import('../js/api.js');
  const dom=new JSDOM(index,{url:'https://sensee.test',pretendToBeVisual:true});
  const originalDocument=globalThis.document, post=api.post;
  const writes=[];
  globalThis.document=dom.window.document;
  api.post=async (_,payload)=>{writes.push(payload.map(c=>c.id));return {};};
  state.view='dashboard';
  state.configs=['1','2','3'].map(id=>({id,gesture:'Victory',hand:'Right Hand',action:'Activate',sound:'Scene',isSynced:true}));
  try {
    renderDashboard();
    let first=document.querySelector('.gesture-card');
    assert.equal(first.querySelector('[data-direction="-1"]').disabled,true);
    const move=first.querySelector('[data-direction="1"]');move.focus();move.click();
    await new Promise(resolve=>setImmediate(resolve));
    assert.deepEqual(state.configs.map(c=>c.id),['2','1','3']);
    assert.deepEqual(writes,[['2','1','3']]);
    assert.equal(document.activeElement.closest('.gesture-card').dataset.id,'1');
    assert.equal(document.querySelector('#modal-root').childElementCount,0);
    const last=document.querySelectorAll('.gesture-card')[2];
    assert.equal(last.querySelector('[data-direction="1"]').disabled,true);
    document.querySelector('[data-id="1"] [data-direction="-1"]').click();
    await new Promise(resolve=>setImmediate(resolve));
    assert.deepEqual(state.configs.map(c=>c.id),['1','2','3']);
    // A failed save retains the moved order and marks it pending for retry.
    api.post=async ()=>{throw Object.assign(new Error('Settings changed'),{status:412});};
    document.querySelector('[data-id="1"] [data-direction="1"]').click();
    await new Promise(resolve=>setImmediate(resolve));
    assert.deepEqual(state.configs.map(c=>c.id),['2','1','3']);
    assert.equal(state.configs.find(c=>c.id==='1').isSynced,false);
    assert.match(document.querySelector('#toast-root').textContent,/Settings changed/);
  } finally {
    state.configs=[];api.post=post;globalThis.document=originalDocument;dom.window.close();
  }
});
