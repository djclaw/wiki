#!/usr/bin/env python3
"""
Extracts tool/project entities from HISTORY.md into a JSON list.
Rule-based only (no LLM). Includes privacy redaction.
"""
import json
import re
from collections import defaultdict, Counter
from pathlib import Path

HISTORY_PATH = Path("/home/dj/.nanobot/workspace/memory/HISTORY.md")
OUTPUT_JSON = Path("/home/dj/.nanobot/workspace/wiki/data/extracted-history.json")

TOOL_KEYWORDS = {
    "git",
    "github",
    "gh",
    "sqlite",
    "python",
    "node",
    "npm",
    "telegram",
    "email",
    "imap",
    "smtp",
    "cron",
    "tavily",
    "humanizer",
    "summarize",
    "clawhub",
    "nanobot",
    "codex",
    "gemini",
    "gemma",
    "groq",
    "openai",
    "mcp",
    "langgraph",
    "autogen",
    "claude",
}

CANONICAL = {
    "djclaw.github.io": "djclaw.github.io",
    "github": "GitHub",
    "gh": "GitHub CLI",
    "npm": "npm",
    "node": "Node.js",
    "sqlite": "SQLite",
    "telegram": "Telegram",
    "email": "Email",
    "imap": "IMAP",
    "smtp": "SMTP",
    "cron": "cron",
    "tavily": "Tavily",
    "humanizer": "humanizer",
    "summarize": "summarize",
    "clawhub": "ClawHub",
    "nanobot": "nanobot",
    "codex": "Codex",
    "gemini": "Gemini",
    "gemma": "Gemma",
    "groq": "Groq",
    "openai": "OpenAI",
    "mcp": "MCP",
    "langgraph": "LangGraph",
    "autogen": "AutoGen",
    "claude": "Claude",
}

SENSITIVE_PATTERNS = [
    r"(?i)\b(api[_-]?key|access[_-]?token|token|secret|password|passwd|pat)\b\s*[:=]\s*\S+",
    r"(?i)\b(GITHUB_API_KEY|OPENAI_API_KEY|GEMINI_API_KEY|TAVILY_API_KEY|GROQ_API_KEY)\b\s*[:=]?\s*\S+",
    r"(?i)\bbearer\s+[a-z0-9\-\._]{10,}",
    r"(?i)[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}",
    r"(?i)\b(ssh-rsa|ssh-ed25519)\s+[A-Za-z0-9+/=]+",
    r"\b[A-Za-z0-9+/=]{32,}\b",
]

PATH_PATTERN = re.compile(r"/home/[^\s]+")


def redact(text: str) -> str:
    text = PATH_PATTERN.sub("[REDACTED_PATH]", text)
    for pat in SENSITIVE_PATTERNS:
        text = re.sub(pat, "[REDACTED]", text)
    return text


def first_sentence(text: str) -> str:
    text = text.strip()
    if not text:
        return ""
    parts = re.split(r"[。！？.!?]\s+", text, maxsplit=1)
    return parts[0].strip()


def normalize_entity(name: str) -> str:
    raw = name.strip().strip("`'\"“”")
    raw = re.sub(r"[\.,;:!\)\]]+$", "", raw)
    key = raw.lower()
    if key in CANONICAL:
        return CANONICAL[key]
    return raw


def classify_entity(name: str) -> str:
    key = name.lower()
    if key in TOOL_KEYWORDS or key in CANONICAL:
        return "tool"
    return "project"


def extract_entities(text: str):
    entities = []
    lower = text.lower()

    # domain-like projects
    for m in re.findall(r"\b[\w\-]+\.github\.io\b", lower):
        entities.append(normalize_entity(m))

    # keyword-based tools
    for kw in TOOL_KEYWORDS:
        if re.search(rf"\b{re.escape(kw)}\b", lower):
            entities.append(normalize_entity(kw))

    # pattern: X skill/repo/project/site/blog/wiki
    pattern = re.compile(r"([A-Za-z0-9\._\-]+)\s+(skill|repo|repository|project|site|blog|wiki)", re.I)
    for m in pattern.finditer(text):
        candidate = m.group(1)
        if candidate.startswith("/") or "/home/" in candidate:
            continue
        entities.append(normalize_entity(candidate))

    # backticked tokens
    for m in re.findall(r"`([^`]+)`", text):
        token = m.strip()
        if token.startswith("/") or "/home/" in token:
            continue
        if len(token) > 60:
            continue
        if re.search(r"\s", token):
            continue
        entities.append(normalize_entity(token))

    # de-dup, keep order
    seen = set()
    clean = []
    for e in entities:
        if not e or e in seen:
            continue
        seen.add(e)
        clean.append(e)

    return clean[:6]


def extract_blocks(history_text: str):
    blocks = re.split(r"\n\s*\n", history_text.strip())
    ts_pattern = re.compile(r"^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2})\]\s*(.*)")
    for block in blocks:
        block = block.strip()
        if not block or block.startswith("#"):
            continue
        first_line = block.splitlines()[0].strip()
        match = ts_pattern.match(first_line)
        if not match:
            continue
        ts, rest = match.groups()
        body_lines = block.splitlines()[1:]
        body = (rest + "\n" + "\n".join(body_lines)).strip()
        yield ts, body


def build_entities(history_text: str):
    entity_events = defaultdict(list)
    related_counts = defaultdict(Counter)
    entity_type = {}

    for ts, body in extract_blocks(history_text):
        body = redact(body)
        entities = extract_entities(body)
        if not entities:
            continue
        sentence = first_sentence(body)
        if not sentence:
            sentence = body[:120].strip()
        event = f"{ts} — {sentence}"

        for e in entities:
            entity_events[e].append(event)
            entity_type[e] = classify_entity(e)
            for other in entities:
                if other != e:
                    related_counts[e][other] += 1

    items = []
    for title, events in entity_events.items():
        overview = " / ".join([e.split(" — ", 1)[-1] for e in events[:2] if e])
        related = [name for name, _ in related_counts[title].most_common(10)]
        category = "Tool" if entity_type.get(title) == "tool" else "Project"

        items.append(
            {
                "title": title,
                "summary": overview,
                "timeline": events[:10],
                "tags": [],
                "categories": [category],
                "aliases": [title.lower()],
                "related": related,
                "source": "history",
                "source_id": "history_md",
            }
        )

    return items


def main():
    history_text = HISTORY_PATH.read_text(encoding="utf-8")
    items = build_entities(history_text)
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(items)} items to {OUTPUT_JSON}")


if __name__ == "__main__":
    main()
