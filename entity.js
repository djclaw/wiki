(function () {
  const relatedList = document.getElementById('related-list');
  const backlinksList = document.getElementById('backlinks-list');
  if (!relatedList && !backlinksList) return;

  const article = document.querySelector('article.entity');
  const title = article ? article.getAttribute('data-title') : null;

  function normalize(value) {
    return (value || '').trim().toLowerCase();
  }

  function renderList(listEl, items) {
    if (!listEl) return;
    if (!items.length) {
      listEl.innerHTML = '<li>—</li>';
      return;
    }
    listEl.innerHTML = items
      .map((item) => {
        if (item.url) {
          return `<li><a href="${item.url}">${item.title}</a></li>`;
        }
        return `<li>${item.title}</li>`;
      })
      .join('');
  }

  fetch('/wiki/data/search-index.json')
    .then((res) => res.json())
    .then((data) => {
      if (!title) return;
      const current = data.find((item) => normalize(item.title) === normalize(title));
      const aliases = current && Array.isArray(current.aliases) ? current.aliases.map(normalize) : [];

      const relatedNames = current && Array.isArray(current.related) ? current.related : [];
      const relatedItems = relatedNames.map((name) => {
        const match = data.find((item) => normalize(item.title) === normalize(name) || (Array.isArray(item.aliases) && item.aliases.map(normalize).includes(normalize(name))));
        if (match) return match;
        return { title: name };
      });

      const backlinks = data.filter((item) => {
        if (!Array.isArray(item.related)) return false;
        return item.related.some((rel) => {
          const relNorm = normalize(rel);
          return relNorm === normalize(title) || aliases.includes(relNorm);
        });
      });

      renderList(relatedList, relatedItems);
      renderList(backlinksList, backlinks);
    })
    .catch(() => {
      renderList(relatedList, []);
      renderList(backlinksList, []);
    });
})();
