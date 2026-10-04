import { api } from './api.js';

let pairingInFlight = null;

export function ensurePaired() {
  if (pairingInFlight) return pairingInFlight;
  pairingInFlight = pairDashboard().finally(() => { pairingInFlight = null; });
  return pairingInFlight;
}

async function pairDashboard() {
  try {
    await api.get('/auth/status');
    return;
  } catch (error) {
    if (error.status !== 401) throw error;
  }
  await new Promise(resolve => {
    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay';
    overlay.style.cssText = 'position:fixed;inset:0;z-index:10000;background:rgba(0,0,0,.85);display:flex;align-items:center;justify-content:center';
    overlay.innerHTML = `<form class="modal" style="max-width:440px;padding:24px">
      <h2>Pair with Sensee</h2>
      <p>Enter the pairing key shown in the Sensee engine window on your device.</p>
      <input class="field-input" name="key" type="password" required autocomplete="off" placeholder="Pairing key" aria-label="Pairing key">
      <p class="pair-error" role="alert"></p>
      <button class="btn btn-primary" type="submit">Pair</button>
    </form>`;
    document.body.append(overlay);
    const form = overlay.querySelector('form');
    form.querySelector('input').focus();
    form.addEventListener('submit', async event => {
      event.preventDefault();
      const button = form.querySelector('button');
      button.disabled = true;
      try {
        await api.post('/auth/pair', { key: form.elements.key.value.trim() });
        overlay.remove();
        resolve();
      } catch (error) {
        form.querySelector('.pair-error').textContent = error.message;
        button.disabled = false;
      }
    });
  });
}
