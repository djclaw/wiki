# Extraction Design

A practical design note for the next phase of the wiki extraction pipeline.

This document answers a narrower question than the overall architecture docs:

**How should this project extract useful structured knowledge from personal history and similar sources without turning into a fragile pile of prompts?**

The short answer:

- do not treat extraction as generic summarization
- do not rely on one-shot ad hoc prompts
- define the kernel shape first
- use schema-first structured extraction
- keep normalization, review, and publishing as separate layers

---

## 1. Goal

The goal of extraction is not merely to produce text.

The goal is to turn local source material into **kernel-shaped candidate knowledge** that can later be:

- reviewed
- normalized
- merged
- stored locally
- materialized into static wiki pages

This means extraction should aim to produce:

- evidence
- nodes
- relations
- events
- aliases / merge suggestions

rather than just summaries.

---

## 2. What extraction should do

For this repo, extraction should eventually answer questions like:

- What people, projects, tools, places, orgs, and topics appear in the source?
- What happened, and when?
- Which things are related to each other?
- What source evidence supports each extracted item?
- Is the item public, private, or review-only?
- Does this look like a new canonical node, or an alias/duplicate of an existing one?

This is closer to a **local knowledge pipeline** than a normal LLM summary task.

---

## 3. Inputs

### Current input
- `memory/HISTORY.md`

### Near-future inputs
- notes directories
- markdown files
- exports
- project docs
- issue / task records
- selected structured files

### Unified source adapter shape

Every raw input should first become a normalized source record with fields like:

- `source_id`
- `source_type`
- `chunk_id`
- `timestamp` if available
- `raw_text`
- `path`
- `metadata`

This keeps extraction independent from any one file format.

---

## 4. Non-goals

Not part of MVP extraction:

- rebuilding a full PKM editor
- perfect automatic ontology induction
- fully automatic public publishing
- extracting every possible latent idea from text
- replacing review with confidence theater

The extraction layer should stay modest and traceable.

---

## 5. Design principles

### 5.1 Schema-first
Extraction should target explicit typed objects, not free-form prose.

### 5.2 Evidence-first
Every extracted fact should remain tied to source evidence.

### 5.3 Kernel-oriented
Extraction should produce objects that can directly enter the wiki kernel.

### 5.4 Local-first
Raw private inputs and local review state should remain local.

### 5.5 Reviewable
The system should preserve uncertainty instead of pretending to know too much.

### 5.6 Layered, not magical
Extraction, normalization, and publication should remain separate steps.

---

## 6. Target extraction objects

This should align with `docs/MINIMAL-SCHEMA.md`.

### 6.1 Source
Represents the ingested document or chunk origin.

### 6.2 Evidence
The concrete raw or redacted snippet supporting a candidate fact.

### 6.3 NodeCandidate
A possible canonical page entity.

Expected early node types:
- `person`
- `project`
- `tool`
- `place`
- `topic`
- `org`
- `doc`

### 6.4 RelationCandidate
A possible directional relation between nodes.

Expected early relation types:
- `related_to`
- `mentioned_with`
- `works_on`
- `uses`
- `located_in`
- `about`

### 6.5 EventCandidate
A timeline-friendly event or mention event.

### 6.6 AliasCandidate / MergeSuggestion
A proposed link between a new extracted label and an existing canonical node.

This object is important because extraction quality depends heavily on normalization, not just first-pass parsing.

---

## 7. Proposed pipeline layers

### Layer 0 — Source adapters
Turn files / logs / exports into normalized text chunks.

Output shape example:

```json
{
  "source_id": "history_md",
  "source_type": "history_md",
  "chunk_id": "history_md:2026-03-25:001",
  "timestamp": "2026-03-25T10:24:00",
  "raw_text": "...",
  "path": "memory/HISTORY.md",
  "metadata": {}
}
```

### Layer 1 — Structured extraction
Use LLM + schema or rules to produce typed candidates.

This layer should output candidate objects, not final published pages.

### Layer 2 — Normalization / canonicalization
Resolve:
- aliases
- duplicate entities
- title normalization
- relation cleanup
- visibility defaults

This layer should use a mix of:
- rules
- alias dictionaries
- string matching
- embeddings later if useful
- LLM adjudication when necessary

### Layer 3 — Review / safety
Decide:
- publishable vs review-only
- confidence
- ambiguity flags
- privacy / sensitivity concerns
- merge conflicts

### Layer 4 — Canonical local storage
Store reviewed/normalized items in local JSON + SQLite.

### Layer 5 — Materialization
Generate:
- entry pages
- related links
- timeline sections
- search artifacts

---

## 8. Candidate tool landscape

The practical question is not “what single plugin solves extraction?”
It is “what tools are worth borrowing for a strong layered pipeline?”

