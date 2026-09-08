import { browser } from './browser.mjs';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import path from 'node:path';
const root = path.resolve(import.meta.dirname, '..');
const url = process.argv[2] || 'http://127.0.0.1:8791/';
const output = path.join(root, 'evidence/runtime'); await mkdir(output, { recursive: true });
const checks = [], network = [], errors = [];
function check(name, result, detail) { checks.push({ name, pass: !!result, ...(detail === undefined ? {} : { detail }) }); console.log((result ? 'PASS ' : 'FAIL ') + name); }
const b = await browser();
try {
  b.on('Network.requestWillBeSent', e => { if (/^https?:/.test(e.request.url)) network.push({ url: e.request.url, method: e.request.method }); });
  b.on('Runtime.exceptionThrown', e => errors.push(e.exceptionDetails.text + ': ' + e.exceptionDetails.exception?.description));
  await b.send('Emulation.setDeviceMetricsOverride', { width: 1440, height: 1000, deviceScaleFactor: 1, mobile: false });
  await b.navigate(url);
  await b.evaluate("window.violations=[];document.addEventListener('securitypolicyviolation',e=>violations.push(e.violatedDirective));");
  check('Secure mode is the default; untouched export is blocked', await b.evaluate("document.getElementById('secure').getAttribute('aria-pressed')==='true' && document.getElementById('download').disabled"));
  await b.evaluate("document.getElementById('blur').click()");
  check('Cosmetic blur opens explicit warning without changing mode', await b.evaluate("document.getElementById('mode-dialog').open && document.getElementById('secure').getAttribute('aria-pressed')==='true'"));
  check('Recommended secure action receives initial focus', await b.evaluate("document.activeElement.id==='recommend-secure'"));
  await b.send('Input.dispatchKeyEvent', { type: 'keyDown', key: 'Escape', code: 'Escape', windowsVirtualKeyCode: 27 });
  await b.send('Input.dispatchKeyEvent', { type: 'keyUp', key: 'Escape', code: 'Escape', windowsVirtualKeyCode: 27 });
  check('Escape cancels without enabling cosmetic blur', await b.evaluate("!document.getElementById('mode-dialog').open && document.getElementById('secure').getAttribute('aria-pressed')==='true'"));
  await b.evaluate("document.getElementById('blur').click();document.getElementById('confirm-blur').click()");
  check('Cosmetic mode requires explicit confirmation', await b.evaluate("document.getElementById('blur').getAttribute('aria-pressed')==='true'"));
  const beforeImage = network.length;
  await b.evaluate("document.getElementById('demo').click()");
  for (let i = 0; i < 80; i++) { if (await b.evaluate("!document.getElementById('canvas-wrap').hidden")) break; await new Promise(r => setTimeout(r, 50)); }
  check('A new image resets to secure mode and blocks untouched export', await b.evaluate("document.getElementById('secure').getAttribute('aria-pressed')==='true' && document.getElementById('download').disabled && !document.getElementById('canvas-wrap').hidden"));
  check('Fit displays the complete image inside the editor viewport', await b.evaluate("(()=>{const v=document.getElementById('view').getBoundingClientRect(),s=document.getElementById('stage').getBoundingClientRect();return v.top>=s.top&&v.left>=s.left&&v.bottom<=s.bottom&&v.right<=s.right})()"));
  await new Promise(r => setTimeout(r, 250));
  check('Successful image load does not emit a false load error', await b.evaluate("!document.getElementById('notice').textContent.includes('could not')"));
  await b.evaluate("document.getElementById('add-region').click()");
  check('Keyboard-accessible region creation enables export', await b.evaluate("document.getElementById('region-count').textContent==='1' && !document.getElementById('download').disabled"));
  await b.evaluate("document.getElementById('peek').click()");
  check('Showing original blocks export', await b.evaluate("document.getElementById('download').disabled"));
  await b.evaluate("document.getElementById('peek').click();document.getElementById('blur').click();document.getElementById('confirm-blur').click();document.getElementById('add-region').click();document.getElementById('download').click()");
  check('Mixed-method export requires an additional explicit warning', await b.evaluate("document.getElementById('export-dialog').open && document.querySelectorAll('#regions li').length===2 && document.querySelector('#regions li').textContent.includes('Secure')"));
  await b.evaluate("document.getElementById('secure-all').click()");
  check('Recommended export action converts to secure and requires review', await b.evaluate("!document.getElementById('export-dialog').open && [...document.querySelectorAll('#regions li')].every(e=>e.textContent.includes('Secure'))"));
  // Capture the real PNG at the final download boundary without navigating away.
  await b.evaluate("window.downloads=[];window.exportBlobs={};window.realObjectURL=URL.createObjectURL;URL.createObjectURL=function(blob){const url=realObjectURL.call(URL,blob);exportBlobs[url]=blob;return url};window.realAnchorClick=HTMLAnchorElement.prototype.click;HTMLAnchorElement.prototype.click=function(){downloads.push({name:this.download,url:this.href})};document.getElementById('download').click()");
  for (let i = 0; i < 80; i++) { if (await b.evaluate('downloads.length>0')) break; await new Promise(r => setTimeout(r, 50)); }
  const exported = await b.evaluate("(async()=>{const d=downloads[0];const buffer=await exportBlobs[d.url].arrayBuffer();const bytes=new Uint8Array(buffer);let s='';for(const x of bytes)s+=String.fromCharCode(x);return {name:d.name,png:btoa(s)}})()");
  const png = Buffer.from(exported.png, 'base64'); await writeFile(path.join(output, 'sample-export.png'), png);
  check('Export uses generic name and genuine PNG bytes', exported.name === 'bluemask.png' && png.subarray(0, 8).equals(Buffer.from([137,80,78,71,13,10,26,10])));
  const chunks = []; for (let off = 8; off + 12 <= png.length;) { const size = png.readUInt32BE(off); chunks.push(png.toString('ascii', off + 4, off + 8)); off += size + 12; }
  check('Fresh export has no EXIF, textual metadata, or animation frames', chunks.every(c => !['eXIf', 'tEXt', 'zTXt', 'iTXt', 'acTL', 'fcTL', 'fdAT'].includes(c)), chunks);
  check('Image selection, masking and export make no HTTP requests', network.length === beforeImage, network.slice(beforeImage));
  check('Normal editor flow raises no CSP violations',await b.evaluate('violations.length===0'),await b.evaluate('violations'));
  // General non-interference over random contents, geometry and overlapping cosmetics.
  const invariance = await b.evaluate(`(()=>{
    let seed=20260906,failures=0;const rand=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296};
    for(let t=0;t<160;t++){
      const a=document.createElement('canvas');a.width=64;a.height=48;const ac=a.getContext('2d');const id=ac.createImageData(64,48);
      for(let i=0;i<id.data.length;i+=4){id.data[i]=rand()*256;id.data[i+1]=rand()*256;id.data[i+2]=rand()*256;id.data[i+3]=rand()*256}ac.putImageData(id,0,0);
      const rs=[];for(let j=0;j<3;j++)rs.push({x:rand()*64-8,y:rand()*48-8,w:rand()*40+3,h:rand()*30+3,method:'secure'});
      rs.push({x:0,y:0,w:64,h:48,method:'blur',radius:3});
      const b=document.createElement('canvas');b.width=64;b.height=48;const bc=b.getContext('2d');bc.putImageData(id,0,0);
      const altered=bc.getImageData(0,0,64,48);for(const box of rs.filter(r=>r.method==='secure')){const r=BlueMaskEngine.rect(box,64,48);if(!r)continue;for(let y=r.y;y<r.y+r.h;y++)for(let x=r.x;x<r.x+r.w;x++){const k=(y*64+x)*4;for(let ch=0;ch<4;ch++)altered.data[k+ch]=rand()*256}}bc.putImageData(altered,0,0);
      const oa=BlueMaskEngine.render(a,rs),ob=BlueMaskEngine.render(b,[...rs].reverse());const da=oa.getContext('2d').getImageData(0,0,64,48).data,db=ob.getContext('2d').getImageData(0,0,64,48).data;
      if(da.some((v,i)=>v!==db[i]))failures++;for(const c of [a,b,oa,ob])c.width=0;
    }return {trials:160,failures};
  })()`);
  check('Secure output is independent of hidden pixels with overlaps and reversed order', invariance.failures === 0, invariance);
  await b.evaluate("document.getElementById('paranoia').click()");
  check('Paranoia mode describes user-controlled disconnection', await b.evaluate("document.getElementById('paranoia-dialog').innerText.includes('Your device controls that connection')"));
  await b.evaluate("document.getElementById('paranoia-dialog').close();document.querySelector('[data-scroll]').click()");
  await writeFile(path.join(output, 'privacy-scroll-desktop.png'), Buffer.from((await b.send('Page.captureScreenshot')).data, 'base64'));
  await b.evaluate("document.getElementById('scroll-dialog').close();window.scrollTo({top:0,behavior:'instant'})");
  await writeFile(path.join(output, 'editor-desktop.png'), Buffer.from((await b.send('Page.captureScreenshot', { captureBeyondViewport: false })).data, 'base64'));
  await b.send('Emulation.setDeviceMetricsOverride', { width: 375, height: 812, deviceScaleFactor: 1, mobile: true });
  await new Promise(r => setTimeout(r, 200));
  check('Phone layout has no horizontal document overflow', await b.evaluate('document.documentElement.scrollWidth<=375'), await b.evaluate('document.documentElement.scrollWidth'));
  await b.evaluate("document.getElementById('blur').click()");
  check('Warning dialog fits phone viewport', await b.evaluate("(()=>{const r=document.getElementById('mode-dialog').getBoundingClientRect();return r.left>=0&&r.right<=375&&r.top>=0&&r.bottom<=innerHeight})()"));
  await writeFile(path.join(output, 'warning-mobile.png'), Buffer.from((await b.send('Page.captureScreenshot')).data, 'base64'));
  await b.evaluate("document.getElementById('mode-dialog').close()");
  // A fresh offline-file navigation prevents HTTP-cache success from posing as offline support.
  await b.send('Network.emulateNetworkConditions', { offline: true, latency: 0, downloadThroughput: 0, uploadThroughput: 0 });
  const beforeOffline = network.length;
  await b.navigate('file://' + path.join(root, 'dist/BlueMask.html'));
  check('Self-contained file opens with browser network disabled', await b.evaluate("typeof BlueMaskEngine==='object' && document.getElementById('secure').getAttribute('aria-pressed')==='true'"));
  await b.evaluate("document.getElementById('demo').click()");
  for (let i=0;i<80;i++){if(await b.evaluate("!document.getElementById('canvas-wrap').hidden"))break;await new Promise(r=>setTimeout(r,50))}
  await b.evaluate("document.getElementById('add-region').click();window.offlineDownloads=[];HTMLAnchorElement.prototype.click=function(){offlineDownloads.push(this.download)};document.getElementById('download').click()");
  for(let i=0;i<80;i++){if(await b.evaluate('offlineDownloads.length>0'))break;await new Promise(r=>setTimeout(r,50))}
  check('Offline file completes image creation, masking and PNG export', await b.evaluate("offlineDownloads[0]==='bluemask.png'"));
  check('Offline operation makes no HTTP requests', network.length===beforeOffline,network.slice(beforeOffline));
  const storage=await b.evaluate("(async()=>({local:localStorage.length,session:sessionStorage.length,dbs:(await indexedDB.databases()).length,caches:typeof caches==='undefined'?0:(await caches.keys()).length}))()");
  check('App writes no web storage during tested flow',Object.values(storage).every(x=>x===0),storage);
  check('No uncaught browser errors', errors.length===0,errors);
  const report={tested_at:new Date().toISOString(),browser:await b.send('Browser.getVersion'),html_sha256:createHash('sha256').update(await readFile(path.join(root,'dist/BlueMask.html'))).digest('hex'),checks,network,errors};
  await writeFile(path.join(output,'results.json'),JSON.stringify(report,null,2)+'\n');
  if(checks.some(c=>!c.pass))process.exitCode=1;
} finally {await b.close();}
