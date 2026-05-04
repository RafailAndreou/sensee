import { t } from '../i18n.js';
import { escHtml, escAttr } from '../utils.js';

export function renderCamera() {
  const main = document.getElementById('main-content');
  main.innerHTML = `
    <div class="view">
      <div class="page-header">
        <div>
          <div class="page-title">${escHtml(t('Live Camera'))}</div>
          <div class="page-sub">${escHtml(t('Gesture recognition feed'))}</div>
        </div>
        <button class="btn btn-ghost btn-sm" id="cam-refresh">${escHtml(t('↻ Refresh'))}</button>
      </div>
      <div class="camera-container">
        <div class="camera-frame">
          <img id="cam-img" src="/video" alt="${escAttr(t('Live Camera'))}"
            onerror="this.style.display='none';document.getElementById('cam-no-feed').style.display='flex'"
          />
          <div id="cam-no-feed" class="camera-no-feed" style="display:none;flex-direction:column;align-items:center;gap:8px;padding:40px">
            <span style="font-size:40px">📷</span>
            <span>${escHtml(t('No feed available'))}</span>
            <span style="font-size:12px;color:var(--t3)">${escHtml(t('Make sure the gesture engine is running'))}</span>
          </div>
        </div>
      </div>
    </div>`;

  document.getElementById('cam-refresh').addEventListener('click', () => {
    const img = document.getElementById('cam-img');
    img.src = '/video?' + Date.now();
  });
}
