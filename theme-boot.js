try {
  if (localStorage.getItem('bluemask-theme') === 'light') document.documentElement.classList.add('light');
} catch (_) {}
