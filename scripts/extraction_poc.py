#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import requests

HISTORY_PATH = Path('/home/dj/.nanobot/workspace/memory/HISTORY.md')
OUT_DIR = Path('/home/dj/.nanobot/workspace/wiki/data/extraction-poc')
SAMPLE_JSON = OUT_DIR / 'recent-history-sample.json'
OUTPUT_JSON = OUT_DIR / 'structured-candidates.json'
NANOBOT_CONFIG_PATH = Path('/home/dj/.nanobot/config.json')

ENTRY_RE = re.compile(r'^\[(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2})\]\s*(.*)$')


@dataclass
class EvidenceRecord:
    evidence_id: str
    source_id: str
    timestamp: str
    text: str


@dataclass
class NodeCandidate:
    label: str
    type: str
    confidence: float


@dataclass
class RelationCandidate:
    source_label: str
    relation_type: str
    target_label: str
    confidence: float


@dataclass
class EventCandidate:
    title: str
    timestamp: str
    summary: str
    confidence: float


@dataclass
class EntryExtraction:
    entry_id: str
    timestamp: str
    evidence: EvidenceRecord
    nodes: list[NodeCandidate] = field(default_factory=list)
    relations: list[RelationCandidate] = field(default_factory=list)
    events: list[EventCandidate] = field(default_factory=list)
    raw_response: str = ''
    parse_error: str | None = None


def load_recent_entries(days: int = 7) -> list[dict[str, Any]]:
    lines = HISTORY_PATH.read_text(encoding='utf-8', errors='ignore').splitlines()
    entries = []
    for line in lines:
        m = ENTRY_RE.match(line)
        if not m:
            continue
        dt = datetime.strptime(m.group(1) + ' ' + m.group(2), '%Y-%m-%d %H:%M')
        entries.append({
            'timestamp': dt.isoformat(timespec='minutes'),
            'text': line,
        })
    if not entries:
        return []
    latest = max(datetime.fromisoformat(e['timestamp']) for e in entries)
    cutoff = latest - timedelta(days=days)
    recent = [e for e in entries if datetime.fromisoformat(e['timestamp']) >= cutoff]
    return recent


def build_prompt(entry: dict[str, Any]) -> str:
    schema = {
        'nodes': [{'label': 'string', 'type': 'person|project|tool|place|topic|org|doc|other', 'confidence': 0.0}],
        'relations': [{'source_label': 'string', 'relation_type': 'related_to|works_on|uses|located_in|about|mentioned_with|published_to|other', 'confidence': 0.0}],
        'events': [{'title': 'string', 'timestamp': entry['timestamp'], 'summary': 'string', 'confidence': 0.0}],
    }
    return f"""You are extracting structured knowledge candidates from one personal history entry for a local wiki pipeline.
Return JSON only. No markdown. No explanation.

Rules:
- Be conservative.
- Keep only useful candidates.
- Prefer 1 to 5 nodes, 0 to 1 relations, and 1 to 2 events per entry.
- Preserve the entry timestamp for events unless the text clearly implies a different time.
- Prefer stable entities that are useful as wiki pages: projects, tools, places, orgs, topics, notable docs.
- Avoid low-value fragments like raw filenames, commit hashes, generic words like User, article, post, file, page, repo, script unless they are clearly the meaningful entity.
- Relations must be even more conservative than nodes.
- Only emit a relation when the entry states or strongly implies a concrete connection between two retained nodes.
- Prefer 0 relations over weak relations.
- Do not emit relations based only on co-occurrence in the same sentence or paragraph.
- Do not invent private details.
- Output must be valid JSON with keys: nodes, relations, events.

Allowed node types: person, project, tool, place, topic, org, doc, other
Allowed relation types: related_to, works_on, uses, located_in, about, mentioned_with, published_to, other
Relation guidance:
- `works_on`: only when a person or org is clearly working on a project/task.
- `uses`: only when the text clearly says one entity uses another tool/service.
- `published_to`: only when content is clearly published to a named destination/platform.
- `about`: use rarely; only when a retained doc/page/note is explicitly about a retained topic/entity.
- `mentioned_with` should be extremely rare; use it only when the pairing itself is the important fact.
- Avoid relations between broad containers and their own docs/pages unless the link is central and explicit.
- If either side is a weak or borderline node, prefer no relation.
- Otherwise prefer no relation.

Target schema example:
{json.dumps(schema, ensure_ascii=False)}

Entry timestamp: {entry['timestamp']}
Entry text:
{entry['text']}
"""


