import assert from 'node:assert/strict';
import { test } from 'node:test';
import { readFileSync } from 'node:fs';
import { normalizeGestureName, wakeGestureName, SUPPORTED_GESTURES } from '../js/gestures.js';
import { settingsLoadGuard } from '../js/settings-load.js';
import { hasConflict } from '../js/config-sync.js';
import { state } from '../js/state.js';
const aliases = JSON.parse(readFileSync(new URL('../../../testdata/gesture_aliases.json',import.meta.url)));

test('browser accepts every shared wake alias using the same selector values', () => {
  for (const [input, expected] of Object.entries(aliases)) {
    assert.equal(normalizeGestureName(input), expected);
    assert.equal(wakeGestureName(input), expected);
    assert.ok(SUPPORTED_GESTURES.includes(expected));
  }
});

test('alias spellings cannot create a duplicate gesture mapping', () => {
  state.configs = [{id:'1', gesture:'Closed_Fist', hand:'Right Hand'}];
  try { assert.equal(hasConflict('Fist', 'Right Hand'), true); }
  finally { state.configs = []; }
});

test('a late settings request cannot replace a newer settings form or its edits', async () => {
  const main = {firstElementChild:{form:'loading camera'}};
  const isCurrent = settingsLoadGuard(main);
  let finish;
  const load = new Promise(resolve => finish=resolve).then(() => {
    if (isCurrent()) main.firstElementChild = {form:'old response'};
  });
  const edited = {form:'new camera form', streamUrl:'user edit'};
  main.firstElementChild = edited;
  finish();
  await load;
  assert.equal(main.firstElementChild, edited);
});
