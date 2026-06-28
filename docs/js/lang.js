/* Language switcher for China Pinginsider */
(function() {
  const LS_KEY = 'pinginsider_lang';
  const currentLang = localStorage.getItem(LS_KEY) || 'en';

  function applyLang(lang) {
    // Toggle all lang-en and lang-fr elements
    document.querySelectorAll('.lang-en, .lang-fr').forEach(function(el) {
      el.classList.toggle('active', el.classList.contains('lang-' + lang));
    });
    // Update lang switch buttons
    document.querySelectorAll('.lang-switch').forEach(function(el) {
      el.classList.toggle('active', el.dataset.lang === lang);
    });
    // Set html lang attribute
    document.documentElement.lang = lang;
    localStorage.setItem(LS_KEY, lang);
  }

  // Apply saved language on load
  applyLang(currentLang);

  // Bind click handlers
  document.querySelectorAll('.lang-switch').forEach(function(el) {
    el.addEventListener('click', function(e) {
      e.preventDefault();
      applyLang(el.dataset.lang);
    });
  });
})();
