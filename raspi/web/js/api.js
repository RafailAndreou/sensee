async function decodeResponse(response, path) {
  if (!response.ok) {
    let detail = `Request ${path} failed (${response.status})`;
    try { detail = (await response.json()).detail || detail; } catch { /* non-JSON error response */ }
    const error = new Error(typeof detail === 'string' ? detail : JSON.stringify(detail));
    error.status = response.status;
    if (response.status === 401 && path !== '/auth/pair') {
      window.dispatchEvent(new Event('sensee-unpaired'));
    }
    throw error;
  }
  return response.json();
}

const revisions = new Map();
const writes = new Map();

export const api = {
  base: '',   // same origin
  async get(path, rememberRevision = true) {
    const r = await fetch(this.base + path, { credentials: 'same-origin', signal: AbortSignal.timeout(10000) });
    const value = await decodeResponse(r, path);
    if ((typeof rememberRevision === "function" ? rememberRevision() : rememberRevision) && r.headers?.get("etag")) revisions.set(path, r.headers.get("etag"));
    return value;
  },
  post(path, body) {
    const snapshot = JSON.stringify(body);
    const operation = (writes.get(path) || Promise.resolve()).catch(() => {}).then(async () => {
      if (!revisions.has(path) && ['/configuration','/engine-settings','/profiles','/camera-settings','/gesture-settings','/voice-settings','/ironman-params','/ha/config'].includes(path)) await this.get(path);
      const revision = revisions.get(path);
      const r = await fetch(this.base + path, {
        method: 'POST', credentials: 'same-origin', signal: AbortSignal.timeout(10000),
        headers: { 'Content-Type': 'application/json', ...(revision ? {'If-Match': revision} : {}),
          ...(path === '/profiles' && revisions.has('/configuration') ? {'If-Match-Configuration':revisions.get('/configuration')} : {}) },
        body: snapshot,
      });
      const value = await decodeResponse(r, path);
      if (r.headers?.get('etag')) revisions.set(path, r.headers.get('etag'));
      return value;
    });
    writes.set(path, operation);
    return operation;
  },
};