### 8.1 Instructor
Best early candidate for structured extraction.

Why it fits:
- schema-first
- Pydantic-based
- validation and retry
- works well in Python
- good fit for candidate object extraction

Best use here:
- first production-grade LLM extraction layer
- event / node / relation / evidence extraction into typed models

### 8.2 Outlines
Good candidate when output constraints become stricter.

Why it fits:
- grammar / constrained generation
- stronger enum and shape control

Best use here:
- later stage when ontology is stable and invalid outputs become costly

### 8.3 BAML
Good candidate for multi-step LLM workflow engineering.

Why it fits:
- treats prompts/functions more like software modules
- supports more maintainable LLM pipelines
- useful when extraction becomes a multi-stage system

Best use here:
- after the extraction flow gets more complex than one or two calls

### 8.4 DSPy
Useful for optimization, not first implementation.

Why it fits:
- good for prompt/program optimization
- good when eval sets exist

Best use here:
- after gold examples and eval metrics exist

### 8.5 LlamaIndex Property Graph ideas
Very relevant as a graph-shaped extraction reference.

Why it fits:
- matches the node/relation/event direction
- offers schema-aware graph extraction patterns

Best use here:
- reference design for graph extraction and ontology-aware path extraction

### 8.6 GraphRAG
Important architectural reference, but probably not the first implementation layer.

Why it fits:
- thinks in terms of graph extraction + summaries + retrieval
- good for large narrative corpora

Best use here:
- long-range architecture reference, not MVP extraction core

---

## 9. Current recommendation

### Near-term recommendation
Use:
- current rule-based pipeline as baseline
- `Instructor` as the first structured LLM extraction candidate
- existing kernel schema as the target shape

### Why
Because this path is:
- practical
- local-friendly
- Python-friendly
- easy to compare with the existing extraction output
- much lighter than adopting a whole new framework stack too early

---

## 10. MVP extraction plan

### MVP-E1 — Clear target schema
Before expanding the extraction logic further, ensure that the target object types are stable enough:
- evidence
- node candidate
- relation candidate
- event candidate
- alias / merge suggestion

### MVP-E2 — Structured extraction PoC
Run a small LLM-based extraction experiment on a small set of `HISTORY.md` samples.

Goals:
- compare with current rule-based output
- measure usefulness, not perfection
- inspect privacy and review risks early

### MVP-E3 — Normalization pass
Add a narrow normalization layer for:
- obvious aliases
- title cleanup
- duplicate candidate merge hints
- visibility defaults

### MVP-E4 — Review surface
Create a local review step before anything enters public materialization.

---

## 11. Proposed PoC scope

The first PoC should stay deliberately small.

### Input size
- 10 to 30 selected history entries

### Proposed tasks
- extract candidate nodes
- extract candidate relations
- extract mention events
- preserve evidence mapping

### Proposed comparison
Compare:
- current rule-based extractor
- structured LLM extractor

### Success criteria
The PoC is successful if it shows that the LLM-based extractor can:
- produce cleaner typed output
- capture more useful entities and relations
- preserve evidence links
- remain reviewable
- avoid obvious privacy regressions

The PoC does **not** need to prove full automation.

---

## 12. Evaluation criteria

Useful early evaluation dimensions:

### Precision of extracted nodes
Are the extracted entities mostly real and useful?

### Relation usefulness
Do the relations help the wiki, or are they noisy?

### Event quality
Are the timeline events understandable and source-grounded?

### Alias burden
How much cleanup is still needed after extraction?

### Review burden
Does the output save time, or just create another mess to clean?

### Privacy safety
Does the extraction surface private or sensitive details too aggressively?

---

## 13. Risks

### Risk 1 — Generic summarization disguised as extraction
This produces pretty text but weak structured data.

### Risk 2 — Over-automation too early
This creates hidden mistakes and messy canonical data.

### Risk 3 — No evidence links
Without evidence, the wiki becomes hard to trust or correct.

### Risk 4 — Alias explosion
The graph will fragment if normalization is weak.

### Risk 5 — Publishing layer too close to raw extraction
Public pages should not be generated directly from unreviewed raw candidates.

---

## 14. Immediate next steps

1. keep the current rule-based extractor as baseline
2. define the first extraction Pydantic models
3. choose a small `HISTORY.md` sample set
4. build a tiny `Instructor`-based PoC
5. compare outputs and write down findings

---

## 15. Practical conclusion

The right next move is:

**design doc first, PoC second**

And the most practical near-term implementation path is:

**rule-based baseline + schema-first structured extraction + normalization + review**

not:

**one giant magical extraction step**

That keeps the wiki small, local-first, and extensible.
