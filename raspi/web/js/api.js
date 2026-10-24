async function decodeResponse(response, path) {
  if (!response.ok) {
    let detail = `Request ${path} failed (${response.status})`;
    try { detail = (await response.json()).detail || detail; } catch { /* non-JSON error response */ }
    const error = new Error(typeof detail === 'string' ? detail : JSON.stringify(detail));
    error.status = response.status;
    throw error;
  }
  return response.json();
}

export const api = {
  base: '',   // same origin
  async get(path) {
    const r = await fetch(this.base + path, { credentials: 'same-origin', signal: AbortSignal.timeout(path.startsWith('/ha/pair/') ? 45000 : 10000) });
    return decodeResponse(r, path);
  },
  async post(path, body) {
    const r = await fetch(this.base + path, {
      method: 'POST',
      credentials: 'same-origin',
      signal: AbortSignal.timeout(path.startsWith('/ha/pair/') ? 45000 : 10000),
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    return decodeResponse(r, path);
  },
};
