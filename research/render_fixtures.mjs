// Product-engine exports of our own synthetic fixtures. No hosted application.
import { readFile, writeFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import { browser } from '../scripts/browser.mjs';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const hash = bytes => createHash('sha256').update(bytes).digest('hex');
const manifest = JSON.parse(await readFile(path.join(root, 'evidence/ai/fixtures/manifest.json'), 'utf8'));
if (!manifest.synthetic_only || manifest.sample_count !== 12) throw new Error('Expected only our 12 generated fixtures');
const engine = await readFile(path.join(root, 'engine.js'), 'utf8');
const b = await browser();
try {
  const version = await b.send('Browser.getVersion');
  await b.send('Network.emulateNetworkConditions', { offline: true, latency: 0, downloadThroughput: 0, uploadThroughput: 0 });
  await b.evaluate(engine);
  const files = [];
  for (const sample of manifest.samples) {
    const original = await readFile(path.join(root, sample.original));
    const dataURL = 'data:image/png;base64,' + original.toString('base64');
    const result = await b.evaluate(`(async () => {
      const image = new Image(); image.src = ${JSON.stringify(dataURL)}; await image.decode();
      const source = document.createElement('canvas'); source.width = image.width; source.height = image.height;
      source.getContext('2d').drawImage(image, 0, 0);
      return BlueMaskEngine.render(source, [${JSON.stringify(sample.region)}]).toDataURL('image/png');
    })()`);
    const bytes = Buffer.from(result.split(',')[1], 'base64');
    const output = `evidence/ai/fixtures/${sample.id}-secure.png`;
    await writeFile(path.join(root, output), bytes);
    files.push({ input: sample.original, input_sha256: hash(original), output, output_sha256: hash(bytes), region: sample.region });
  }
  await writeFile(path.join(root, 'evidence/ai/render-provenance.json'), JSON.stringify({
    generated_at_utc: new Date().toISOString(), synthetic_only: true,
    renderer: 'BlueMaskEngine.render', engine_sha256: hash(engine),
    browser: version, browser_network_emulation: 'offline',
    source_image_loaded_from: 'inline data URL', files
  }, null, 2) + '\n');
  console.log(JSON.stringify({ exported: files.length, unique_secure_pngs: new Set(files.map(f => f.output_sha256)).size }));
} finally {
  await b.close();
}
