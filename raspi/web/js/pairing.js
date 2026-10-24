import { t } from './i18n.js';
import { api } from './api.js';
import { escHtml, escAttr } from './utils.js';
import { showModal, toast } from './ui.js';

export async function showPairingWizard(draft, onNoPendingFlows) {
  showModal(close => {
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.innerHTML = `
      <div class="modal-header">
        <div class="modal-title">${escHtml(t('Pair New Device'))}</div>
        <button class="modal-close" id="pair-close">×</button>
      </div><div class="modal-body"></div>`;
    modal.querySelector('#pair-close').addEventListener('click', close);
    const body = modal.querySelector('.modal-body');
    const busy = () => { body.innerHTML = `<div class="loading-row"><div class="spinner"></div> ${escHtml(t('Starting pairing…'))}</div>`; };
    const error = e => { toast(e.message, 'error'); };

    async function renderStep(result) {
      if (result.type === 'create_entry') {
        toast(t('Device paired successfully!'), 'success');
        close();
        onNoPendingFlows?.();
        return;
      }
      if (result.type === 'abort') {
        body.innerHTML = `<div class="banner banner-warn">${escHtml(result.reason || 'Pairing stopped')}</div>`;
        return;
      }
      const fields = result.data_schema || [];
      const supported = result.type === 'form' && fields.every(f =>
        ['string', 'integer', 'float', 'boolean'].includes(f.type) ||
        (f.selector?.text && !f.type));
      if (!supported) {
        body.innerHTML = `<div class="banner banner-warn">${escHtml(t('Complete this setup step in Home Assistant, then refresh devices in Sensee.'))}</div>`;
        return;
      }
      const confirmation = fields.length === 0 && ['zeroconf_confirm', 'confirm'].includes(result.step_id);
      const pinStep = fields.some(f => f.name === 'pin');
      body.innerHTML = `
        ${confirmation ? '<p>Start pairing to request a code on this TV.</p>' : ''}
        ${pinStep ? '<p>Pairing requested. Keep the TV awake and enter the code displayed on that TV.</p>' : ''}
        <p>${escHtml(result.description_placeholders?.name || result.step_id || '')}</p>
        ${Object.entries(result.errors || {}).map(([key, value]) => `<div class="banner banner-error">${escHtml(key)}: ${escHtml(value)}</div>`).join('')}
        <form id="pair-form">
        ${fields.map((f, i) => `<div class="field-group">
          <label class="field-label" for="pair-field-${i}">${escHtml(f.name === 'host' ? 'TV IP address or hostname' : f.name === 'pin' ? 'PIN shown on TV' : f.name)}</label>
          <input class="field-input" id="pair-field-${i}" type="${f.type === 'boolean' ? 'checkbox' : ['integer', 'float'].includes(f.type) ? 'number' : 'text'}"
            ${f.type === 'float' ? 'step="any"' : ''}
            ${f.type === 'boolean' ? (f.default ? 'checked' : '') : `value="${escAttr(f.default ?? f.description?.suggested_value ?? '')}" ${f.required ? 'required' : ''}`} />
        </div>`).join('')}
        <button class="btn btn-primary" type="submit">${escHtml(t(confirmation ? 'Start pairing' : 'Continue'))}</button>
        </form>`;
      body.querySelector('#pair-form').addEventListener('submit', async event => {
        event.preventDefault();
        const input = {};
        fields.forEach((f, i) => {
          const element = body.querySelector(`#pair-field-${i}`);
          if (f.type === 'boolean') input[f.name] = element.checked;
          else if (element.value !== '') input[f.name] = ['integer', 'float'].includes(f.type) ? Number(element.value) : element.value.trim();
        });
        busy();
        try {
          const { result: next } = await api.post('/ha/pair/submit', { flow_id: result.flow_id, user_input: input });
          await renderStep(next);
        } catch (e) { await renderStep(result); error(e); }
      });
    }

    async function start(flow) {
      busy();
      try {
        const { result } = flow?.flow_id
          ? await api.post(`/ha/pair/${encodeURIComponent(flow.flow_id)}/resume`, {})
          : await api.post('/ha/pair/start', { handler: flow?.handler || 'androidtv_remote', ...(flow?.host ? { host: flow.host } : {}) });
        await renderStep(result);
      } catch (e) { error(e); await discover(); }
    }

    async function discover() {
      busy();
      let flows = [];
      let failure = '';
      try { ({ flows } = await api.get('/ha/discovered')); }
      catch (e) { failure = e.message; }
      body.innerHTML = `
        ${failure ? `<div class="banner banner-error">${escHtml(failure)}</div>` : ''}
        ${!flows.length ? `<p>${escHtml(t('No new devices are waiting for pairing.'))}</p>` : ''}
        <p>Select your TV to request its pairing code. Searching alone does not display a code.</p>
        <div class="item-list" id="pair-list"></div>
        <button class="btn btn-primary" id="pair-manual">${escHtml(t('Add Android TV by IP'))}</button>
        <button class="btn btn-ghost" id="pair-refresh">${escHtml(t('Refresh'))}</button>
        <button class="btn btn-ghost" id="use-existing-device">${escHtml(t('Use Existing HA Device'))}</button>`;
      flows.forEach(flow => {
        const button = document.createElement('button');
        button.className = 'list-item';
        const name = flow.context?.title_placeholders?.name || flow.context?.title || flow.handler;
        button.textContent = `${name}${flow.host ? ' (' + flow.host + ')' : ''} ? Pair`;
        button.addEventListener('click', () => start(flow));
        body.querySelector('#pair-list').append(button);
      });
      body.querySelector('#pair-manual').addEventListener('click', () => start(null));
      body.querySelector('#pair-refresh').addEventListener('click', discover);
      body.querySelector('#use-existing-device').addEventListener('click', () => { close(); onNoPendingFlows?.(); });
    }
    discover();
    return modal;
  });
}
