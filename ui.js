(function () {
  const DEFAULT_LANG = 'en';
  const STORAGE_KEY = 'wiki_lang';
  const TEXT_PATH = '/wiki/ui-text.json';

  function getLangFromUrl() {
    const params = new URLSearchParams(window.location.search);
    return params.get('lang');
  }

  function setLangInUrl(lang) {
    const url = new URL(window.location.href);
    url.searchParams.set('lang', lang);
    history.replaceState({}, '', url.toString());
  }

  function applyI18n(texts, lang) {
    const dict = texts[lang] || texts[DEFAULT_LANG] || {};
    window.UI_TEXT = dict;
    window.UI_LANG = lang;

    document.querySelectorAll('[data-i18n]').forEach((el) => {
      const key = el.getAttribute('data-i18n');
      if (dict[key]) {
        el.textContent = dict[key];
      }
    });

    document.querySelectorAll('[data-i18n-attr]').forEach((el) => {
      const raw = el.getAttribute('data-i18n-attr');
      raw.split(',').forEach((pair) => {
        const [attr, key] = pair.split(':').map((s) => s.trim());
        if (attr && key && dict[key]) {
          el.setAttribute(attr, dict[key]);
        }
      });
    });

    document.querySelectorAll('a[data-lang]').forEach((el) => {
      const target = el.getAttribute('data-lang');
      const url = new URL(window.location.href);
      url.searchParams.set('lang', target);
      el.href = url.pathname + url.search + url.hash;
    });

    document.querySelectorAll('a[href]').forEach((el) => {
      const href = el.getAttribute('href');
      if (!href || href.startsWith('http') || href.startsWith('mailto:') || href.startsWith('#')) {
        return;
      }
      if (href.includes('lang=')) return;
      const url = new URL(href, window.location.origin + window.location.pathname);
      url.searchParams.set('lang', lang);
      el.setAttribute('href', url.pathname + url.search + url.hash);
    });
  }

  function init() {
    const urlLang = getLangFromUrl();
    const savedLang = localStorage.getItem(STORAGE_KEY);
    const lang = urlLang || savedLang || DEFAULT_LANG;

    fetch(TEXT_PATH)
      .then((res) => res.json())
      .then((texts) => {
        applyI18n(texts, lang);
        setLangInUrl(lang);
        localStorage.setItem(STORAGE_KEY, lang);
        document.dispatchEvent(new CustomEvent('ui-text-ready'));
      })
      .catch(() => {
        window.UI_TEXT = {};
        window.UI_LANG = lang;
      });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