def load_nanobot_provider_config() -> dict[str, Any]:
    if not NANOBOT_CONFIG_PATH.exists():
        return {}
    try:
        obj = json.loads(NANOBOT_CONFIG_PATH.read_text(encoding='utf-8'))
    except Exception:
        return {}
    return (obj.get('providers') or {}) if isinstance(obj, dict) else {}


def get_provider_api_key(provider: str) -> str:
    env_map = {
        'gemini': ['GEMINI_API_KEY', 'GOOGLE_API_KEY'],
        'groq': ['GROQ_API_KEY'],
        'openai': ['OPENAI_API_KEY'],
    }
    for env_name in env_map.get(provider, []):
        value = os.getenv(env_name, '').strip()
        if value:
            return value

    providers = load_nanobot_provider_config()
    node = providers.get(provider) or {}
    if isinstance(node, dict):
        api_key = (node.get('apiKey') or '').strip()
        if api_key:
            return api_key
    raise RuntimeError(f'No API key found for provider={provider} in env or {NANOBOT_CONFIG_PATH}')


def extract_json_text(raw: str) -> str:
    text = (raw or '').strip()
    if not text:
        raise ValueError('empty model response')
    if text.startswith('```'):
        text = re.sub(r'^```(?:json)?\s*', '', text)
        text = re.sub(r'\s*```\s*$', '', text)
    try:
        json.loads(text)
        return text
    except Exception:
        pass
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1 and end > start:
        candidate = text[start:end + 1]
        try:
            json.loads(candidate)
            return candidate
        except Exception:
            pass
    # softer salvage for common trailing-text / wrapper noise cases
    m = re.search(r'(\{.*\})', text, flags=re.S)
    if m:
        candidate = m.group(1)
        try:
            json.loads(candidate)
            return candidate
        except Exception:
            pass
    raise ValueError('could not isolate valid JSON object from model response')


def call_gemini(prompt: str, model: str, api_key: str) -> str:
    url = f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}'
    payload = {
        'contents': [{'parts': [{'text': prompt}]}],
        'generationConfig': {
            'temperature': 0,
            'responseMimeType': 'application/json',
        },
    }

    last_error = None
    for attempt in range(5):
        resp = requests.post(url, json=payload, timeout=90)
        if resp.status_code == 200:
            data = resp.json()
            candidates = data.get('candidates') or []
            if not candidates:
                raise RuntimeError(f'No candidates in Gemini response: {data}')
            parts = (((candidates[0] or {}).get('content') or {}).get('parts')) or []
            text = ''.join(part.get('text', '') for part in parts if isinstance(part, dict)).strip()
            if not text:
                raise RuntimeError(f'No text in Gemini response: {data}')
            return extract_json_text(text)
        last_error = f'Gemini HTTP {resp.status_code}: {resp.text[:500]}'
        if resp.status_code == 429 and attempt < 4:
            time.sleep(20 + attempt * 5)
            continue
        break
    raise RuntimeError(last_error or 'Gemini call failed')


