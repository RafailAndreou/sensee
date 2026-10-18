import assert from 'node:assert/strict';
import { afterEach, test } from 'node:test';
import { api } from '../js/api.js';
import { state, pendingDeletedIds } from '../js/state.js';
import { pullConfigs, pushConfigs, saveConfig } from '../js/config-sync.js';

const original = { get:api.get, post:api.post, document:globalThis.document };
afterEach(() => {
  api.get = original.get; api.post = original.post; globalThis.document = original.document;
  state.configs = []; pendingDeletedIds.clear(); state.syncInFlight = false;
});
function mapping() { return {id:'1', action:'Turn on', gesture:'Thumb+Index', isSynced:true}; }

test('an old poll cannot overwrite an edit acknowledged while it was in flight', async () => {
  globalThis.document = {hidden:false};
  state.configs = [mapping()];
  let release;
  api.get = () => new Promise(resolve => release = resolve);
  api.post = async () => ({});
  const poll = pullConfigs();
  saveConfig({...mapping(), action:'Turn off'});
  await pushConfigs(true);
  release([mapping()]);
  await poll;
  assert.equal(state.configs[0].action, 'Turn off');
  assert.equal(state.configs[0].isSynced, true);
});

test('a save acknowledgement cannot mark a newer unsent edit as synced', async () => {
  globalThis.document = {hidden:false};
  state.configs = [{...mapping(), isSynced:false}];
  let release, started;
  const requestStarted = new Promise(resolve=>started=resolve);
  api.post = () => { started(); return new Promise(resolve=>release=resolve); };
  const save = pushConfigs(true);
  await requestStarted;
  state.configs[0].action = 'Turn off';
  release({});
  await save;
  assert.equal(state.configs[0].action, 'Turn off');
  assert.equal(state.configs[0].isSynced, false);
});

test('background tabs pause mapping polling', async () => {
  globalThis.document = {hidden:true};
  api.get = () => assert.fail('Hidden tab polled the server');
  await pullConfigs();
});
