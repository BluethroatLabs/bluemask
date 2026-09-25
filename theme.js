(function () {
  'use strict';
  const key = 'bluemask-theme';
  const root = document.documentElement;
  const button = document.getElementById('theme');
  const themeColor = document.querySelector('meta[name="theme-color"]');

  function apply(value, persist) {
    const light = value === 'light';
    root.classList.toggle('light', light);
    document.body.classList.toggle('light', light);
    if (themeColor) themeColor.content = light ? '#fafafa' : '#0a0a0a';
    if (button) {
      const label = light ? 'Switch to dark appearance' : 'Switch to light appearance';
      button.setAttribute('aria-label', label);
      button.title = label;
    }
    if (persist) {
      try { localStorage.setItem(key, light ? 'light' : 'dark'); } catch (_) {}
    }
  }

  apply(root.classList.contains('light') ? 'light' : 'dark', false);
  if (button) button.onclick = () => apply(root.classList.contains('light') ? 'dark' : 'light', true);
})();
