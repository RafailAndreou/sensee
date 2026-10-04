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

export const api = {
  base: '',   // same origin
  async get(path) {
    const r = await fetch(this.base + path, { credentials: 'same-origin', signal: AbortSignal.timeout(10000) });
    return decodeResponse(r, path);
  },
  async post(path, body) {
    const r = await fetch(this.base + path, {
      method: 'POST',
      credentials: 'same-origin',
      signal: AbortSignal.timeout(10000),
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    return decodeResponse(r, path);
  },
};
