# Minimal Schema for the Wiki Kernel

This document defines the smallest useful schema for the next phase of the wiki.

The goal is not maximum elegance.
The goal is to support MVP2 + MVP3 with the least complexity that still keeps future graph growth possible.

## Design principles

1. **Entity-first for public pages**
   Public wiki pages are still mainly entity pages.

2. **Evidence-first for trust**
   Every extracted fact should be traceable to a source snippet or event line.

3. **Relation-ready underneath**
   Even if the UI stays simple, the data should be able to say that one thing is connected to another.

4. **Local-first safety**
   Canonical and review layers stay local. Only filtered/static material is published.

## Core object types

### 1. SourceDocument
Represents an ingested source.

Fields:
- `source_id` — stable ID like `history_md`
- `source_type` — `history_md`, `notes_dir`, `csv`, etc.
- `path` — local path
- `display_name` — human-readable label
- `ingested_at` — timestamp

### 2. Evidence
A concrete span or event from a source.

Fields:
- `evidence_id`
- `source_id`
- `timestamp` — if present in the source
- `raw_text`
- `redacted_text`
- `publishable` — boolean
- `confidence` — optional float later

### 3. Node
A canonical thing that may become a page.

Fields:
- `node_id` — stable slug-like ID
- `node_type` — one of:
  - `person`
  - `project`
  - `tool`
  - `place`
  - `topic`
  - `event`
  - `org`
  - `doc`
- `title`
- `summary`
- `aliases` — list
- `tags` — list
- `categories` — list for page/UI compatibility
- `status` — `candidate`, `canonical`, `hidden`, `merged`
- `visibility` — `public`, `private`, `review`

### 4. Relation
A directional edge between nodes.

Fields:
- `relation_id`
- `from_node`
- `to_node`
- `relation_type`
- `weight` — optional integer/count
- `evidence_ids` — list
- `status` — `candidate` or `canonical`

Recommended early `relation_type` set:
- `related_to`
- `mentioned_with`
- `works_on`
- `uses`
- `located_in`
- `about`

### 5. MentionEvent
A timeline-friendly event that can appear in pages.

Fields:
- `event_id`
- `timestamp`
- `summary`
- `node_ids`
- `evidence_id`
- `source_id`

## Minimal JSON intermediate shape

For extraction output, the next useful shape is:

```json
{
  "sources": [],
  "evidence": [],
  "nodes": [],
  "relations": [],
  "events": []
}
```

## Minimal SQLite direction

Current DB has one `entries` table.

The next small step should be five tables:

- `sources`
- `evidence`
- `nodes`
- `relations`
- `events`

This is enough for MVP2 + MVP3 without overbuilding.

## Page generation model

Each public page still maps mainly to one `Node`.

Suggested generated sections:
- Overview
- Timeline
- Related
- Evidence / Sources
- Aliases / Metadata

## What stays out for now

Not needed yet:
- full block editor
- live graph canvas
- complex ontology
- multi-hop reasoning layer
- automatic public publishing of everything
- heavy ranking systems

## Mapping from current extraction

Current `extracted-history.json` objects are roughly entry-shaped:
- `title`
- `summary`
- `timeline`
- `related`
- `aliases`
- `source`
- `source_id`

The next bridge step is:
- `title` -> `Node.title`
- `aliases` -> `Node.aliases`
- `timeline[]` -> `MentionEvent[]`
- `related[]` -> candidate `Relation[]`
- source fields -> `SourceDocument`

## B implementation target

The B-phase should do three modest things:

1. write this minimal schema down clearly
2. add a bridge script that converts current extracted JSON into kernel-shaped JSON
3. keep the existing static pipeline working while the new kernel grows underneath

That way the wiki keeps moving without a full rewrite.
