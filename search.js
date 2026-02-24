const input = document.getElementById('q');
const results = document.getElementById('results');
const tagFilter = document.getElementById('tag-filter');
const categoryFilter = document.getElementById('category-filter');
const clearFiltersBtn = document.getElementById('clear-filters');

let index = [];
let currentQuery = '';

function getUIText(key, fallback) {
  if (window.UI_TEXT && window.UI_TEXT[key]) {
    return window.UI_TEXT[key];
  }
  return fallback || '';
}

function setSelectOptions(selectEl, values) {
  if (!selectEl) return;
  const allLabel = getUIText('filter_all', 'All');
  selectEl.innerHTML = '';
  const allOption = document.createElement('option');
  allOption.value = '';
  allOption.textContent = allLabel;
  selectEl.appendChild(allOption);
  values.forEach((value) => {
    const option = document.createElement('option');
    option.value = value;
    option.textContent = value;
    selectEl.appendChild(option);
  });
}

function render(items) {
  if (!items.length) {
    results.innerHTML = `<li>${getUIText('no_results', 'No results.')}</li>`;
    return;
  }
  results.innerHTML = items
    .map((item) => {
      return `
        <li>
          <div class="title"><a href="${item.url}">${item.title}</a></div>
          <div class="snippet">${item.snippet || ''}</div>
        </li>
      `;
    })
    .join('');
}

function matchesQuery(item, query) {
  if (!query) return true;
  const q = query.toLowerCase();
  const titleMatch = item.title && item.title.toLowerCase().includes(q);
  const snippetMatch = item.snippet && item.snippet.toLowerCase().includes(q);
  const aliasesMatch = Array.isArray(item.aliases)
    ? item.aliases.some((alias) => alias.toLowerCase().includes(q))
    : false;
  return titleMatch || snippetMatch || aliasesMatch;
}

function matchesFilter(item, filterValue, key) {
  if (!filterValue) return true;
  const values = Array.isArray(item[key]) ? item[key] : [];
  return values.some((value) => value.toLowerCase() === filterValue.toLowerCase());
}

function applyFilters() {
  const tagValue = tagFilter ? tagFilter.value : '';
  const categoryValue = categoryFilter ? categoryFilter.value : '';
  const filtered = index.filter((item) => {
    return matchesQuery(item, currentQuery) && matchesFilter(item, tagValue, 'tags') && matchesFilter(item, categoryValue, 'categories');
  });
  render(filtered);
}

function populateFilters() {
  const tags = new Set();
  const categories = new Set();
  index.forEach((item) => {
    (item.tags || []).forEach((tag) => tags.add(tag));
    (item.categories || []).forEach((cat) => categories.add(cat));
  });
  setSelectOptions(tagFilter, Array.from(tags).sort());
  setSelectOptions(categoryFilter, Array.from(categories).sort());
}

function initEvents() {
  if (input) {
    input.addEventListener('input', (event) => {
      currentQuery = event.target.value.trim();
      applyFilters();
    });
  }
  if (tagFilter) {
    tagFilter.addEventListener('change', applyFilters);
  }
  if (categoryFilter) {
    categoryFilter.addEventListener('change', applyFilters);
  }
  if (clearFiltersBtn) {
    clearFiltersBtn.addEventListener('click', () => {
      if (input) input.value = '';
      if (tagFilter) tagFilter.value = '';
      if (categoryFilter) categoryFilter.value = '';
      currentQuery = '';
      applyFilters();
    });
  }

  document.addEventListener('ui-text-ready', () => {
    populateFilters();
    applyFilters();
  });
}

fetch('/wiki/data/search-index.json')
  .then((res) => res.json())
  .then((data) => {
    index = data;
    populateFilters();
    render(index);
  })
  .catch(() => {
    results.innerHTML = `<li>${getUIText('search_index_error', 'Search index not loaded.')}</li>`;
  });

initEvents();
