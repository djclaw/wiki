# Wiki Architecture

A quiet personal wiki with a Logseq-inspired inner model.

This project is best understood as a **small knowledge pipeline** rather than just a static site.

## Core idea

Borrow the useful grammar from Logseq:

- page
- block / fragment
- link
- backlink
- timeline / journal
- graph-ready relations

But do **not** turn this repo into a full note-taking product.

The custom value of this project is elsewhere:

- ingesting personal source material
- extracting candidate knowledge
- normalizing it locally
- materializing it into a static, privacy-aware wiki

## Layers

### 1. Source layer
Raw inputs.

Current:
- `memory/HISTORY.md`

Future:
- notes
- exports
- issue/project data
- custom files

Config:
- `config/sources.json`

### 2. Extraction layer
Transforms raw text into candidate knowledge.

Current output shape is still entry-first.
The target shape should become:

- nodes
- relations
- evidence
- mentions/events

Current script:
- `scripts/extract_history.py`

### 3. Canonical data layer
Stores normalized local knowledge.

Current:
- local SQLite at `/home/dj/.nanobot/workspace/memory/wiki.db`

This layer should gradually separate:
- canonical nodes
- aliases
- relations
- evidence spans
- source documents

### 4. Materialization layer
Turns canonical data into publishable pages.

Current scripts:
- `scripts/generate_entries_from_db.py`
- `scripts/build_search_index.py`

Outputs:
- `entries/`
- `data/search-index.json`

### 5. Front-end layer
A minimalist static browse/search shell.

Main files:
- `index.html`
- `style.css`
- `search.js`
- `entity.js`

### 6. Review / safety layer
Keeps the system useful and safe.

Needs to govern:
- privacy redaction
- publishability
- confidence / ambiguity
- alias merge and correction
- manual review before publication

## MVP framing

### MVP1 — Static foundation
- static entry pages
- minimal layout
- search
- calm browse shell

### MVP2 — Better structure and browse
- stronger page template
- clearer page sections
- better metadata and related links
- timeline-oriented browsing

### MVP3 — Real local knowledge pipeline
- source config
- extraction from personal history
- local DB
- generated pages from real data

### MVP4 — Smarter extraction and review
- LLM + rules
- stronger privacy workflow
- confidence and validation
- better entity schema

## Practical rule

**Do not rebuild Logseq.**

Use a Logseq-inspired grammar to turn history into a calm personal wiki.
