#!/usr/bin/env python3
import json
import re
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path('/home/dj/.nanobot/workspace/memory/wiki.db')
OUTPUT_DIR = Path('/home/dj/.nanobot/workspace/wiki/entries/history')
TEMPLATES_DIR = Path('/home/dj/.nanobot/workspace/wiki/templates')
LIMIT = 200
STOPWORDS = {
    'a', 'an', 'and', 'all', 'are', 'as', 'at', 'about', 'after', 'around', 'be', 'by', 'for', 'from',
    'how', 'i', 'if', 'in', 'into', 'is', 'it', 'new', 'of', 'on', 'or', 'the', 'to', 'with', 'we', 'you',
    'comparison', 'confirmed', 'current', 'destination', 'directed', 'explained', 'explainer', 'listing',
    'master', 'notes', 'personal', 'public', 'pushed', 'refine', 'requested', 'shows', 'switched',
    'travel', 'update'
}
ALLOW_SHORT = {'AI', 'UI', 'DB', 'CLI', 'MCP', 'BJJ', 'Git', 'npm'}
ALLOW_NODE_TYPES = {'project', 'tool', 'person', 'place', 'concept', 'event', 'organization'}


def slugify(text: str) -> str:
    text = (text or '').strip().lower()
    text = re.sub(r'\s+', '-', text)
    text = re.sub(r'[^a-z0-9\-\u4e00-\u9fff]', '', text)
    return text[:80] or 'entry'


def load_template(name: str) -> str:
    return (TEMPLATES_DIR / name).read_text(encoding='utf-8')


def html_escape(text: str) -> str:
    return ((text or '')
        .replace('&', '&amp;')
        .replace('<', '&lt;')
        .replace('>', '&gt;'))


def is_publishable_node(node, timeline_count=0, related_count=0):
    title = (node.get('title') or '').strip()
    lower = title.lower()
    node_type = (node.get('node_type') or '').strip().lower()
    summary = (node.get('summary') or '').strip()
    aliases = node.get('aliases') or []
    tags = node.get('tags') or []
    categories = node.get('categories') or []

    signal_count = 0
    if timeline_count > 0:
        signal_count += 1
    if related_count >= 2:
        signal_count += 1
    if aliases:
        signal_count += 1
    if tags or categories:
        signal_count += 1
    if summary and summary.lower() not in {'(no summary yet.)', 'no summary yet.', 'unknown'}:
        signal_count += 1

    if not title:
        return False, 'empty'
    if node_type and node_type not in ALLOW_NODE_TYPES:
        return False, 'node-type'
    if lower in STOPWORDS:
        return False, 'stopword'
    if title.startswith(('#', '.', '-', '(', '/', '[')):
        return False, 'punct-start'
    if re.fullmatch(r'[0-9a-f]{7,40}', lower):
        return False, 'commit-hash'
    if re.fullmatch(r'\d+(\.\d+){1,4}(:\d+)?', title):
        return False, 'ip-or-version'
    if re.fullmatch(r'\d+(\.\d+)+', title):
        return False, 'section-number'
    if '/' in title or '\\' in title:
        return False, 'path-like'
    if title.endswith(('.html', '.md', '.json', '.py', '.sh', '.png', '.jpg', '.jpeg')):
        return False, 'file-like'
    if '@' in title:
        return False, 'handle-or-address'
    if re.search(r'\.html\b|\.md\b|\.json\b|\.py\b|\.sh\b', lower):
        return False, 'file-like'
    if title.islower() and re.fullmatch(r'[a-z]+', lower) and len(title) <= 4 and title not in ALLOW_SHORT:
        return False, 'short-lowercase-word'
    if re.fullmatch(r'[a-z\-]+', lower) and '-' in lower and title == lower:
        return False, 'slug-like'
    if len(title) <= 2 and title not in ALLOW_SHORT:
        return False, 'too-short'
    if signal_count < 2:
        return False, 'low-signal'
    if timeline_count == 0 and related_count < 2:
        return False, 'too-thin'
    return True, 'ok'


def build_infobox_rows(node):
    rows = []
    rows.append(f"<dt>Type</dt><dd>{html_escape(node.get('node_type') or 'topic')}</dd>")
    rows.append(f"<dt>Node ID</dt><dd>{html_escape(node['node_id'])}</dd>")
    if node.get('status'):
        rows.append(f"<dt>Status</dt><dd>{html_escape(node['status'])}</dd>")
    if node.get('visibility'):
        rows.append(f"<dt>Visibility</dt><dd>{html_escape(node['visibility'])}</dd>")
    categories = node.get('categories', [])
    if categories:
        rows.append(f"<dt>Categories</dt><dd>{html_escape(', '.join(categories))}</dd>")
    tags = node.get('tags', [])
    if tags:
        rows.append(f"<dt>Tags</dt><dd>{html_escape(', '.join(tags))}</dd>")
    aliases = node.get('aliases', [])
    if aliases:
        rows.append(f"<dt>Aliases</dt><dd>{html_escape(', '.join(aliases))}</dd>")
    return '\n'.join(rows)


