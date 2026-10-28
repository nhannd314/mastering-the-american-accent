"""Build data/index.json (the book's Index) from the PDF.

Each index page has two columns; within a column an entry starts at the column's left
edge, a sub-entry is indented one step, and a wrapped list of page numbers is indented
further. Every page number links to the part of the site that covers that book page:
the last entry of the contents (data/front.json) that starts on or before it.

Run from the project root:  python tools/build_index.py
"""
import json
import re
import sys
from pathlib import Path

import pymupdf

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pdflines import marked_lines  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PAGES = (191, 193)
MIDDLE = 380  # x between the two columns
REFS = re.compile(r'^(.*?)\s*((?:\d+(?:–\d+)?\s*,?\s*)+)$')
# Misprints in the book's index
# Entries the book prints indented by mistake (they are not sub-entries of the one above)
TOP = {'Content words'}
FIXES = [('/o /', '/oʊ/'), ('/y versus', '/y/ versus'), ('123,124', '123, 124'), ('<strong>/</strong>', '/')]


def plain(s):
    return re.sub(r'<[^>]+>', '', s)


def columns(doc):
    """Lines of the index in reading order: [(level, html)], level 0 entry, 1 sub-entry, 2 wrapped numbers."""
    out = []
    for pn in range(*PAGES[:1], PAGES[1] + 1):
        lines = [d for d in marked_lines(doc, pn) if plain(d['html']) not in ('Index', 'INDEX')
                 and 'Mastering the American Accent' not in d['html']]
        for col in ([d for d in lines if d['x'] < MIDDLE], [d for d in lines if d['x'] >= MIDDLE]):
            if not col:
                continue
            base = min(d['x'] for d in col)
            for d in sorted(col, key=lambda d: d['y']):
                step = d['x'] - base
                level = 2 if step > 18 and re.match(r'\d', plain(d['html'])) else 1 if step > 6 else 0
                out.append((level, d['html']))
    return out


def split_refs(html):
    m = REFS.match(plain(html))
    if not m:
        return html, []
    nums = m.group(2).strip()
    at = html.rfind(nums)  # the numbers carry no tags, so they end the html as they are
    term = html[:at] if at >= 0 else html
    return term.strip().rstrip(','), [p.strip() for p in nums.split(',') if p.strip()]


def linker():
    toc = json.loads((ROOT / 'data' / 'front.json').read_text(encoding='utf-8'))['toc']
    starts = sorted((int(t['page']), i, t['link']) for i, t in enumerate(toc)
                    if t.get('link') and str(t.get('page', '')).isdigit())

    def link(p):
        n = int(p.split('–')[0])
        hit = [s for s in starts if s[0] <= n]
        return hit[-1][2] if hit else None
    return link


def letter_of(term, current):
    m = re.search(r'[A-Za-z]', plain(term))
    c = m.group(0).upper() if m else current
    return c if current is None or c >= current else current


def main():
    doc = pymupdf.open(ROOT / 'Mastering the American Accent.pdf')
    link = linker()
    entries = []
    for level, html in columns(doc):
        for a, b in FIXES:
            html = html.replace(a, b)
        if level == 2:
            target = entries[-1]['subs'][-1] if entries[-1]['subs'] else entries[-1]
            target['refs'] += split_refs(html)[1]
            continue
        term, refs = split_refs(html)
        item = {'term': term, 'refs': refs}
        if level == 0 or plain(term) in TOP:
            entries.append({**item, 'subs': []})
        else:
            entries[-1]['subs'].append(item)

    groups, cur = [], None
    for e in entries:
        c = letter_of(e['term'], cur)
        if c != cur:
            groups.append({'letter': c, 'entries': []})
            cur = c
        groups[-1]['entries'].append(e)

    def linked(item):
        item['refs'] = [{'p': p, 'link': link(p)} for p in item['refs']]
        for s in item.get('subs', []):
            linked(s)
    for g in groups:
        for e in g['entries']:
            linked(e)

    out = ROOT / 'data' / 'index.json'
    out.write_text(json.dumps({'blocks': [{'t': 'index', 'groups': groups}]}, ensure_ascii=False, indent=1),
                   encoding='utf-8')

    front_path = ROOT / 'data' / 'front.json'
    front = json.loads(front_path.read_text(encoding='utf-8'))
    for t in front['toc']:
        if t['title'] == 'Index':
            t['link'] = 'index'
    front_path.write_text(json.dumps(front, ensure_ascii=False, indent=1), encoding='utf-8')
    subs = sum(len(e['subs']) for e in entries)
    print(f'wrote {out}: {len(entries)} entries + {subs} sub-entries, letters {"".join(g["letter"] for g in groups)}')


if __name__ == '__main__':
    main()
