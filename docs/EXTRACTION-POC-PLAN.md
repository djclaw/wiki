# Extraction PoC Plan

This is the first tiny PoC for the wiki extraction pipeline.

## Scope

Use only the most recent **7 days** of `memory/HISTORY.md` as the sample window.

Current observed sample size: **12 entries**.

This is intentionally small.
The goal is not full coverage.
The goal is to compare a schema-first extraction path against the existing rule-based baseline.

## Why this scope

- small enough to inspect manually
- recent enough to reflect current project language
- diverse enough to include projects, tools, publishing, and architecture work
- low risk for first-pass iteration

## PoC objective

From each selected history entry, extract candidate structured objects:

- `evidence`
- `nodes`
- `relations`
- `events`

The PoC should preserve source grounding and remain reviewable.

## What we will not do in PoC v1

- no full automatic publishing
- no automatic merge into canonical DB
- no embeddings
- no complex ontology induction
- no cross-source extraction
- no heavy optimization loop yet

## Sample strategy

Window:
- latest timestamp in `HISTORY.md`
- go back 7 days

Current expected entries include topics such as:
- trips project
- DJClaw publishing
- SeqLog / Logseq notes
- wiki kernel architecture

## Baseline

Keep the current rule-based extractor as the baseline.

Comparison dimensions:
- extracted node usefulness
- relation usefulness
- event quality
- evidence preservation
- cleanup burden

## Proposed object shape for PoC

### EvidenceRecord
- `evidence_id`
- `source_id`
- `timestamp`
- `text`

### NodeCandidate
- `label`
- `type`
- `confidence`

### RelationCandidate
- `source_label`
- `relation_type`
- `target_label`
- `confidence`

### EventCandidate
- `title`
- `timestamp`
- `summary`
- `confidence`

## Recommended implementation path

Use the current available model path with a schema-first prompt.

Implementation should be provider-light:
- separate sample selection
- separate prompt building
- separate model call
- separate JSON validation

This keeps the PoC portable if the model backend changes.

## Deliverables

- sample selection script
- PoC extraction script
- JSON output in `data/`
- quick comparison notes against baseline

## Success criteria

PoC v1 is successful if it:

- produces valid structured output for the recent sample set
- preserves evidence and timestamps
- yields more useful node/relation/event candidates than the pure rule-based baseline
- is easy to inspect manually

## Current recommendation

Proceed with:

1. recent-7-day sample selector
2. minimal schema-first extraction script
3. use Groq `llama-3.3-70b-versatile` as the default primary model
4. keep `moonshotai/kimi-k2-instruct` as the challenger model for comparison
5. write outputs to `data/extraction-poc/`
6. inspect results manually before any DB integration
