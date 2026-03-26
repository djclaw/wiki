# Extraction Comparison Notes

## Scope

Recent 7-day HISTORY window only.

## Current model path

- **Default Groq primary:** `llama-3.3-70b-versatile`
- **Groq backup challenger:** `moonshotai/kimi-k2-instruct`
- Gemini remains useful for comparison, but the current primary working direction for the PoC is now Groq-first.
- `gemini-2.5-pro` is still effectively blocked by free-tier quota in this environment.

## A. Parse error diagnosis

The earlier 5 parse errors were **not** JSON-format failures.
They were Gemini HTTP `429` quota failures.

Later, when switching to `gemini-2.5-pro`, all requests failed with `429`, so that path is not currently usable in this environment.

Conclusion:
- parser is mostly fine
- immediate stability issue is provider quota, not local schema parsing

## B. Normalization changes added

Added lightweight normalization and filtering in the PoC extractor:

- map `djclaw.github.io` / `djclaw site` -> `DJClaw`
- map `trips project` -> `trips`
- map `github project` -> `GitHub Projects`
- force `DJClaw` to `project`
- force `GitHub`, `GitHub Pages`, `GitHub Projects`, `Airbnb` to `org`
- force `New Orleans` to `place`
- force `Logseq`, `SeqLog`, `Leaflet`, `OpenStreetMap` to `tool`
- filter low-value fragments like `MVP1`, `MVP2`, `pages mvp2`, generic `post`, `file`, `repo`, hashes, filenames

## C. Baseline comparison approach

The existing `extract_history.py` output is a **global full-history aggregate view**, not a direct per-entry recent-window baseline. So it is not a clean apples-to-apples comparator for the PoC.

To fix this, a new lightweight comparator was added for the recent 7-day window only:

- `scripts/baseline_recent_history_compare.py`
- output: `data/extraction-poc/baseline-recent-history.json`

This baseline is intentionally simple and keyword-based.
It is useful mainly as a floor, not as a target.

## Current takeaway

Rule-based recent-window extraction is good at:
- stable keyword spotting
- deterministic repeatability
- low cost

Model-based PoC is better positioned for:
- event summaries
- relation candidates
- more useful structured objects per entry

But model-based extraction still needs:
- quota-aware execution
- stronger normalization
- optional batching or backoff
- eventual review loop before DB merge

## Recommended next step

1. keep PoC default on Groq `llama-3.3-70b-versatile`
2. keep `moonshotai/kimi-k2-instruct` as challenger for spot checks
3. keep tightening parse-error handling and normalization
4. compare Groq-primary output against the recent-window baseline
5. only then decide whether to widen beyond 7 days

## D. Normalization v2 + gentle abstraction tightening (13-entry rerun)

A second tightening pass was completed on the same recent 13-entry comparison window.

What changed:
- broader alias normalization for DJClaw / GitHub / model names / OpenStreetMap variants
- additional removal of low-value config/doc-name noise such as environment-key-like tokens and note-file labels
- gentle abstract-node suppression for words like `comparison`, `listing`, `confirmed`, `explained`, `refine`, `personal`
- explicit protection for still-valuable architecture/project nodes like `wiki`, `wiki pipeline`, `Wiki extraction PoC`

Observed result on the same 13 entries:
- parse errors: `0`
- nodes total: `53`
- unique node labels: `28`
- events total: `21`
- relations total: `0`

Interpretation:
- this pass reduced noise slightly without materially shrinking event coverage
- the system does **not** appear over-tightened yet
- remaining output is still a little broad, but more page-worthy than the prior pass

Current judgment:
- normalization v2 was worth doing
- one gentle abstraction pass was worth doing
- do **not** aggressively tighten further until DB-merge behavior and daily-ingestion behavior are tested on live updates
