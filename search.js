const input = document.getElementById('q');
const results = document.getElementById('results');

let index = [];

fetch('data/search-index.json')
  .then((res) => res.json())
  .then((data) => {
    index = data;
    render(index);
  })
  .catch(() => {
    results.innerHTML = '<li>Search index not loaded.</li>';
  });

function render(items) {
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

function filterIndex(query) {
  if (!query) return index;
  const q = query.toLowerCase();
  return index.filter((item) => {
    return (
      item.title.toLowerCase().includes(q) ||
      (item.snippet && item.snippet.toLowerCase().includes(q))
    );
  });
}

input.addEventListener('input', (event) => {
  const query = event.target.value.trim();
  render(filterIndex(query));
});
