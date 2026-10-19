import assert from 'node:assert/strict';
import { afterEach, test } from 'node:test';
import { api } from '../js/api.js';
import { state, pendingDeletedIds } from '../js/state.js';
import { pullConfigs, pushConfigs, saveConfig, swapConfigs } from '../js/config-sync.js';

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


test('a clean poll adopts the saved server order from another client', async () => {
  globalThis.document = {hidden:false};
  state.configs = [mapping(), {...mapping(),id:'2'}, {...mapping(),id:'3'}];
  api.get = async () => [{...mapping(),id:'3'}, mapping(), {...mapping(),id:'2'}];
  await pullConfigs();
  assert.deepEqual(state.configs.map(c=>c.id), ['3','1','2']);
});

test('polling preserves an unsaved local order after a failed reorder', async () => {
  globalThis.document = {hidden:false};
  state.configs = [{...mapping(),id:'2',isSynced:false},mapping()];
  api.get = async () => [mapping(), {...mapping(),id:'2'}];
  await pullConfigs();
  assert.deepEqual(state.configs.map(c=>c.id), ['2','1']);
  assert.equal(state.configs[0].isSynced,false);
});

test('an older save acknowledgement cannot mark a newer unsent reorder as synced', async () => {
  globalThis.document = {hidden:false};
  state.configs = [mapping(), {...mapping(),id:'2'}];
  let started, release, finishNew;
  const newResponse = new Promise(resolve=>finishNew=resolve);
  const firstStarted = new Promise(resolve=>started=resolve);
  const sent=[];
  api.post = (_,payload) => {
    sent.push(payload.map(c=>c.id));
    if(sent.length===1){started();return new Promise(resolve=>release=resolve);}
    return newResponse;
  };
  const oldSave=pushConfigs(true);
  await firstStarted;
  const newSave=swapConfigs('1','2');
  release({});
  await oldSave;
  assert.equal(state.configs.every(c=>c.isSynced),false);
  finishNew({});
  await newSave;
  assert.deepEqual(sent[0],['1','2']);
  assert.deepEqual(sent.at(-1),['2','1']);
});
