import { browser } from './browser.mjs';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import path from 'node:path';
const root=path.resolve(import.meta.dirname,'..'), out=path.join(root,'evidence/runtime');
await mkdir(out,{recursive:true});
const checks=[];function check(name,pass,detail){checks.push({name,pass:!!pass,detail});console.log((pass?'PASS ':'FAIL ')+name)}
const b=await browser();
async function load(){
  const {root:doc}=await b.send('DOM.getDocument'); const {nodeId}=await b.send('DOM.querySelector',{nodeId:doc.nodeId,selector:'#file'});
  await b.send('DOM.setFileInputFiles',{nodeId,files:[path.join(root,'evidence/ai/fixtures/00-original.png')]});
  for(let i=0;i<80;i++){if(await b.evaluate("!document.getElementById('canvas-wrap').hidden"))break;await new Promise(r=>setTimeout(r,50))}
  await b.evaluate("document.getElementById('zoom-100').click();document.getElementById('overlay').scrollIntoView({block:'center',behavior:'instant'})");
}
async function bounds(){return b.evaluate("(()=>{const r=document.getElementById('overlay').getBoundingClientRect();return {x:r.x,y:r.y,w:r.width,h:r.height}})()");}
async function mouse(x0,y0,x1,y1){const r=await bounds();await b.send('Input.dispatchMouseEvent',{type:'mousePressed',x:r.x+x0,y:r.y+y0,button:'left',clickCount:1});await b.send('Input.dispatchMouseEvent',{type:'mouseMoved',x:r.x+x1,y:r.y+y1,button:'left',buttons:1});await b.send('Input.dispatchMouseEvent',{type:'mouseReleased',x:r.x+x1,y:r.y+y1,button:'left',clickCount:1});}
async function touch(x0,y0,x1,y1){const r=await bounds();await b.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x:r.x+x0,y:r.y+y0,id:1}]});await b.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x:r.x+x1,y:r.y+y1,id:1}]});await b.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});}
async function hover(x,y){const r=await bounds();await b.send('Input.dispatchMouseEvent',{type:'mouseMoved',x:r.x+x,y:r.y+y});return b.evaluate("getComputedStyle(document.getElementById('overlay')).cursor");}
try{
  await b.send('Emulation.setDeviceMetricsOverride',{width:1440,height:1000,deviceScaleFactor:1,mobile:false});await b.navigate('http://127.0.0.1:8791/');await load();
  await mouse(24,36,232,84);
  check('Real mouse drag creates the selected image-space mask',await b.evaluate("document.getElementById('region-count').textContent==='1' && Number(document.getElementById('rx').value)===24 && Number(document.getElementById('rw').value)===208"));
  check('Pointer indicates moving, corner resizing and drawing automatically',await hover(100,55)==='move' && await hover(232,84)==='nwse-resize' && await hover(100,10)==='crosshair');
  await mouse(100,55,110,55);
  check('Real mouse drag moves a mask immediately after drawing',await b.evaluate("Number(document.getElementById('rx').value)===34 && document.getElementById('region-count').textContent==='1'"));
  await mouse(242,84,248,90);
  check('Corner drag resizes without changing tools',await b.evaluate("Number(document.getElementById('rw').value)===214 && Number(document.getElementById('rh').value)===54"));
  await b.evaluate("document.getElementById('undo').click();document.querySelector('.region-select').click()");
  check('Undo restores geometry before resizing',await b.evaluate("Number(document.getElementById('rx').value)===34 && Number(document.getElementById('rw').value)===208 && Number(document.getElementById('rh').value)===48"));
  await b.evaluate("document.getElementById('undo').click();document.querySelector('.region-select').click()");
  check('Undo restores geometry before moving',await b.evaluate("Number(document.getElementById('rx').value)===24 && Number(document.getElementById('rw').value)===208"));
  await mouse(170,5,245,26);
  check('Dragging empty space creates another mask automatically',await b.evaluate("document.getElementById('region-count').textContent==='2' && Number(document.getElementById('ry').value)===5"));
  await mouse(100,55,105,55);
  check('Dragging an unselected mask selects and moves it',await b.evaluate("Number(document.getElementById('rx').value)===29 && document.getElementById('region-count').textContent==='2'"));
  await b.evaluate("document.getElementById('draw').click()");await mouse(110,48,145,67);
  check('Draw can create an overlapping mask and returns to direct editing',await b.evaluate("document.getElementById('region-count').textContent==='3' && Number(document.getElementById('rx').value)===110 && Number(document.getElementById('rw').value)===35 && document.getElementById('draw').getAttribute('aria-pressed')==='false'"));
  await mouse(125,57,130,57);
  check('Direct movement selects the topmost overlapping mask',await b.evaluate("Number(document.getElementById('rx').value)===115 && Number(document.getElementById('rw').value)===35"));
  await b.evaluate("document.getElementById('blur').click();document.getElementById('confirm-blur').click()");await mouse(80,55,90,55);
  check('Moving preserves secure masking when new-region method is cosmetic',await b.evaluate("Number(document.getElementById('rx').value)===39 && [...document.querySelectorAll('.region-select')].every(e=>e.textContent.includes('Secure'))"));
  const drag=await bounds();
  await b.send('Input.dispatchMouseEvent',{type:'mousePressed',x:drag.x+80,y:drag.y+55,button:'left',clickCount:1});
  await b.send('Input.dispatchMouseEvent',{type:'mouseMoved',x:drag.x+85,y:drag.y+55,button:'left',buttons:1});
  check('Download is disabled during an unfinished drag',await b.evaluate("document.getElementById('download').disabled"));
  await b.send('Input.dispatchKeyEvent',{type:'keyDown',key:'Escape',code:'Escape',windowsVirtualKeyCode:27});
  await b.send('Input.dispatchKeyEvent',{type:'keyUp',key:'Escape',code:'Escape',windowsVirtualKeyCode:27});
  await b.send('Input.dispatchMouseEvent',{type:'mouseReleased',x:drag.x+85,y:drag.y+55,button:'left',clickCount:1});
  check('Escape cancels a drag without committing geometry',await b.evaluate("Number(document.getElementById('rx').value)===39 && !document.getElementById('download').disabled"));
  // Hold PNG encoding pending and attempt edits through normally blocked paths.
  await b.evaluate("window.realToBlob=HTMLCanvasElement.prototype.toBlob;window.pending=[];HTMLCanvasElement.prototype.toBlob=function(cb,...args){pending.push(()=>realToBlob.call(this,cb,...args))};window.saved=[];HTMLAnchorElement.prototype.click=function(){saved.push(this.download)};document.getElementById('download').click();");
  check('All sidebar controls are inert while export is encoding',await b.evaluate("document.querySelector('.controls').inert && document.getElementById('download').disabled"));
  const before=await b.evaluate("document.getElementById('rw').value");
  await b.evaluate("const f=document.getElementById('rw');f.value=5;f.dispatchEvent(new Event('change'));document.getElementById('undo').click();document.dispatchEvent(new KeyboardEvent('keydown',{key:'z',ctrlKey:true,bubbles:true}));");
  await b.evaluate("HTMLCanvasElement.prototype.toBlob=realToBlob;pending.forEach(f=>f())");for(let i=0;i<80;i++){if(await b.evaluate('saved.length>0'))break;await new Promise(r=>setTimeout(r,50))}
  check('Pending export ignores geometry/history mutations',await b.evaluate("document.getElementById('rw').value")===before);
  // Simulate a browser allocation/render failure to verify recovery rather than a permanent busy lock.
  await b.evaluate("window.realDraw=CanvasRenderingContext2D.prototype.drawImage;CanvasRenderingContext2D.prototype.drawImage=function(){throw Error('synthetic allocation failure')};document.getElementById('download').click();CanvasRenderingContext2D.prototype.drawImage=realDraw;");
  check('Rendering failure releases busy state and leaves reset available',await b.evaluate("!document.querySelector('.controls').inert && !document.getElementById('reset').disabled && document.getElementById('notice').textContent.includes('could not save')"));
  await b.evaluate("document.getElementById('reset').click()");
  check('Clear session removes visible source, regions and history',await b.evaluate("document.getElementById('canvas-wrap').hidden && document.getElementById('view').width===0 && document.getElementById('region-count').textContent==='0' && document.getElementById('undo').disabled"));
  await b.send('Emulation.setDeviceMetricsOverride',{width:375,height:812,deviceScaleFactor:1,mobile:true});await b.send('Emulation.setTouchEmulationEnabled',{enabled:true,maxTouchPoints:1});await load();
  await touch(24,36,232,84);
  check('Real touch drag creates a mask on a phone viewport',await b.evaluate("document.getElementById('region-count').textContent==='1' && !document.getElementById('download').disabled"));
  await touch(100,55,104,55);
  check('Touch moves a mask directly after drawing',await b.evaluate("Number(document.getElementById('rx').value)===28 && document.getElementById('region-count').textContent==='1'"));
  await touch(236,84,244,90);
  check('Touch resizes a selected corner without a mode change',await b.evaluate("Number(document.getElementById('rw').value)===216 && Number(document.getElementById('rh').value)===54"));
  await b.evaluate("window.savedPixels=[];window.realURL=URL.createObjectURL;URL.createObjectURL=function(blob){window.exportedBlob=blob;return realURL.call(URL,blob)};HTMLAnchorElement.prototype.click=function(){savedPixels.push(this.download)};document.getElementById('download').click()");for(let i=0;i<80;i++){if(await b.evaluate('savedPixels.length>0'))break;await new Promise(r=>setTimeout(r,50))}
  const pixels=await b.evaluate("(async()=>{const bitmap=await createImageBitmap(exportedBlob);const c=document.createElement('canvas');c.width=bitmap.width;c.height=bitmap.height;const ctx=c.getContext('2d');ctx.drawImage(bitmap,0,0);const d=ctx.getImageData(28,36,216,54).data;let bad=0;for(let i=0;i<d.length;i+=4)if(d[i]!==110||d[i+1]!==113||d[i+2]!==118||d[i+3]!==255)bad++;return {bad,pixels:d.length/4}})()");
  check('Touch-edited mask exports opaque replacement at every covered pixel',pixels.bad===0,pixels);
  await b.evaluate("window.scrollTo({top:0,behavior:'instant'})");await writeFile(path.join(out,'editor-mobile.png'),Buffer.from((await b.send('Page.captureScreenshot')).data,'base64'));
  await b.send('Emulation.setTouchEmulationEnabled',{enabled:false});await b.send('Emulation.setDeviceMetricsOverride',{width:1440,height:1000,deviceScaleFactor:1,mobile:false});
  await b.evaluate("document.getElementById('theme').click();window.scrollTo({top:0,behavior:'instant'})");await writeFile(path.join(out,'editor-light.png'),Buffer.from((await b.send('Page.captureScreenshot')).data,'base64'));
  const report={tested_at:new Date().toISOString(),html_sha256:createHash('sha256').update(await readFile(path.join(root,'dist/BlueMask.html'))).digest('hex'),checks};await writeFile(path.join(out,'interactions.json'),JSON.stringify(report,null,2)+'\n');if(checks.some(c=>!c.pass))process.exitCode=1;
}finally{await b.close()}