def build_sections(node, timeline, related):
    summary = (node.get('summary') or '').strip() or '(No summary yet.)'
    timeline_items = []
    for item in timeline:
        label = html_escape(item.get('timestamp') or 'Unknown time')
        summary_text = html_escape(item.get('summary') or '')
        timeline_items.append(f'<li><strong>{label}</strong> — {summary_text}</li>')
    if not timeline_items:
        timeline_items.append('<li>(No events yet.)</li>')

    related_items = []
    for item in related:
        href = f"/wiki/entries/history/{item['to_node']}.html"
        title = html_escape(item.get('title') or item['to_node'])
        rtype = html_escape(item.get('relation_type') or 'related_to')
        related_items.append(f'<li><a href="{href}">{title}</a> <span class="muted">({rtype})</span></li>')
    if not related_items:
        related_items.append('<li>(No related entries yet.)</li>')

    sections = [
        '<section id="summary">', '<h2>Overview</h2>', f'<p>{html_escape(summary)}</p>', '</section>',
        '<section id="timeline">', '<h2>Timeline</h2>', '<ul>', *timeline_items, '</ul>', '</section>',
        '<section id="related-manual">', '<h2>Related</h2>', '<ul>', *related_items, '</ul>', '</section>',
    ]
    return '\n'.join(sections)


def build_toc_items():
    return ''.join([
        '<li><a href="#summary">Overview</a></li>',
        '<li><a href="#timeline">Timeline</a></li>',
        '<li><a href="#related-manual">Related</a></li>',
    ])


def render_entity(node, timeline, related):
    entity_tpl = load_template('entity.html')
    entity = entity_tpl.replace('{{title}}', html_escape(node['title']))
    entity = entity.replace('{{summary}}', html_escape(node.get('summary', '') or ''))
    entity = entity.replace('{{infobox_rows}}', build_infobox_rows(node))
    entity = entity.replace('{{toc_items}}', build_toc_items())
    entity = entity.replace('{{sections}}', build_sections(node, timeline, related))
    return entity


def render_page(title: str, content: str):
    layout = load_template('layout.html')
    updated_at = datetime.now().strftime('%Y-%m-%d %H:%M')
    page = layout.replace('{{title}}', html_escape(title))
    page = page.replace('{{content}}', content)
    page = page.replace('{{updated_at}}', updated_at)
    return page


def fetch_nodes(conn):
    conn.row_factory = sqlite3.Row
    return conn.execute(
        'SELECT node_id, node_type, title, summary, aliases_json, tags_json, categories_json, status, visibility FROM nodes ORDER BY title LIMIT ?',
        (LIMIT,),
    ).fetchall()


def fetch_timeline(conn, node_id):
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT event_id, timestamp, summary FROM events WHERE node_ids_json LIKE ? ORDER BY timestamp DESC, event_id DESC LIMIT 40",
        (f'%\"{node_id}\"%',),
    ).fetchall()
    return [dict(r) for r in rows]


def fetch_related(conn, node_id):
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        '''
        SELECT r.to_node, r.relation_type, n.title
        FROM relations r
        LEFT JOIN nodes n ON n.node_id = r.to_node
        WHERE r.from_node = ?
        ORDER BY COALESCE(n.title, r.to_node)
        LIMIT 40
        ''',
        (node_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def main():
    conn = sqlite3.connect(DB_PATH)
    rows = fetch_nodes(conn)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for old in OUTPUT_DIR.glob('*.html'):
        old.unlink()

    generated = []
    skipped = []
    for row in rows:
        node = dict(row)
        node['aliases'] = json.loads(node.get('aliases_json') or '[]')
        node['tags'] = json.loads(node.get('tags_json') or '[]')
        node['categories'] = json.loads(node.get('categories_json') or '[]')
        timeline = fetch_timeline(conn, node['node_id'])
        related = fetch_related(conn, node['node_id'])
        ok, reason = is_publishable_node(node, len(timeline), len(related))
        if not ok:
            skipped.append((node['title'], reason))
            continue
        full_page = render_page(node['title'], render_entity(node, timeline, related))
        filename = f"{slugify(node['node_id'])}.html"
        (OUTPUT_DIR / filename).write_text(full_page, encoding='utf-8')
        generated.append(filename)

    conn.close()
    print(f'Generated {len(generated)} node pages in {OUTPUT_DIR}')
    print(f'Skipped {len(skipped)} nodes')
    reason_counts = {}
    for _, reason in skipped:
        reason_counts[reason] = reason_counts.get(reason, 0) + 1
    print('Skip reasons:', json.dumps(reason_counts, ensure_ascii=False, sort_keys=True))
    for name in generated[:20]:
        print('OK ', name)
    for title, reason in skipped[:30]:
        print('SKIP', reason, '::', title)


if __name__ == '__main__':
    main()
