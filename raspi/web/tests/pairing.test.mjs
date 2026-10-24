import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { test } from 'node:test';
import vm from 'node:vm';

class Element {
  nodes = new Map();
  listeners = new Map();
  value = '';
  set innerHTML(value) {
    this.html = value;
    this.nodes.clear();
    if (value.includes('class="modal-body"')) this.nodes.set('.modal-body', new Element());
    for (const match of value.matchAll(/id="([^"]+)"/g)) this.nodes.set('#' + match[1], new Element());
  }
  get innerHTML() { return this.html; }
  querySelector(selector) { return this.nodes.get(selector); }
  addEventListener(type, callback) { this.listeners.set(type, callback); }
  append(element) { (this.children ??= []).push(element); }
  async fire(type) { await this.listeners.get(type)({ preventDefault() {} }); }
}

async function wizard(flows, steps) {
  let modal;
  let closed = false;
  const calls = [];
  const source = (await readFile(new URL('../js/pairing.js', import.meta.url), 'utf8'))
    .replace(/^\uFEFF/, '').replace(/^import .*;\r?\n/gm, '').replace('export async function', 'async function');
  const context = vm.createContext({
    document: { createElement: () => new Element() },
    t: text => text, escHtml: String, escAttr: String,
    toast: () => {},
    showModal: render => { modal = render(() => { closed = true; }); },
    api: {
      get: async path => {
        calls.push({ path });
        return path === '/ha/discovered' ? { flows } : { result: steps.shift() };
      },
      post: async (path, body) => { calls.push({ path, body }); return { result: steps.shift() }; },
    },
  });
  vm.runInContext(source, context);
  await context.showPairingWizard({}, () => {});
  await new Promise(resolve => setImmediate(resolve));
  return { calls, body: modal.querySelector('.modal-body'), isClosed: () => closed };
}

const form = (step, fields, errors = {}) => ({
  type: 'form', flow_id: 'tv-flow', step_id: step,
  data_schema: fields.map(name => ({ name, type: 'string', required: true })), errors,
});

test('manual Android TV setup asks for host then hexadecimal PIN and retries errors', async () => {
  const ui = await wizard([], [form('user', ['host']), form('pair', ['pin']),
    form('pair', ['pin'], { base: 'invalid_auth' }), { type: 'create_entry' }]);
  await ui.body.querySelector('#pair-manual').fire('click');
  assert.match(ui.body.innerHTML, /TV IP address/);
  ui.body.querySelector('#pair-field-0').value = '192.168.1.22';
  await ui.body.querySelector('#pair-form').fire('submit');
  assert.match(ui.body.innerHTML, /PIN shown on TV/);
  ui.body.querySelector('#pair-field-0').value = 'ABC123';
  await ui.body.querySelector('#pair-form').fire('submit');
  assert.match(ui.body.innerHTML, /invalid_auth/);
  ui.body.querySelector('#pair-field-0').value = 'DEF456';
  await ui.body.querySelector('#pair-form').fire('submit');
  assert.equal(ui.isClosed(), true);
  assert.equal(ui.calls[2].body.user_input.host, '192.168.1.22');
  assert.equal(ui.calls[3].body.user_input.pin, 'ABC123');
  assert.equal(ui.calls[4].body.user_input.pin, 'DEF456');
});

test('a discovered TV resumes its existing flow and confirms without creating a new one', async () => {
  const ui = await wizard([{ flow_id: 'discovered-tv', handler: 'androidtv_remote', context: {} }],
    [form('confirm', []), form('pair', ['pin'])]);
  await ui.body.querySelector('#pair-list').children[0].fire('click');
  assert.equal(ui.calls[1].path, '/ha/pair/discovered-tv/resume');
  await ui.body.querySelector('#pair-form').fire('submit');
  assert.equal(Object.keys(ui.calls[2].body.user_input).length, 0);
  assert.equal(ui.calls.some(call => call.path === '/ha/pair/start'), false);
});

test('unsupported integration forms explain how to finish setup', async () => {
  const ui = await wizard([], [{ type: 'external', flow_id: 'tv-flow' }]);
  await ui.body.querySelector('#pair-manual').fire('click');
  assert.match(ui.body.innerHTML, /Complete this setup step in Home Assistant/);
});


test('a TV discovered by Sensee supplies its address automatically', async () => {
  const ui = await wizard([{ handler: 'androidtv_remote', host: '192.168.1.22', context: { title: 'Bedroom TV' } }],
    [form('pair', ['pin'])]);
  await ui.body.querySelector('#pair-list').children[0].fire('click');
  assert.equal(ui.calls[1].path, '/ha/pair/start');
  assert.equal(ui.calls[1].body.host, '192.168.1.22');
  assert.match(ui.body.innerHTML, /PIN shown on TV/);
});


test('searching does not request a PIN until a TV is selected', async () => {
  const ui = await wizard([{ handler: 'androidtv_remote', host: '192.168.1.22', context: { title: 'Bedroom TV' } }], []);
  assert.equal(ui.calls.length, 1);
  assert.match(ui.body.innerHTML, /Searching alone does not display a code/);
  assert.match(ui.body.querySelector('#pair-list').children[0].textContent, /Bedroom TV.*192.168.1.22/);
});
