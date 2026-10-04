import assert from 'node:assert/strict';
import { afterEach, test } from 'node:test';
import { api } from '../js/api.js';

const originalFetch = globalThis.fetch;
const originalWindow = globalThis.window;
afterEach(() => {
  globalThis.fetch = originalFetch;
  globalThis.window = originalWindow;
});

test('protected requests send the browser cookie and have a deadline', async () => {
  globalThis.fetch = async (path, options) => {
    assert.equal(path, '/configuration');
    assert.equal(options.credentials, 'same-origin');
    assert.ok(options.signal instanceof AbortSignal);
    return new Response('[]', { status: 200 });
  };
  assert.deepEqual(await api.get('/configuration'), []);
});

test('an expired pairing signals the UI and retains the HTTP status', async () => {
  const events = [];
  globalThis.window = { dispatchEvent: event => events.push(event.type) };
  globalThis.fetch = async () => new Response('{"detail":"Pair first"}', { status: 401 });
  await assert.rejects(api.get('/configuration'), error => error.status === 401 && error.message === 'Pair first');
  assert.deepEqual(events, ['sensee-unpaired']);
});

test('an incorrect pairing key does not recursively open another pairing UI', async () => {
  globalThis.window = { dispatchEvent: () => assert.fail('Unexpected pairing event') };
  globalThis.fetch = async () => new Response('{"detail":"Incorrect pairing key"}', { status: 401 });
  await assert.rejects(api.post('/auth/pair', { key: 'incorrect' }), /Incorrect pairing key/);
});

test('validation errors retain the server explanation', async () => {
  globalThis.fetch = async () => new Response('{"detail":"Duplicate gesture+hand mapping"}', { status: 400 });
  await assert.rejects(api.post('/configuration', []), /Duplicate gesture\+hand mapping/);
});
