import { spawn } from 'node:child_process';
import { mkdtemp, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';

export async function browser() {
  const profile = await mkdtemp(path.join(tmpdir(), 'bluemask-browser-'));
  const child = spawn('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', [
    '--headless=new', '--no-first-run', '--no-default-browser-check', '--disable-extensions',
    '--disable-background-networking', '--disable-component-update', '--remote-debugging-port=0',
    '--remote-debugging-address=127.0.0.1', `--user-data-dir=${profile}`, 'about:blank'
  ], { stdio: ['ignore', 'ignore', 'pipe'] });
  let stderr = '';
  const endpoint = await new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error('Chrome startup timeout: ' + stderr.slice(-1000))), 20000);
    child.stderr.on('data', b => { stderr += b; const m = stderr.match(/DevTools listening on (ws:\/\/[^\s]+)/); if (m) { clearTimeout(timer); resolve(m[1]); } });
    child.on('error', e => { clearTimeout(timer); reject(e); });
  });
  const origin = endpoint.replace(/^ws:/, 'http:').split('/devtools/')[0];
  const tabs = await (await fetch(`${origin}/json/list`)).json();
  const tab = tabs.find(t => t.type === 'page');
  const ws = new WebSocket(tab.webSocketDebuggerUrl);
  await new Promise((resolve, reject) => { ws.onopen = resolve; ws.onerror = reject; });
  let id = 0; const waiting = new Map(), listeners = new Map();
  ws.onmessage = e => {
    const data = JSON.parse(e.data);
    if (data.id && waiting.has(data.id)) {
      const p = waiting.get(data.id); waiting.delete(data.id); clearTimeout(p.timer);
      data.error ? p.reject(new Error(JSON.stringify(data.error))) : p.resolve(data.result);
    } else if (data.method) for (const listener of listeners.get(data.method) || []) listener(data.params);
  };
  const send = (method, params = {}) => new Promise((resolve, reject) => {
    const n = ++id; const timer = setTimeout(() => { waiting.delete(n); reject(new Error(method + ' timeout')); }, 60000);
    waiting.set(n, { resolve, reject, timer }); ws.send(JSON.stringify({ id: n, method, params }));
  });
  await send('Page.enable'); await send('Runtime.enable'); await send('Network.enable');
  return {
    send,
    on(method, listener) { if (!listeners.has(method)) listeners.set(method, []); listeners.get(method).push(listener); },
    async evaluate(expression) {
      const r = await send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true });
      if (r.exceptionDetails) throw new Error(JSON.stringify(r.exceptionDetails)); return r.result.value;
    },
    async navigate(url) {
      await send('Page.navigate', { url });
      for (let i = 0; i < 100; i++) {
        await new Promise(r => setTimeout(r, 100));
        if (await this.evaluate('document.readyState') === 'complete') return;
      }
      throw new Error('Navigation timeout');
    },
    async close() {
      ws.close(); child.kill('SIGTERM');
      await new Promise(resolve => { if (child.exitCode !== null) return resolve(); child.once('exit', resolve); setTimeout(resolve, 5000); });
      if (child.exitCode === null) child.kill('SIGKILL');
      await rm(profile, { recursive: true, force: true, maxRetries: 4, retryDelay: 250 });
    }
  };
}
