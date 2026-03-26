# Personal Wiki

A quiet, local-first personal wiki built on a Raspberry Pi.

It is **not** trying to rebuild Logseq as a full product.
It borrows the useful parts of the Logseq mental model — pages, blocks, links, backlinks, journal-like time structure — and combines them with a small extraction pipeline that turns personal history into a publishable wiki.

## Current Direction

This project is moving toward a **Logseq-inspired knowledge kernel**:

- **Page** for stable entities like people, places, projects, tools, and topics
- **Block / fragment** for smaller extracted facts, mentions, and evidence
- **Backlinks / related links** for navigation
- **Timeline / journal** for history-first browsing
- **Graph-ready relations** underneath, even if the UI stays minimal

The goal is a quiet personal wiki that can grow from real history logs without requiring a full note-taking app or a heavy editor.

## What Exists Now

Current repo state already includes:

- static HTML entry pages
- Wikipedia-like styling
- front-end search index
- bilingual UI framework
- rule-based extraction from `HISTORY.md`
- local SQLite build step
- generated entry pipeline foundations

## Architecture

The project now follows a layered model:

### 1. Source Layer
Inputs such as:

- `memory/HISTORY.md`
- later: notes, exports, custom files, structured records

Configured in:

- `config/sources.json`

### 2. Extraction Layer
Turns history-like text into structured candidate knowledge.

Current status:

- rule-based extraction exists
- privacy redaction exists
- JSON intermediate output exists

Main script:

- `scripts/extract_history.py`

Output:

- `data/extracted-history.json`

### 3. Canonical Data Layer
Stores normalized extracted items for local processing.

Current status:

- local SQLite DB exists for MVP3 foundation
- DB is intentionally local-only and not committed to git

Main script:

- `scripts/build_db.py`

Local DB path:

- `/home/dj/.nanobot/workspace/memory/wiki.db`

### 4. Materialization Layer
Turns structured data into browsable entry pages and search artifacts.

Main files:

- `entries/`
- `templates/`
- `scripts/generate_entries_from_db.py`
- `scripts/build_search_index.py`
- `data/search-index.json`

### 5. Front-End Layer
Minimal browse/search UI for GitHub Pages.

Main files:

- `index.html`
- `style.css`
- `search.js`
- `ui.js`
- `ui-text.json`

### 6. Review / Safety Layer
Needed to keep the wiki useful and safe.

Current status:

- privacy redaction exists in extraction
- stronger review workflow is still needed
- alias merge / correction / confidence workflow is still needed

## MVP Plan

### MVP1 — Static Wiki Foundation
Goal: a quiet, usable wiki shell.

Includes:

- static entry pages
- minimal Wikipedia-like layout
- fast search
- bilingual UI framework
- related / backlink-style navigation

### MVP2 — Structure and Browse Better
Goal: make the static wiki feel more like a real knowledge surface.

Includes:

- better entry templates
- stronger entity metadata
- improved generated search / browse experience
- cleaner related links / backlink presentation
- timeline-oriented browsing and more consistent entry generation

### MVP3 — Real Personal Data Pipeline
Goal: turn real history into local structured knowledge.

Includes:

- source config
- extraction from `HISTORY.md`
- local SQLite build
- privacy-aware local processing
- generated entries from extracted data

### MVP4 — Smarter Extraction and Review
Goal: improve quality without leaking private data.

Planned after scope is clearly defined.

Includes:

- clearer inclusion boundaries
- LLM + rules extraction pipeline
- stronger privacy filters
- human review / audit workflow
- canonical entity schema improvements

## Why Logseq-Inspired Instead of Logseq-Itself

Using Logseq as inspiration is a good fit.
Using Logseq as the whole product engine is not necessary for this repo.

Why:

- this project is history-first, not editor-first
- the hard problem here is extraction and normalization, not block editing
- the target output is a public/static wiki, not a full local PKM app
- a smaller custom pipeline is easier to control on a Raspberry Pi

So the project takes the **concept kernel**, not the whole application burden.

## Key Docs

- `docs/ARCHITECTURE.md` — layered technical architecture
- `docs/MINIMAL-SCHEMA.md` — minimal schema for the wiki kernel
- `docs/EXTRACTION-DESIGN.md` — extraction strategy, tool options, MVP path, and PoC plan
- `docs/PROJECT.md` — short project overview

## Current local pipeline

The local kernel pipeline now runs like this:

1. `python3 scripts/extract_history.py`
2. `python3 scripts/build_kernel_json.py`
3. `python3 scripts/build_db.py`

This rebuilds the local-only SQLite database using the new kernel schema:
- `sources`
- `evidence`
- `nodes`
- `relations`
- `events`

## Repository Structure

- `index.html` — home / search entry
- `entries/` — entity pages
- `data/search-index.json` — front-end search index
- `data/extracted-history.json` — extracted intermediate data
- `scripts/extract_history.py` — rule-based history extraction
- `scripts/build_db.py` — local SQLite build
- `scripts/generate_entries_from_db.py` — entry generation
- `scripts/build_search_index.py` — search index generation
- `templates/` — page templates
- `config/sources.json` — source configuration
- `docs/PROJECT.md` — short public project overview

## Local Development

### Rebuild extracted history
```bash
python3 scripts/extract_history.py
```

### Build local DB
```bash
python3 scripts/build_db.py
```

### Rebuild search index
```bash
python3 scripts/build_search_index.py
```

### Generate entries from DB
```bash
python3 scripts/generate_entries_from_db.py
```

## Privacy

Sensitive data should not go to GitHub.

Rules:

- keep SQLite local-only
- avoid publishing raw private history
- redact keys, secrets, tokens, emails, and sensitive paths
- add stronger review before broader automated publishing

## Publishing

This repo is intended for GitHub Pages (`main` branch / root).
The publishable layer should remain static and privacy-filtered.