def call_openai_compatible(prompt: str, provider: str, model: str, api_key: str) -> str:
    if provider == 'groq':
        url = 'https://api.groq.com/openai/v1/chat/completions'
    elif provider == 'openai':
        url = 'https://api.openai.com/v1/chat/completions'
    else:
        raise RuntimeError(f'Unsupported OpenAI-compatible provider: {provider}')

    payload = {
        'model': model,
        'temperature': 0,
        'response_format': {'type': 'json_object'},
        'messages': [
            {'role': 'system', 'content': 'Return only valid JSON. No markdown fences. No explanation.'},
            {'role': 'user', 'content': prompt},
        ],
    }

    last_error = None
    for attempt in range(5):
        resp = requests.post(
            url,
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
            },
            json=payload,
            timeout=90,
        )
        if resp.status_code == 200:
            data = resp.json()
            choices = data.get('choices') or []
            if not choices:
                raise RuntimeError(f'No choices in {provider} response: {data}')
            message = (choices[0] or {}).get('message') or {}
            text = (message.get('content') or '').strip()
            if not text:
                raise RuntimeError(f'No content in {provider} response: {data}')
            return extract_json_text(text)
        last_error = f'{provider} HTTP {resp.status_code}: {resp.text[:500]}'
        if resp.status_code in {429, 500, 502, 503, 504} and attempt < 4:
            time.sleep(10 + attempt * 5)
            continue
        break
    raise RuntimeError(last_error or f'{provider} call failed')


def try_model_call(prompt: str, provider: str, model: str) -> str:
    api_key = get_provider_api_key(provider)
    if provider == 'gemini':
        return call_gemini(prompt, model, api_key)
    if provider in {'groq', 'openai'}:
        return call_openai_compatible(prompt, provider, model, api_key)
    raise RuntimeError(f'Unsupported provider: {provider}')


def _normalize_label(label: str, node_type: str) -> str:
    s = (label or '').strip().strip('`').strip()
    s = re.sub(r'\s+', ' ', s)
    s = s.strip(' .,:;[](){}<>"\'')
    low = s.lower()
    mapping = {
        'djclaw article': '',
        'djclaw post': 'DJClaw',
        'djclaw posts': 'DJClaw',
        'github project': 'GitHub Projects',
        'github projects': 'GitHub Projects',
        'github pages': 'GitHub Pages',
        'github page': 'GitHub Pages',
        'github repo': 'GitHub',
        'github repository': 'GitHub',
        'djclaw github io': 'DJClaw',
        'djclaw.github.io': 'DJClaw',
        'djclaw site': 'DJClaw',
        'djclaw website': 'DJClaw',
        'djclaw blog': 'DJClaw',
        'the trips project': 'trips',
        'trips project': 'trips',
        'trip project': 'trips',
        'new orleans trip page': 'New Orleans',
        'wiki kernel': 'wiki kernel',
        'personal wiki': 'wiki',
        'wiki project': 'wiki',
        'logseq-like framework': 'Logseq',
        'logseq inspired wiki kernel': 'wiki kernel',
        'history.md': 'HISTORY.md',
        'history md': 'HISTORY.md',
        'github issues': 'GitHub Issues',
        'github issue': 'GitHub Issues',
        'github project board': 'GitHub Projects',
        'djclaw/wiki': 'wiki',
        'djclaw wiki': 'wiki',
        'wiki repo': 'wiki',
        'wiki readme': '',
        'readme': '',
        'extraction pipeline': '',
        'wiki extraction': '',
        'structured extraction': '',
        'extraction poc': '',
        'recent history sample': '',
        'structured candidates': '',
        'history sample': '',
        'local wiki pipeline': 'wiki',
        'local wiki': 'wiki',
    }
    if low in mapping:
        return mapping[low]
    if low == 'djclaw':
        return 'DJClaw'
    if low in {'github', 'github.com'}:
        return 'GitHub'
    if low == 'logseq':
        return 'Logseq'
    if low == 'seqlog':
        return 'SeqLog'
    if low == 'new orleans':
        return 'New Orleans'
    if low == 'airbnb':
        return 'Airbnb'
    if low == 'leaflet':
        return 'Leaflet'
    if low in {'openstreetmap', 'osm'}:
        return 'OpenStreetMap'
    if low in {'wiki', 'personal wiki'}:
        return 'wiki'
    if low in {'trips', 'trips repo'}:
        return 'trips'
    s = re.sub(r'\bgithub pages site\b', 'GitHub Pages', s, flags=re.I)
    s = re.sub(r'\bdjclaw website\b', 'DJClaw', s, flags=re.I)
    s = re.sub(r'\bdjclaw/?wiki\b', 'wiki', s, flags=re.I)
    s = re.sub(r'\bwiki repo\b', 'wiki', s, flags=re.I)
    s = re.sub(r'\bwiki project\b', 'wiki', s, flags=re.I)
    s = re.sub(r'\bpersonal wiki project\b', 'wiki', s, flags=re.I)
    return s


