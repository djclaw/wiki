# Extraction Baseline Note

## Decision

Current default Groq primary model for the extraction PoC:

- `llama-3.3-70b-versatile`

Current Groq challenger model kept for comparison:

- `moonshotai/kimi-k2-instruct`

## Why this default

A small recent-window comparison on the same HISTORY sample showed:

- `llama-3.3-70b-versatile` was the most balanced across JSON stability, node count, relation production, and event coverage.
- `moonshotai/kimi-k2-instruct` was also stable and sometimes more conservative/natural, but tended to produce fewer relations.
- `openai/gpt-oss-120b` was stable for events but too weak on usable relations in the current pipeline.

So the current practical choice is:

- use `llama-3.3-70b-versatile` as the working default
- keep `moonshotai/kimi-k2-instruct` as the spot-check challenger

## Current baseline framing

The recent-window rule-based baseline (`baseline_recent_history_compare.py`) is still useful, but it should be treated as a floor, not a target.

It is good for:

- stable keyword spotting
- deterministic repeatability
- low cost

It is weak for:

- relation extraction
- event summarization
- typed structured candidates per entry

The model-based PoC should therefore be judged against the baseline in terms of:

1. better entity usefulness
2. better event quality
3. at least some usable relation output
4. preserved evidence for review
5. manageable cleanup burden after normalization

## Current implementation status

Already in place:

- default Groq model path points to `llama-3.3-70b-versatile`
- challenger model is documented as `moonshotai/kimi-k2-instruct`
- lightweight normalization/filtering exists in `extraction_poc.py`
- recent-window baseline JSON exists in `data/extraction-poc/baseline-recent-history.json`

Current spot-check result:

- running `python wiki/scripts/extraction_poc.py --provider groq --limit 5`
- result: 5/5 entries completed, 0 parse errors

## Immediate next work

1. continue tightening normalization and alias merge rules
2. expand comparison from 5-entry checks to the full recent window
3. keep parse errors at or near zero under Groq-default execution
4. only after that consider wiring candidate output toward canonical storage
