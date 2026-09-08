/* BlueMask: local canvas rendering. No network or storage APIs. */
(function (root) {
  'use strict';
  const FILL = '#6e7176';
  function rect(r, width, height) {
    if (![r.x, r.y, r.w, r.h].every(Number.isFinite)) return null;
    const left = Math.max(0, Math.min(width, Math.floor(Math.min(r.x, r.x + r.w))));
    const top = Math.max(0, Math.min(height, Math.floor(Math.min(r.y, r.y + r.h))));
    const right = Math.max(0, Math.min(width, Math.ceil(Math.max(r.x, r.x + r.w))));
    const bottom = Math.max(0, Math.min(height, Math.ceil(Math.max(r.y, r.y + r.h))));
    return right > left && bottom > top ? { x: left, y: top, w: right - left, h: bottom - top } : null;
  }
  function canvas(width, height) {
    const c = document.createElement('canvas'); c.width = width; c.height = height; return c;
  }
  function cover(ctx, boxes) {
    ctx.save(); ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over';
    ctx.fillStyle = FILL;
    for (const r of boxes) ctx.fillRect(r.x, r.y, r.w, r.h);
    ctx.restore();
  }
  // Three separable box passes produce a soft cosmetic blur on every browser.
  // The input is already sanitized; secure pixels can never enter these sums.
  function soften(image, radius) {
    const { width: w, height: h } = image;
    let input = new Uint8ClampedArray(image.data), output = new Uint8ClampedArray(input.length);
    const span = radius * 2 + 1;
    for (let pass = 0; pass < 3; pass++) {
      for (const horizontal of [true, false]) {
        const major = horizontal ? h : w, minor = horizontal ? w : h;
        const step = horizontal ? 4 : w * 4;
        for (let a = 0; a < major; a++) {
          const base = horizontal ? a * w * 4 : a * 4;
          for (let channel = 0; channel < 3; channel++) {
            let sum = 0;
            for (let i = -radius; i <= radius; i++) sum += input[base + Math.max(0, Math.min(minor - 1, i)) * step + channel];
            for (let i = 0; i < minor; i++) {
              output[base + i * step + channel] = Math.round(sum / span);
              sum += input[base + Math.min(minor - 1, i + radius + 1) * step + channel]
                - input[base + Math.max(0, i - radius) * step + channel];
            }
          }
          for (let i = 0; i < minor; i++) output[base + i * step + 3] = 255;
        }
        [input, output] = [output, input];
      }
    }
    image.data.set(input); return image;
  }
  function render(source, regions) {
    const w = source.width, h = source.height;
    const normalized = regions.map(r => {
      if (r.method !== 'secure' && r.method !== 'blur') throw new Error('Unknown masking method');
      const box = rect(r, w, h);
      return box ? { ...box, method: r.method, radius: Math.max(2, Math.min(30, Math.round(r.radius || 10))) } : null;
    }).filter(Boolean);
    const secure = normalized.filter(r => r.method === 'secure');
    const sanitized = canvas(w, h), sc = sanitized.getContext('2d', { willReadFrequently: true });
    // Flatten transparency as well as removing selected pixels.
    sc.fillStyle = '#ffffff'; sc.fillRect(0, 0, w, h); sc.drawImage(source, 0, 0);
    cover(sc, secure);
    const output = canvas(w, h), ctx = output.getContext('2d'); ctx.drawImage(sanitized, 0, 0);
    const blur = normalized.filter(r => r.method === 'blur').sort((a, b) => a.y - b.y || a.x - b.x || a.h - b.h || a.w - b.w || a.radius - b.radius);
    for (const r of blur) ctx.putImageData(soften(sc.getImageData(r.x, r.y, r.w, r.h), r.radius), r.x, r.y);
    // Secure masks take precedence, including when a blur overlaps them.
    cover(ctx, secure); sanitized.width = 0; sanitized.height = 0;
    return output;
  }
  root.BlueMaskEngine = Object.freeze({ render, rect, fill: FILL });
})(globalThis);
