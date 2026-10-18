import { api } from '../api.js';
import { escHtml, escAttr } from '../utils.js';
import { navigate } from '../navigate.js';
import { toast } from '../ui.js';
import { state, pendingDeletedIds, sanitizeConfigForSync } from '../state.js';
import { pushConfigs, pullConfigs } from '../config-sync.js';

export async function renderEngineTools() {
  const main = document.getElementById('main-content');
  main.innerHTML = '<div class="view">Loading Engine tools…</div>';
  try {
    const [settings, tools, profiles] = await Promise.all([
      api.get('/engine-settings'), api.get('/engine-tools'), api.get('/profiles'),
    ]);
    await api.get('/configuration', ()=>!state.configs.some(c=>!c.isSynced) && !pendingDeletedIds.size);
    if (!main.textContent.includes('Loading Engine tools')) return;
    main.innerHTML = `<div class="view"><button id="engine-back" class="back-btn">‹ Settings</button>
      <h1>Engine tools</h1><div class="settings-form">
      <h2>Performance</h2>${Object.entries(settings).filter(([,v]) => typeof v === 'number').map(([key,value]) =>
        `<label>${escHtml(key)}<input class="field-input" type="number" data-engine="${escAttr(key)}" value="${value}"></label>`).join('')}
      <h2>Hand contact calibration</h2>
      <p>Keep one hand visible. Touch thumb to index and collect 30 observations, then separate them and collect 30 more. Apply the result to all four contacts.</p>
      <label><input id="cal-enabled" type="checkbox" ${settings.calibration.enabled ? 'checked' : ''}>Use saved calibration</label>
      <label>Contact ratio<input id="cal-ratio" class="field-input" type="number" step=".01" value="${settings.calibration.contactRatio}"></label>
      <label>Depth ratio<input id="cal-depth" class="field-input" type="number" step=".01" value="${settings.calibration.depthRatio}"></label>
      <button data-phase="contact" class="btn">1. Sample touching</button><button data-phase="open" class="btn">2. Sample separated</button>
      <button id="cal-apply" class="btn">Apply sampled calibration</button><button id="engine-save" class="btn btn-primary">Save engine settings</button>
      <h2>Session test mode</h2><p>Displays intended actions and blocks device, cursor, keyboard and voice output. Resets on engine restart.</p>
      <label><input id="engine-test" type="checkbox" ${tools.testMode ? 'checked' : ''}>Test mode</label>
      <h2>Mapping conflicts</h2><p>Review both versions before retrying local edits. Reviewing keeps local mappings and adopts the displayed server revision.</p>
      <button id="mapping-review" class="btn">Review latest server mappings</button><pre id="mapping-versions"></pre>
      <button id="mapping-retry" class="btn" disabled>Retry local mappings</button>
      <h2>Mapping profiles</h2><input id="profile-name" class="field-input" placeholder="Profile name" list="profile-names">
      <datalist id="profile-names">${Object.keys(profiles).map(n=>`<option value="${escAttr(n)}">`).join('')}</datalist>
      ${['save','load','delete','export','import'].map(op=>`<button class="btn" data-profile="${op}">${op}</button>`).join('')}
      <label>Profile JSON (copy or paste)<textarea class="field-input" id="profile-json" rows="8"></textarea></label>
      <h2>Diagnostics</h2><button id="engine-refresh" class="btn">Refresh diagnostics</button><pre id="engine-diagnostics"></pre>
      </div></div>`;
    const show = value => { document.getElementById('engine-diagnostics').textContent = JSON.stringify(value, null, 2); };
    show(tools);
    const run = fn => async () => { try { await fn(); } catch(e) { toast(e.message, 'error'); } };
    main.querySelector('#engine-back').onclick = () => navigate('settings');
    main.querySelector('#engine-refresh').onclick = run(async () => show(await api.get('/engine-tools')));
    main.querySelectorAll('[data-phase]').forEach(el => el.onclick = run(async () => show(await api.post('/calibration/'+el.dataset.phase, {}))));
    main.querySelector('#cal-apply').onclick = run(async () => {
      const value = (await api.get('/engine-tools')).calibration.result;
      if (!value) throw new Error('Complete both sampling steps first; use Refresh diagnostics to check progress.');
      main.querySelector('#cal-enabled').checked = true;
      main.querySelector('#cal-ratio').value = value.contactRatio;
      main.querySelector('#cal-depth').value = value.depthRatio;
    });
    main.querySelector('#engine-save').onclick = run(async () => {
      const payload = {...settings};
      main.querySelectorAll('[data-engine]').forEach(el => payload[el.dataset.engine] = Number(el.value));
      payload.calibration = {enabled:main.querySelector('#cal-enabled').checked,
        contactRatio:Number(main.querySelector('#cal-ratio').value), depthRatio:Number(main.querySelector('#cal-depth').value)};
      await api.post('/engine-settings', payload); toast('Engine settings saved', 'success');
    });
    main.querySelector('#mapping-review').onclick = run(async () => {
      const server = await api.get('/configuration');
      main.querySelector('#mapping-versions').textContent = JSON.stringify({server, local:state.configs.map(sanitizeConfigForSync)}, null, 2);
      main.querySelector('#mapping-retry').disabled = false;
    });
    main.querySelector('#mapping-retry').onclick = run(async () => { await pushConfigs(); });
    main.querySelector('#engine-test').onchange = run(async () => {
      await api.post('/test-mode', {enabled:main.querySelector('#engine-test').checked}); show(await api.get('/engine-tools'));
    });
    main.querySelectorAll('[data-profile]').forEach(el => el.onclick = run(async () => {
      const name = main.querySelector('#profile-name').value.trim();
      const op = el.dataset.profile;
      if (op === 'export') {
        const saved = await api.get('/profiles');
        if (!saved[name]) throw new Error('Select a saved profile');
        main.querySelector('#profile-json').value = JSON.stringify({name, configurations:saved[name]}, null, 2); return;
      }
      const imported = op === 'import' ? JSON.parse(main.querySelector('#profile-json').value) : {};
      await api.post('/profiles', {name: name || imported.name, operation:op, ...(op==='import' ? {configurations:imported.configurations} : {})});
      if (op === 'load') { await api.get('/configuration'); await pullConfigs(); }
      toast('Profile '+op+' completed', 'success');
    }));
  } catch(e) { main.textContent = e.message; }
}
