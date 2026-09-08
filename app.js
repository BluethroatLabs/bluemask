(function () {
  'use strict';
  const $ = id => document.getElementById(id), E = BlueMaskEngine;
  const state = { source: null, regions: [], selected: -1, method: 'secure', drawNew: false, zoom: 'fit', peek: false, undo: [], redo: [], gesture: null, composite: null, busy: false, load: 0 };
  let nextID = 1, loadURL = null;
  const dialogs = [...document.querySelectorAll('dialog')];
  const modalOpen = () => dialogs.some(d => d.open);
  function notice(message) { $('notice').textContent = message; }
  function toast(message) { $('toast').textContent = message; $('toast').hidden = false; clearTimeout(toast.timer); toast.timer = setTimeout(() => { $('toast').hidden = true; }, 4500); }
  function openDialog(id) { $(id).showModal(); }
  for (const button of document.querySelectorAll('[data-close]')) button.onclick = () => button.closest('dialog').close();
  for (const button of document.querySelectorAll('[data-scroll]')) button.onclick = () => openDialog('scroll-dialog');
  $('tests').onclick = () => openDialog('tests-dialog');
  $('theme').onclick = () => {
    const light = document.body.classList.toggle('light');
    const label = light ? 'Switch to dark appearance' : 'Switch to light appearance';
    $('theme').setAttribute('aria-label', label); $('theme').title = label;
  };
  function method(value) {
    if (state.busy) return;
    state.method = value;
    for (const m of ['secure', 'blur']) { $(m).classList.toggle('selected', m === value); $(m).setAttribute('aria-pressed', String(m === value)); }
    $('method-description').textContent = value === 'secure' ? 'Replaces pixels with a solid mask.' : 'Softens pixels. Details may be recoverable.';
  }
  $('secure').onclick = () => method('secure');
  $('blur').onclick = () => { if (state.method !== 'blur') openDialog('mode-dialog'); };
  $('recommend-secure').onclick = () => { method('secure'); $('mode-dialog').close(); $('secure').focus(); };
  $('confirm-blur').onclick = () => { method('blur'); $('mode-dialog').close(); $('blur').focus(); };
  $('draw').onclick = () => {
    if (!state.source || state.busy || state.gesture) return;
    state.drawNew = !state.drawNew; state.selected = -1; $('overlay').dataset.action = 'draw'; refresh(); paintOverlay();
  };
  function help() {
    $('canvas-help').textContent = !state.source ? 'Choose an image, then draw over what you want to hide.' : state.peek ? 'Showing the original. Turn this off to download.' : state.drawNew ? 'Drag to draw a new mask. Press Escape to cancel.' : 'Drag an empty area to draw. Drag a mask to move it or a corner to resize.';
  }
  function snapshot() { return state.regions.map(r => ({ ...r })); }
  function remember() { state.undo.push(snapshot()); if (state.undo.length > 60) state.undo.shift(); state.redo = []; }
  function history(direction) {
    const from = state[direction], to = state[direction === 'undo' ? 'redo' : 'undo'];
    if (!from.length || state.gesture || state.busy) return;
    to.push(snapshot()); state.regions = from.pop(); state.selected = -1; render();
  }
  $('undo').onclick = () => history('undo'); $('redo').onclick = () => history('redo');
  function releaseCanvas(c) { if (c) { c.width = 0; c.height = 0; } }
  function clearSession() {
    state.load++; if (loadURL) URL.revokeObjectURL(loadURL); loadURL = null;
    releaseCanvas(state.source); releaseCanvas(state.composite); state.source = state.composite = null;
    state.regions = []; state.undo = []; state.redo = []; state.selected = -1; state.gesture = null; state.drawNew = false; state.peek = false; state.busy = false;
    $('peek').checked = false; $('file').value = ''; $('canvas-wrap').hidden = true; $('drop').hidden = false;
    releaseCanvas($('view')); releaseCanvas($('overlay')); $('dimensions').textContent = ''; $('overlay').dataset.action = 'draw'; method('secure'); notice(''); refresh();
  }
  $('reset').onclick = () => { clearSession(); toast('Editor session cleared. Your original file was not changed.'); $('choose').focus(); };
  function loadFile(file) {
    if (!file || modalOpen() || state.busy) return;
    if (!['image/png', 'image/jpeg', 'image/webp'].includes(file.type)) { notice('Please choose a PNG, JPEG or WebP image.'); return; }
    if (file.size > 35 * 1024 * 1024) { notice('This image is larger than 35 MB. Choose a smaller copy.'); return; }
    // Remove the prior private image as soon as a replacement is requested.
    clearSession(); const generation = ++state.load; state.busy = true; refresh();
    const image = new Image(); const url = URL.createObjectURL(file); loadURL = url;
    image.onload = () => {
      URL.revokeObjectURL(url); if (loadURL === url) loadURL = null;
      if (generation !== state.load) return;
      state.busy = false;
      if (!image.naturalWidth || !image.naturalHeight || image.naturalWidth * image.naturalHeight > 24000000 || Math.max(image.naturalWidth, image.naturalHeight) > 12000) { notice('This image is too large to edit safely here. Use a copy under 24 megapixels and 12,000 pixels per side.'); refresh(); return; }
      try {
        const c = document.createElement('canvas'); c.width = image.naturalWidth; c.height = image.naturalHeight;
        const ctx = c.getContext('2d'); ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, c.width, c.height); ctx.drawImage(image, 0, 0);
        state.source = c; state.zoom = 'fit'; $('canvas-wrap').hidden = false; $('drop').hidden = true;
        $('dimensions').textContent = `${c.width} × ${c.height} px`; render();
      } catch (_) { clearSession(); notice('The browser could not open that image. Try a smaller PNG or JPEG.'); }
      image.onload = image.onerror = null; image.src = '';
    };
    image.onerror = () => { URL.revokeObjectURL(url); if (generation === state.load) { loadURL = null; state.busy = false; notice('The browser could not read this image. Try a PNG or JPEG export.'); refresh(); } };
    image.src = url;
  }
  for (const id of ['choose', 'replace']) $(id).onclick = () => $('file').click();
  $('file').onchange = () => { const file = $('file').files[0]; $('file').value = ''; loadFile(file); };
  document.addEventListener('dragover', e => { if (e.dataTransfer?.types.includes('Files')) { e.preventDefault(); if (!modalOpen()) $('stage').classList.add('drag-over'); } });
  document.addEventListener('dragleave', e => { if (!e.relatedTarget) $('stage').classList.remove('drag-over'); });
  document.addEventListener('drop', e => { e.preventDefault(); $('stage').classList.remove('drag-over'); if (!modalOpen()) loadFile(e.dataTransfer?.files[0]); });
  document.addEventListener('paste', e => { if (modalOpen()) return; for (const item of e.clipboardData?.items || []) if (item.kind === 'file' && item.type.startsWith('image/')) { e.preventDefault(); loadFile(item.getAsFile()); break; } });
  $('demo').onclick = async () => {
    if (state.busy) return; const generation = state.load;
    await document.fonts.ready;
    if (generation !== state.load || state.busy) return;
    const c = document.createElement('canvas'); c.width = 1000; c.height = 600; const ctx = c.getContext('2d');
    ctx.fillStyle = '#f7f7f5'; ctx.fillRect(0, 0, 1000, 600); ctx.fillStyle = '#111'; ctx.font = '16px "Geist Mono"'; ctx.fillText('SAMPLE / ALL DETAILS ARE FICTIONAL', 60, 62);
    ctx.fillStyle = '#d9d9d5'; ctx.fillRect(60, 96, 880, 1); ctx.fillStyle = '#111'; ctx.font = '42px "Instrument Serif"'; ctx.fillText('Sample document', 60, 174);
    ctx.font = '22px "Geist Mono"'; ctx.fillText('NAME       ALEX MORGAN', 60, 255); ctx.fillText('EMAIL      alex@example.com', 60, 306); ctx.fillText('REFERENCE  4827 1936', 60, 357);
    ctx.fillStyle = '#dadad5'; ctx.fillRect(60, 406, 880, 112); ctx.fillStyle = '#444'; ctx.font = '18px "Geist Mono"'; ctx.fillText('Try masking the name and reference.', 84, 451); ctx.fillText('Nothing in this sample is real personal data.', 84, 485);
    c.toBlob(blob => { if (blob && generation === state.load) loadFile(new File([blob], 'sample.png', { type: 'image/png' })); releaseCanvas(c); });
  };
  function scale() {
    if (!state.source) return 1;
    if (state.zoom !== 'fit') return state.zoom;
    const stage = $('stage'), style = getComputedStyle(stage);
    const width = stage.clientWidth - parseFloat(style.paddingLeft) - parseFloat(style.paddingRight);
    const height = stage.clientHeight - parseFloat(style.paddingTop) - parseFloat(style.paddingBottom);
    return Math.min(1, Math.max(1, width) / state.source.width, Math.max(1, height) / state.source.height);
  }
  function paint() {
    if (!state.source) return;
    const s = scale(), width = Math.max(1, Math.round(state.source.width * s)), height = Math.max(1, Math.round(state.source.height * s));
    const dpr = Math.min(devicePixelRatio || 1, 2);
    for (const c of [$('view'), $('overlay')]) { c.style.width = `${width}px`; c.style.height = `${height}px`; c.width = Math.round(width * dpr); c.height = Math.round(height * dpr); }
    $('canvas-wrap').style.width = `${width}px`; $('canvas-wrap').style.height = `${height}px`;
    const ctx = $('view').getContext('2d'); ctx.drawImage(state.peek ? state.source : state.composite, 0, 0, $('view').width, $('view').height);
    $('zoom-fit').textContent = state.zoom === 'fit' ? `Fit · ${Math.round(s * 100)}%` : 'Fit';
    help();
    if (!state.peek) notice(s < 0.6 ? 'This preview is reduced. Check at 100% to make sure every letter or detail is covered.' : '');
    paintOverlay();
  }
  function paintOverlay() {
    const c = $('overlay'), ctx = c.getContext('2d'); ctx.clearRect(0, 0, c.width, c.height); if (!state.source || state.peek) return;
    const s = c.width / state.source.width, dpr = Math.min(devicePixelRatio || 1, 2);
    let list = state.regions;
    if (state.gesture?.candidate) list = list.filter(r => r.id !== state.gesture.id).concat([{ ...state.gesture.candidate, id: state.gesture.id || -1, method: state.gesture.original?.method || state.method }]);
    for (const r of list) {
      const selected = r.id === state.selected || r.id === state.gesture?.id;
      ctx.strokeStyle = r.method === 'blur' ? '#d8b378' : '#ffffff'; ctx.lineWidth = (selected ? 2 : 1) * dpr; ctx.setLineDash(selected ? [] : [4 * dpr, 3 * dpr]);
      ctx.strokeRect(r.x * s + 0.5, r.y * s + 0.5, r.w * s, r.h * s); ctx.setLineDash([]);
      if (selected) for (const [x, y] of [[r.x, r.y], [r.x + r.w, r.y], [r.x, r.y + r.h], [r.x + r.w, r.y + r.h]]) { ctx.fillStyle = '#fff'; ctx.fillRect(x * s - 4 * dpr, y * s - 4 * dpr, 8 * dpr, 8 * dpr); }
    }
  }
  function render() {
    if (state.source) {
      try { const old = state.composite; state.composite = E.render(state.source, state.regions); releaseCanvas(old); paint(); }
      catch (_) { releaseCanvas(state.composite); state.composite = null; notice('The image could not be rendered. Reduce the image size or clear the session.'); }
    }
    refresh();
  }
  function refresh() {
    const loaded = !!state.source, has = state.regions.length > 0;
    document.querySelector('.controls').inert = state.busy;
    for (const id of ['replace', 'reset', 'add-region', 'peek', 'draw', 'zoom-fit', 'zoom-100', 'zoom-in', 'zoom-out']) $(id).disabled = !loaded || state.busy;
    $('draw').classList.toggle('selected', state.drawNew); $('draw').setAttribute('aria-pressed', String(state.drawNew)); help();
    $('undo').disabled = !state.undo.length || state.busy; $('redo').disabled = !state.redo.length || state.busy;
    $('download').disabled = !loaded || !has || state.peek || state.busy || !!state.gesture || !state.composite;
    $('choose').disabled = state.busy; $('demo').disabled = state.busy;
    $('region-count').textContent = String(state.regions.length); $('empty-regions').hidden = has;
    $('regions').replaceChildren();
    for (const [i, r] of state.regions.entries()) {
      const li = document.createElement('li'); li.classList.toggle('selected', r.id === state.selected);
      const button = document.createElement('button'); button.type = 'button'; button.className = 'region-select';
      button.textContent = `${String(i + 1).padStart(2, '0')} / ${r.method === 'secure' ? 'Secure mask' : 'Appearance only'}`; button.setAttribute('aria-pressed', String(r.id === state.selected));
      button.onclick = () => { if (state.busy || state.gesture) return; state.selected = r.id; state.drawNew = false; refresh(); paintOverlay(); };
      const remove = document.createElement('button'); remove.type = 'button'; remove.className = 'region-remove'; remove.textContent = '×'; remove.setAttribute('aria-label', `Remove region ${i + 1}`);
      remove.onclick = () => { if (state.busy) return; remember(); state.regions = state.regions.filter(x => x.id !== r.id); state.selected = -1; render(); };
      li.append(button, remove); $('regions').append(li);
    }
    const selected = state.regions.find(r => r.id === state.selected); $('coordinates').hidden = !selected;
    if (selected) { for (const [id, key] of [['rx', 'x'], ['ry', 'y'], ['rw', 'w'], ['rh', 'h']]) $(id).value = selected[key]; $('make-secure').hidden = selected.method === 'secure'; }
    $('export-help').textContent = state.peek ? 'Turn off “Show original” before downloading.' : state.regions.some(r => r.method === 'blur') ? 'Contains cosmetic blur. Appearance only.' : 'Check coverage at 100% before saving.';
  }
  function point(e) { const b = $('overlay').getBoundingClientRect(); return { x: Math.max(0, Math.min(state.source.width, (e.clientX - b.left) * state.source.width / b.width)), y: Math.max(0, Math.min(state.source.height, (e.clientY - b.top) * state.source.height / b.height)) }; }
  function hitTest(p) {
    if (state.drawNew) return { kind: 'draw' };
    const selected = state.regions.find(r => r.id === state.selected), tolerance = 12 / scale();
    if (selected) for (const [kind, x, y] of [['nw', selected.x, selected.y], ['ne', selected.x + selected.w, selected.y], ['sw', selected.x, selected.y + selected.h], ['se', selected.x + selected.w, selected.y + selected.h]]) {
      if (Math.hypot(p.x - x, p.y - y) < tolerance) return { kind, region: selected };
    }
    const region = [...state.regions].reverse().find(r => p.x >= r.x && p.x <= r.x + r.w && p.y >= r.y && p.y <= r.y + r.h);
    return region ? { kind: 'move', region } : { kind: 'draw' };
  }
  $('overlay').onpointerdown = e => {
    if (!state.source || state.peek || state.busy || state.gesture || e.button !== 0 || !e.isPrimary || modalOpen()) return;
    e.preventDefault(); $('overlay').focus(); const p = point(e), hit = hitTest(p);
    state.selected = hit.region?.id ?? -1;
    state.gesture = { start: p, kind: hit.kind, pointerId: e.pointerId, ...(hit.region ? { id: hit.region.id, original: { ...hit.region } } : {}) };
    $('overlay').dataset.action = hit.kind;
    try { $('overlay').setPointerCapture(e.pointerId); } catch (_) {} refresh(); paintOverlay();
  };
  $('overlay').onpointermove = e => {
    if (!state.source || state.peek || state.busy) { $('overlay').dataset.action = 'idle'; return; }
    if (!state.gesture) { $('overlay').dataset.action = hitTest(point(e)).kind; return; }
    if (e.pointerId !== state.gesture.pointerId) return;
    const p = point(e), g = state.gesture, dx = p.x - g.start.x, dy = p.y - g.start.y; let r;
    if (g.kind === 'draw') r = { x: g.start.x, y: g.start.y, w: dx, h: dy };
    else if (g.kind === 'move') r = { ...g.original, x: Math.max(0, Math.min(state.source.width - g.original.w, g.original.x + dx)), y: Math.max(0, Math.min(state.source.height - g.original.h, g.original.y + dy)) };
    else {
      const o = g.original, left = g.kind.includes('w') ? p.x : o.x, right = g.kind.includes('e') ? p.x : o.x + o.w, top = g.kind.includes('n') ? p.y : o.y, bottom = g.kind.includes('s') ? p.y : o.y + o.h;
      r = { x: left, y: top, w: right - left, h: bottom - top };
    }
    g.candidate = E.rect(r, state.source.width, state.source.height); paintOverlay();
  };
  $('overlay').onpointerup = e => {
    const g = state.gesture; if (!g || e.pointerId !== g.pointerId) return; state.gesture = null;
    if (g.candidate && (g.kind !== 'draw' || g.candidate.w >= 3 && g.candidate.h >= 3)) {
      remember(); if (g.kind === 'draw') { const r = { ...g.candidate, id: nextID++, method: state.method, radius: 10 }; state.regions.push(r); state.selected = r.id; state.drawNew = false; }
      else state.regions = state.regions.map(r => r.id === g.id ? { ...r, ...g.candidate } : r);
    }
    render(); $('overlay').dataset.action = hitTest(point(e)).kind;
  };
  $('overlay').onpointercancel = e => { if (state.gesture?.pointerId !== e.pointerId) return; state.gesture = null; paintOverlay(); refresh(); };
  $('add-region').onclick = () => { if (!state.source || state.busy || state.gesture) return; remember(); const w = Math.max(1, Math.round(state.source.width * 0.3)), h = Math.max(1, Math.round(state.source.height * 0.15)); const r = { x: Math.floor((state.source.width - w) / 2), y: Math.floor((state.source.height - h) / 2), w, h, method: state.method, id: nextID++, radius: 10 }; state.regions.push(r); state.selected = r.id; state.drawNew = false; render(); $('rx').focus(); };
  for (const [id, key] of [['rx', 'x'], ['ry', 'y'], ['rw', 'w'], ['rh', 'h']]) $(id).onchange = () => {
    if (state.busy) return;
    const r = state.regions.find(r => r.id === state.selected), value = Number($(id).value); if (!r || !Number.isFinite(value)) return;
    const updated = { ...r, [key]: Math.max(key === 'w' || key === 'h' ? 1 : 0, Math.round(value)) };
    updated.x = Math.min(state.source.width - 1, updated.x); updated.y = Math.min(state.source.height - 1, updated.y);
    updated.w = Math.min(state.source.width - updated.x, updated.w); updated.h = Math.min(state.source.height - updated.y, updated.h);
    remember(); Object.assign(r, updated); render();
  };
  $('make-secure').onclick = () => { if (state.busy) return; const r = state.regions.find(r => r.id === state.selected); if (r) { remember(); r.method = 'secure'; render(); } };
  $('peek').onchange = () => { state.peek = $('peek').checked; state.gesture = null; paint(); refresh(); };
  for (const [id, action] of [['zoom-fit', () => 'fit'], ['zoom-100', () => 1], ['zoom-in', () => Math.min(4, scale() * 1.5)], ['zoom-out', () => Math.max(0.05, scale() / 1.5)]]) $(id).onclick = () => { state.zoom = action(); paint(); };
  window.addEventListener('resize', paint);
  document.addEventListener('keydown', e => {
    if (state.busy || modalOpen() || /INPUT|TEXTAREA|SELECT/.test(document.activeElement?.tagName) || !state.source) return;
    if (e.key === 'Escape') { e.preventDefault(); state.gesture = null; state.drawNew = false; $('overlay').dataset.action = 'draw'; refresh(); paintOverlay(); return; }
    if (state.gesture) return;
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'z') { e.preventDefault(); history(e.shiftKey ? 'redo' : 'undo'); }
    if (document.activeElement === $('overlay') && ['Delete', 'Backspace'].includes(e.key) && state.selected !== -1) { e.preventDefault(); remember(); state.regions = state.regions.filter(r => r.id !== state.selected); state.selected = -1; render(); }
  });
  async function saveImage() {
    if (!state.source || !state.regions.length || state.peek || state.busy || state.gesture || !state.composite) return;
    state.busy = true; refresh(); const generation = state.load;
    // Snapshot the rendered image so a later edit cannot change an in-flight save.
    let output;
    try {
      output = E.render(state.source, state.regions);
      const blob = await new Promise(resolve => output.toBlob(resolve, 'image/png'));
      if (!blob) throw new Error('Encoding failed');
      if (generation !== state.load) return;
      const url = URL.createObjectURL(blob), a = document.createElement('a'); a.href = url; a.download = 'bluemask.png'; document.body.append(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(url), 10000);
      toast('PNG ready. Open the downloaded image and review it before sharing.');
    } catch (_) { notice('The browser could not save the image. Try a smaller image.'); }
    finally { releaseCanvas(output); if (generation === state.load) { state.busy = false; refresh(); } }
  }
  $('download').onclick = () => {
    if ($('download').disabled) return;
    const count = state.regions.filter(r => r.method === 'blur').length;
    if (count) { $('blur-export-count').textContent = `${count} ${count === 1 ? 'region uses' : 'regions use'} cosmetic blur. Details may be recoverable.`; openDialog('export-dialog'); }
    else saveImage();
  };
  $('secure-all').onclick = () => { remember(); state.regions.forEach(r => { r.method = 'secure'; }); method('secure'); $('export-dialog').close(); render(); toast('All regions now use secure masking. Review, then download.'); };
  $('export-blur').onclick = () => { $('export-dialog').close(); saveImage(); };
  function connection() { $('connection').textContent = navigator.onLine ? 'Browser reports a network connection. This is only a hint.' : 'Browser reports offline. This is only a hint; verify using your device controls.'; }
  $('paranoia').onclick = () => { connection(); $('paranoia-loaded').hidden = !state.source; openDialog('paranoia-dialog'); };
  $('begin-offline').onclick = () => { $('paranoia-dialog').close(); if (state.source) clearSession(); toast('Disconnect with your device controls before choosing your private image.'); };
  window.addEventListener('online', connection); window.addEventListener('offline', connection);
  if (location.protocol === 'file:') {
    $('offline-download').removeAttribute('href'); $('offline-download').removeAttribute('download'); $('offline-download').textContent = 'You are using the offline edition';
    $('paranoia-download').hidden = true; $('begin-offline').textContent = 'Continue with this offline edition';
    $('source-download').removeAttribute('href'); $('source-download').removeAttribute('download'); $('source-download').textContent = 'Source and release hashes are available with the hosted edition.'; $('manifest-download').hidden = true;
    if ($('evidence-download')) { $('evidence-download').removeAttribute('href'); $('evidence-download').removeAttribute('download'); $('evidence-download').textContent = 'For full reproduction files, download the separate evidence bundle from the hosted edition before disconnecting.'; }
  }
  method('secure'); refresh(); connection();
})();