def _keep_node(label: str, node_type: str) -> bool:
    s = _normalize_label(label, node_type)
    low = s.lower()
    if not s:
        return False
    if low in {'user', 'assistant', 'article', 'post', 'file', 'page', 'repo', 'script', 'project', 'tool', 'doc', 'mvp1', 'mvp2', 'pages mvp2', 'entry', 'history entry', 'personal history entry', 'markdown file', 'website', 'blog', 'platform', 'system', 'workflow', 'process', 'content', 'note', 'notes', 'planning', 'implementation', 'architecture', 'pipeline', 'extraction pipeline', 'structured extraction', 'extraction poc', 'history sample', 'recent history sample', 'structured candidates', 'readme', 'wiki readme'}:
        return False
    if low.startswith('post ') and low[5:].isdigit():
        return False
    if re.fullmatch(r'[0-9a-f]{7,40}', low):
        return False
    if s.endswith('.html') or s.endswith('.md') or s.endswith('.json'):
        return False
    if s.startswith('/') and node_type in {'doc', 'other'}:
        return False
    if node_type in {'topic', 'other'} and len(s.split()) <= 2 and low in {'update', 'task', 'tasks', 'status', 'plan', 'note', 'notes', 'design', 'feature'}:
        return False
    if node_type in {'topic', 'other'} and re.fullmatch(r'(current|latest|recent|future|past|next|more|less)', low):
        return False
    return True


def _dedupe_dict_rows(rows: list[dict[str, Any]], key_fields: tuple[str, ...]) -> list[dict[str, Any]]:
    seen = set()
    out = []
    for row in rows:
        key = tuple((row.get(k) or '').strip().lower() if isinstance(row.get(k), str) else row.get(k) for k in key_fields)
        if key in seen:
            continue
        seen.add(key)
        out.append(row)
    return out


