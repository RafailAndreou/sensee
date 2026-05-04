import { t } from './i18n.js';
import { api } from './api.js';
import { escHtml, escAttr } from './utils.js';
import { showModal, toast } from './ui.js';

export async function showPairingWizard(draft) {
  showModal(close => {
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.innerHTML = `
      <div class="modal-header">
        <div class="modal-title">${escHtml(t('Pair New Device'))}</div>
        <button class="modal-close" id="pair-close">✕</button>
      </div>
      <div class="modal-body">
        <div class="loading-row"><div class="spinner"></div> ${escHtml(t('Discovering devices…'))}</div>
      </div>`;
    modal.querySelector('#pair-close').addEventListener('click', close);

    api.get('/ha/discovered').then(({ flows }) => {
      const body = modal.querySelector('.modal-body');
      if (!flows || flows.length === 0) {
        body.innerHTML = `<div class="banner banner-warn">${escHtml(t('No devices discovered. Make sure devices are in pairing mode.'))}</div>`;
        return;
      }
      body.innerHTML = `
        <div class="item-list" id="pair-list">
          ${flows.map(f => `
            <div class="list-item" data-handler="${escAttr(f.handler || f)}">
              <div class="list-item-icon">🔗</div>
              <div class="list-item-title">${escHtml(f.handler || f)}</div>
            </div>`).join('')}
        </div>`;

      body.querySelectorAll('.list-item').forEach(item => {
        item.addEventListener('click', async () => {
          body.innerHTML = `<div class="loading-row"><div class="spinner"></div> ${escHtml(t('Starting pairing…'))}</div>`;
          try {
            const { result } = await api.post('/ha/pair/start', { handler: item.dataset.handler });
            body.innerHTML = `
              <div class="field-group">
                <div class="field-label">${escHtml(t('Enter PIN shown on device'))}</div>
                <input class="field-input" id="pair-pin" type="text" placeholder="e.g. 123456" />
              </div>
              <div class="modal-footer" style="padding:12px 0 0">
                <button class="btn btn-ghost" id="pair-cancel">${escHtml(t('Cancel'))}</button>
                <button class="btn btn-primary" id="pair-submit">${escHtml(t('Pair'))}</button>
              </div>`;
            body.querySelector('#pair-cancel').addEventListener('click', close);
            body.querySelector('#pair-submit').addEventListener('click', async () => {
              const pin = body.querySelector('#pair-pin').value.trim();
              try {
                const { result: res } = await api.post('/ha/pair/submit', {
                  flow_id: result.flow_id, user_input: { code: pin }
                });
                if (res.type === 'create_entry') {
                  toast(t('Device paired successfully!'), 'success');
                  close();
                } else {
                  toast(t('Pairing failed — check PIN'), 'error');
                }
              } catch (e) { toast(t('Error') + ': ' + e.message, 'error'); }
            });
          } catch (e) { body.innerHTML = `<div class="banner banner-error">${escHtml(e.message)}</div>`; }
        });
      });
    }).catch(e => {
      modal.querySelector('.modal-body').innerHTML =
        `<div class="banner banner-error">${escHtml(t('Failed'))}: ${escHtml(e.message)}</div>`;
    });

    return modal;
  });
}
