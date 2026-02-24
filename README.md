# Personal Wiki

A lightweight, static personal Wikipedia powered by a local knowledge graph.

## Structure
- `index.html` — entry index + search
- `entries/` — entity pages (one per entry)
- `data/search-index.json` — search index for the front-end
- `scripts/build_search_index.py` — generates the search index
- `style.css` — minimal Wikipedia-like theme
- `templates/` — base HTML templates

## Add a New Entry
1) Create a new file under `entries/` (e.g. `entries/your-entity.html`).
2) Use the existing entry pages as a template.
3) Optional metadata (for search):
   - `data-tags="a,b,c"`
   - `data-categories="x,y"`
   - `data-aliases="alt name,short"`
   - `data-related="other entity,another"`
   - `data-lat="40.7128"` / `data-lon="-74.0060"`
4) Regenerate the index:
   ```bash
   python3 scripts/build_search_index.py
   ```

## Publishing
This repo is intended to be published via GitHub Pages (main branch / root).