def parse_response(raw: str) -> tuple[list[NodeCandidate], list[RelationCandidate], list[EventCandidate]]:
    data = json.loads(raw)

    node_rows = []
    for item in data.get('nodes', []):
        normalized = _normalize_label(item.get('label', ''), item.get('type', 'other'))
        item = dict(item)
        item['label'] = normalized
        if item['label'] == 'DJClaw':
            item['type'] = 'project'
        if item['label'] in {'GitHub', 'GitHub Pages', 'GitHub Projects', 'Airbnb'}:
            item['type'] = 'org'
        if item['label'] in {'New Orleans'}:
            item['type'] = 'place'
        if item['label'] in {'Logseq', 'SeqLog', 'Leaflet', 'OpenStreetMap'}:
            item['type'] = 'tool'
        if _keep_node(item.get('label', ''), item.get('type', 'other')):
            node_rows.append(item)
    node_rows = _dedupe_dict_rows(node_rows, ('label', 'type'))[:5]

    allowed_labels = {row['label'] for row in node_rows}
    rel_rows = []
    for item in data.get('relations', []):
        s = item.get('source_label', '')
        t = item.get('target_label', '')
        if s in allowed_labels and t in allowed_labels:
            rel_rows.append(item)
    node_type_by_label = {row['label']: row.get('type', 'other') for row in node_rows}
    filtered_rel_rows = []
    for item in rel_rows:
        rt = (item.get('relation_type') or '').strip()
        conf = float(item.get('confidence') or 0)
        s = (item.get('source_label') or '').strip()
        t = (item.get('target_label') or '').strip()
        st = node_type_by_label.get(s, 'other')
        tt = node_type_by_label.get(t, 'other')
        if rt in {'mentioned_with', 'related_to', 'about', 'located_in', 'other'}:
            continue
        if rt == 'works_on' and conf < 0.85:
            continue
        if rt == 'uses' and conf < 0.85:
            continue
        if rt == 'published_to' and conf < 0.9:
            continue
        if rt == 'works_on' and st not in {'person', 'org'}:
            continue
        if rt == 'uses' and st not in {'person', 'org', 'project'}:
            continue
        if rt == 'published_to' and tt not in {'org', 'project'}:
            continue
        if s == t:
            continue
        filtered_rel_rows.append(item)
    rel_rows = _dedupe_dict_rows(filtered_rel_rows, ('source_label', 'relation_type', 'target_label'))[:1]

    event_rows = []
    for item in data.get('events', []):
        title = (item.get('title') or '').strip()
        summary = (item.get('summary') or '').strip()
        if title and summary:
            event_rows.append(item)
    event_rows = _dedupe_dict_rows(event_rows, ('title', 'timestamp'))[:2]

    nodes = [NodeCandidate(**item) for item in node_rows]
    relations = [RelationCandidate(**item) for item in rel_rows]
    events = [EventCandidate(**item) for item in event_rows]
    return nodes, relations, events


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('--provider', choices=['gemini', 'groq', 'openai'], default=os.getenv('WIKI_EXTRACTION_PROVIDER', 'gemini'))
    parser.add_argument('--model', default='')
    parser.add_argument('--days', type=int, default=7)
    parser.add_argument('--limit', type=int, default=0)
    return parser.parse_args()


def choose_default_model(provider: str) -> str:
    defaults = {
        'gemini': os.getenv('WIKI_EXTRACTION_GEMINI_MODEL', 'gemini-2.5-flash'),
        'groq': os.getenv('WIKI_EXTRACTION_GROQ_MODEL', 'llama-3.3-70b-versatile'),
        'openai': os.getenv('WIKI_EXTRACTION_OPENAI_MODEL', 'gpt-4o-mini'),
    }
    return defaults[provider]


def main() -> int:
    args = parse_args()
    provider = args.provider
    model = (args.model or choose_default_model(provider)).strip()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    entries = load_recent_entries(days=args.days)
    if args.limit and args.limit > 0:
        entries = entries[-args.limit:]
    SAMPLE_JSON.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding='utf-8')

    print(f'provider={provider} model={model} entries={len(entries)}')

    results: list[dict[str, Any]] = []
    for i, entry in enumerate(entries, start=1):
        evidence = EvidenceRecord(
            evidence_id=f'evidence-{i:03d}',
            source_id='history_md',
            timestamp=entry['timestamp'],
            text=entry['text'],
        )
        item = EntryExtraction(
            entry_id=f'entry-{i:03d}',
            timestamp=entry['timestamp'],
            evidence=evidence,
        )
        prompt = build_prompt(entry)
        try:
            raw = try_model_call(prompt, provider=provider, model=model)
            item.raw_response = raw
            nodes, relations, events = parse_response(raw)
            item.nodes = nodes
            item.relations = relations
            item.events = events
        except Exception as e:
            item.parse_error = str(e)
        results.append({
            'entry_id': item.entry_id,
            'timestamp': item.timestamp,
            'evidence': asdict(item.evidence),
            'nodes': [asdict(x) for x in item.nodes],
            'relations': [asdict(x) for x in item.relations],
            'events': [asdict(x) for x in item.events],
            'raw_response': item.raw_response,
            'parse_error': item.parse_error,
        })
        status = 'ok' if not item.parse_error else f'error={item.parse_error[:120]}'
        print(f'[{i}/{len(entries)}] {item.timestamp} {status}')

    OUTPUT_JSON.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'wrote {len(results)} entries to {OUTPUT_JSON}')
    if results and any(r.get('parse_error') for r in results):
        print('note: some entries have parse_error; inspect structured-candidates.json')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
