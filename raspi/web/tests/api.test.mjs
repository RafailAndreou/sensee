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

test('writes serialize and use the revision acknowledged by the previous write', async () => {
  let release;
  let started;
  const firstStarted = new Promise(resolve => started = resolve);
  const gate = new Promise(resolve => release = resolve);
  const requests = [];
  let posts = 0;
  globalThis.fetch = async (path, options) => {
    if (!options.method) return new Response('{}', {headers:{etag:'"initial"'}});
    requests.push(options);
    posts++;
    if (posts === 1) { started(); await gate; }
    return new Response('{}', {headers:{etag: posts === 1 ? '"after-first"' : '"after-second"'}});
  };
  const first = api.post('/engine-settings', {previewFps:5});
  await firstStarted;
  const second = api.post('/engine-settings', {previewFps:10});
  await Promise.resolve();
  assert.equal(requests.length, 1);
  release();
  await Promise.all([first,second]);
  assert.equal(requests[0].headers['If-Match'], '"initial"');
  assert.equal(requests[1].headers['If-Match'], '"after-first"');
  assert.deepEqual(requests.map(r=>JSON.parse(r.body).previewFps), [5,10]);
});

test('conflicts preserve the previous revision until an explicit reload', async () => {
  globalThis.fetch = async () => new Response('{}', {headers:{etag:'"known"'}});
  await api.get('/camera-settings');
  const revisions = [];
  globalThis.fetch = async (_, options) => {
    revisions.push(options.headers['If-Match']);
    return new Response('{"detail":"Review unsaved edits"}', {status:412,headers:{etag:'"changed"'}});
  };
  await assert.rejects(api.post('/camera-settings', {streamUrl:'local draft'}), e=>e.status===412);
  await assert.rejects(api.post('/camera-settings', {streamUrl:'local draft'}), e=>e.status===412);
  assert.deepEqual(revisions, ['"known"','"known"']);
});

test('a background read cannot silently adopt a revision over unsaved edits', async () => {
  let dirty = false;
  globalThis.fetch = async () => new Response('{}', {headers:{etag:'"base"'}});
  await api.get('/voice-settings');
  globalThis.fetch = async () => { dirty = true; return new Response('{}',{headers:{etag:'"remote"'}}); };
  await api.get('/voice-settings', ()=>!dirty);
  globalThis.fetch = async (_, options) => {
    assert.equal(options.headers['If-Match'], '"base"');
    return new Response('{}', {status:200});
  };
  await api.post('/voice-settings', {enabled:true});
});
