"""Convert a chapter of the book PDF into data/<chapter>.json for the PHP site.

All text comes straight from the PDF. The script classifies text blocks by
their font (section titles, exercise titles, quotes, CD-track badges...),
rebuilds tables/lists from line positions, turns light-blue panels into
boxes and crops vector illustrations into PNGs under assets/images/.

Usage (from the project root):  python tools/pdf2json.py ch4
"""
import json
import re
import sys
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parent.parent
PDF = ROOT / 'Mastering the American Accent.pdf'

CHAPTERS = {
    'ch4': {
        'pages': (41, 72),
        'cd': 2,
        # Section ids in order of appearance (they match the links in data/front.json).
        'ids': ['t-sounds', 'fast-d', 'tr', 'dr', 'du', 'tu', 'ed', 'th', 'r', 'l', 'l-r', 'v', 'b-v', 'w',
                'v-w', 's-z', 'ng', 'clusters'],
        # Exercises left out entirely (copyrighted song lyrics).
        'skip': [r'^Song Lyrics'],
    },
}

BOX_FILL = (0.88, 0.96, 0.99)
BLUE = 0x00aeef


# ---------------------------------------------------------------------------
# Text helpers

def fix(s):
    s = s.replace(' ', ' ').replace('/q/', '/θ/').replace('/ /', '/θ/')
    return re.sub(r'[ \t]+', ' ', s).strip()


def prose(lines):
    out = ''
    for l in lines:
        l = fix(l)
        if not l:
            continue
        if out.endswith('-') and l[:1].islower():
            out = out[:-1] + l
        else:
            out = f'{out} {l}' if out else l
    return out


def is_marker_line(t):
    return bool(re.fullmatch(r'(\s*/[^/\s]+/\s*)+', t))


NUM = re.compile(r'^(\d+)\.?(?:\s+(.*))?$')


# ---------------------------------------------------------------------------
# Raw page reading

class Line:
    def __init__(self, raw):
        spans = [s for s in raw['spans'] if s['text'].strip()]
        self.text = fix(''.join(s['text'] for s in raw['spans']))
        self.bbox = pymupdf.Rect(raw['bbox'])
        s = spans[0] if spans else raw['spans'][0]
        self.font, self.size, self.color = s['font'], round(s['size']), s['color']


class Block:
    def __init__(self, pn, raw):
        self.pn = pn
        self.bbox = pymupdf.Rect(raw['bbox'])
        self.lines = [Line(l) for l in raw['lines'] if ''.join(s['text'] for s in l['spans']).strip()]
        self.text = ' | '.join(l.text for l in self.lines)
        f = self.lines[0] if self.lines else None
        self.font, self.size, self.color = (f.font, f.size, f.color) if f else ('', 0, 0)

    @property
    def y(self):
        return self.bbox.y0


def near(a, b, tol=3):
    return all(abs(x - y) <= tol for x, y in zip(a, b))


def read_page(doc, pn):
    page = doc[pn - 1]
    blocks = []
    for raw in page.get_text('dict')['blocks']:
        if raw['type'] != 0:
            continue
        b = Block(pn, raw)
        if not b.lines or not b.text.replace('(', '').replace('|', '').strip():
            continue  # empty, or the "(" glyphs used to draw linking arcs
        if b.y > page.rect.height * 0.75 and re.search(r'Mastering the American Accent|Chapter \w+:', b.text):
            continue  # running footer
        blocks.append(b)

    rects = [(pymupdf.Rect(d['rect']), d.get('fill')) for d in page.get_drawings()]
    title_blocks = [b for b in blocks if is_box_title(b)]
    boxes = [r for r, f in rects if f and near(f, BOX_FILL, 0.02) and r.get_area() > 3000]
    # White panels holding a box title are boxes too (e.g. "Advice from a Successful Student").
    boxes += [r for r, f in rects if f and near(f, (1, 1, 1), 0.01) and r.get_area() > 3000
              and any(r.contains(t.bbox) for t in title_blocks)]
    boxes = [r for r in boxes if not any(o is not r and o.contains(r) for o in boxes)]

    # Illustrations: white frames plus the blue (tongue/mouth) or pale-blue (lips) shapes inside them.
    # A cluster only counts if it holds one of those coloured shapes, or is a large stroked panel.
    figs = []
    for r, f in rects:
        if r.get_area() < 2000 or any(b.intersects(r) for b in boxes):
            continue
        if f is None and not any(near(r, b, 3) for b in boxes) and r.get_area() > 40000:
            figs.append((pymupdf.Rect(r), True))  # stroked illustration panel
        elif f and (near(f, (0, 0.68, 0.94), 0.03) or near(f, (0.78, 0.92, 0.99), 0.03)):
            figs.append((pymupdf.Rect(r), True))
        elif f and near(f, (1, 1, 1), 0.01):
            figs.append((pymupdf.Rect(r), False))
    figs = [r for r, coloured in merge_rows(figs) if coloured]
    return page, blocks, boxes, figs


def merge_rows(rects):
    """Union rectangles whose vertical ranges overlap (illustrations side by side)."""
    out = []
    for r, c in sorted(rects, key=lambda rc: rc[0].y0):
        for o in out:
            if r.y0 < o[0].y1 and r.y1 > o[0].y0:
                o[0] |= r
                o[1] = o[1] or c
                break
        else:
            out.append([pymupdf.Rect(r), c])
    return out


def is_box_title(b):
    return b.size == 12 and (b.font.startswith('Giovanni-Black') or b.font.startswith('ArialMT-ExtraBold'))


# ---------------------------------------------------------------------------
# Classification

def classify(b):
    f, s = b.font, b.size
    if s >= 20:
        return 'skip'
    if s <= 8:
        return 'badge' if f.startswith('Garamond') else 'skip'
    if f.startswith('ArialMT-ExtraBold') and s >= 18:
        return 'sec'
    if f.startswith('ArialMT') and s == 16:
        return 'sub'
    if f.startswith('ArialMT') and s == 14 and b.color != BLUE:
        return 'ex'
    if f.startswith('Giovanni-BoldItali') and s == 12:
        return 'quote'
    if f.startswith('Giovanni-BookItali') and s == 10:
        return 'by'
    if is_box_title(b):
        return 'boxtitle'
    if f.startswith('Giovanni-Bold') and s == 12:
        return 'kick'
    return 'content'


def elements(doc, pn, cfg, figdir, figprefix):
    """Ordered raw elements for one page."""
    page, blocks, boxes, figs = read_page(doc, pn)
    used = set()
    els = []

    for r in boxes:
        inside = [b for b in blocks if r.contains(b.bbox.tl + (1, 1)) and id(b) not in used]
        used.update(id(b) for b in inside)
        inside.sort(key=lambda b: (b.y, b.bbox.x0))
        icon = any(r.contains(pymupdf.Rect(i['bbox'])) for i in page.get_image_info())
        els.append({'k': 'box', 'pn': pn, 'y': r.y0, 'blocks': inside, 'icon': icon})

    for n, r in enumerate(figs, 1):
        grab = pymupdf.Rect(r.x0 - 10, r.y0 - 5, r.x1 + 10, r.y1 + 28)
        labels = [b for b in blocks if id(b) not in used and grab.contains((b.bbox.tl + b.bbox.br) / 2)
                  and (len(b.text) < 40 or r.contains(b.bbox))]
        clip = pymupdf.Rect(r)
        for b in labels:
            clip |= b.bbox
            used.add(id(b))
        clip = clip + (-6, -6, 6, 6)
        name = f'{figprefix}-{pn}-{n}.png'
        page.get_pixmap(dpi=200, clip=clip).save(figdir / name)
        alt = prose(l.text for b in labels for l in b.lines)
        els.append({'k': 'fig', 'pn': pn, 'y': r.y0, 'src': 'images/' + name, 'alt': alt})

    badges = []
    for b in blocks:
        if id(b) in used:
            continue
        k = classify(b)
        if k == 'skip':
            continue
        if k == 'badge':
            if b.text.startswith('CD'):
                badges.append(b)
            continue
        els.append({'k': k, 'pn': pn, 'y': b.y, 'b': b})

    for bd in badges:
        cd = int(re.search(r'CD (\d+)', bd.text).group(1))
        num = next((int(o.text) for o in blocks if o is not bd and o.text.isdigit()
                    and abs(o.bbox.x0 - bd.bbox.x0) < 8 and 0 < o.y - bd.y < 20), None)
        if num is None:
            continue
        heads = [e for e in els if e['k'] in ('sec', 'sub', 'ex', 'box')] or els
        target = min(heads, key=lambda e: abs(e['y'] - bd.y))
        if abs(target['y'] - bd.y) > 40:
            target = min(els, key=lambda e: abs(e['y'] - bd.y))
        target['cd'], target['track'] = cd, num

    els.sort(key=lambda e: e['y'])
    return els


# ---------------------------------------------------------------------------
# Content blocks -> JSON blocks

def rows_of(lines):
    rows = []
    for l in sorted(lines, key=lambda l: (round(l.bbox.y0), l.bbox.x0)):
        for r in rows:
            if abs(r[0].bbox.y0 - l.bbox.y0) <= 3:
                r.append(l)
                break
        else:
            rows.append([l])
    return [sorted(r, key=lambda l: l.bbox.x0) for r in rows]


def looks_prose(texts):
    if len(texts) == 1:
        return len(texts[0]) > 60
    joins = sum(1 for a, b in zip(texts, texts[1:]) if a.endswith('-') or b[:1].islower())
    return joins >= (len(texts) - 1) / 2


def convert(lines):
    rows = rows_of(lines)
    if any(is_marker_line(r[0].text) for r in rows if len(r) == 1) or any(
            is_marker_line(' '.join(c.text for c in r)) for r in rows):
        out, ipa = [], None
        for r in rows:
            t = ' '.join(c.text for c in r)
            if is_marker_line(t):
                ipa = re.sub(r'\s+', '  ', t.strip())
                continue
            sp = ''
            m = re.match(r'^([A-Z][\w ]+):\s*(.*)$', t)
            if m and len(m.group(1)) < 20:
                sp, t = m.group(1), m.group(2)
            if not t and sp:
                out.append([sp, '', ''])
                continue
            if out and not sp and not ipa and out[-1][1]:
                out[-1][1] += ' ' + t
            else:
                out.append([sp, t, ipa or ''])
            ipa = None
        return {'t': 'script', 'lines': out}

    if all(len(r) == 1 for r in rows):
        texts = [r[0].text for r in rows]
        if any(NUM.match(t) and NUM.match(t).group(2) for t in texts):
            items = []
            for t in texts:
                m = NUM.match(t)
                if m and m.group(2):
                    items.append([m.group(2)])
                elif items:
                    if re.match(r'^[a-z]\.\s', t) or re.match(r'^[a-z]\.\s', items[-1][0]):
                        items[-1].append(t)
                    else:
                        items[-1][-1] = prose([items[-1][-1], t])
            if any(len(i) > 1 for i in items):
                return {'t': 'dialog', 'items': items}
            return {'t': 'list', 'items': [i[0] for i in items]}
        if looks_prose(texts):
            return {'t': 'p', 'paras': [prose(texts)]}
        return {'t': 'lines', 'lines': texts}

    # Multi-column rows.
    def segs(r):
        out, cur = [], None
        for i, c in enumerate(r):
            m = NUM.match(c.text)
            if m and (m.group(2) or i < len(r) - 1) and (c.text.endswith('.') or m.group(2) or i == 0):
                cur = [int(m.group(1)), [m.group(2)] if m.group(2) else []]
                out.append(cur)
            elif cur:
                cur[1].append(c.text)
            else:
                return None
        return out

    numbered = [(r, segs(r)) for r in rows]
    if any(s for _, s in numbered):
        head_rows = []
        for r, s in numbered:
            if s:
                break
            head_rows.append([c.text for c in r])
        items = sorted((seg for _, s in numbered if s for seg in s), key=lambda s: s[0])
        width = max(len(s[1]) for s in items)
        per_row = max(len(s) for _, s in numbered if s)
        heads = []
        for hr in head_rows:
            hr = hr[:width] if len(hr) >= width * per_row else hr
            heads = [f'{a} {b}'.strip() for a, b in zip(heads, hr)] if heads else hr
        if width == 1:
            return {'t': 'nums', 'cols': per_row, 'items': [s[1][0] for s in items]}
        rows_out = [s[1] + [''] * (width - len(s[1])) for s in items]
        if width == 2 and len(heads) in (0, 2):
            return {'t': 'contrast', 'heads': heads or ['', ''], 'rows': rows_out}
        blk = {'t': 'table', 'numbered': True, 'rows': rows_out}
        if heads:
            blk['heads'] = heads[:width] if len(heads) >= width else heads + [''] * (width - len(heads))
        return blk

    cells = [[c.text for c in r] for r in rows]
    first, second = rows[0], rows[1] if len(rows) > 1 else None
    header = second is not None and (
        all(re.fullmatch(r'/.+/|.+:', c.text) for c in first)
        or (first[0].color != second[0].color) or (first[0].font != second[0].font))
    if header and len(rows) > 1:
        width = len(first)
        return {'t': 'table', 'heads': cells[0], 'rows': [r + [''] * (width - len(r)) for r in cells[1:]]}
    if all(len(c) < 30 for r in cells for c in r):
        return {'t': 'words', 'groups': [{'words': [c for r in cells for c in r]}]}
    width = max(len(r) for r in cells)
    return {'t': 'table', 'rows': [r + [''] * (width - len(r)) for r in cells]}


def group_contents(blocks):
    """Merge vertically adjacent content blocks that share a left edge (one list split in pieces)."""
    groups = []
    for b in blocks:
        g = groups[-1] if groups else None
        if g and b.pn == g[-1].pn and abs(b.bbox.x0 - g[-1].bbox.x0) < 4 and 0 <= b.y - g[-1].bbox.y1 < 12:
            g.append(b)
        else:
            groups.append([b])
    return groups


# ---------------------------------------------------------------------------
# Assembly

class Builder:
    def __init__(self, cfg):
        self.cfg = cfg
        self.out = []
        self.pending = None
        self.ids = list(cfg['ids'])
        self.skipping = False

    def head(self):
        p, self.pending = self.pending, None
        return p

    def flush(self):
        p = self.head()
        if p:
            blk = {'t': 'p', 'paras': [p.pop('sub')] if p.get('sub') else []}
            blk.update({k: v for k, v in p.items() if v})
            self.emit(blk)

    def emit(self, blk, pend=None):
        if pend:
            for k, v in pend.items():
                if v and not blk.get(k):
                    blk[k] = v
        last = self.out[-1] if self.out else None
        mergeable = last and not pend and not any(blk.get(k) for k in ('title', 'track', 'kicker', 'sub'))
        if mergeable and last['t'] == blk['t'] and blk['t'] in ('p', 'dialog', 'list', 'script', 'lines'):
            key = {'p': 'paras', 'dialog': 'items', 'list': 'items', 'script': 'lines', 'lines': 'lines'}[blk['t']]
            last[key] += blk[key]
            return
        self.out.append(blk)

    def track_of(self, e):
        return {'cd': e['cd'], 'track': e['track']} if e.get('track') else {}

    def add_content(self, blocks, extra=None):
        for g in group_contents(blocks):
            lines = [l for b in g for l in b.lines]
            kick = None
            if lines and lines[0].font.startswith('Giovanni-Bold') and lines[0].size == 12 and len(lines) > 1:
                kick = lines.pop(0).text
            blk = convert(lines)
            pend = self.head() or {}
            if extra:
                pend.update(extra)
                extra = None
            if kick:
                pend['kicker'] = pend.get('kicker') or kick
            self.emit(blk, pend)

    def run(self, els):
        i = 0
        while i < len(els):
            e = els[i]
            k = e['k']
            b = e.get('b')
            if self.skipping and k not in ('sec', 'sub', 'ex', 'box', 'fig'):
                i += 1
                continue
            self.skipping = False

            if k == 'sec':
                self.flush()
                blk = {'t': 'sec', 'id': self.ids.pop(0) if self.ids else None, 'title': prose(l.text for l in b.lines)}
                blk.update(self.track_of(e))
                self.out.append(blk)
            elif k == 'quote':
                qs = [prose(l.text for l in b.lines)]
                while i + 1 < len(els) and els[i + 1]['k'] == 'quote':
                    i += 1
                    qs.append(prose(l.text for l in els[i]['b'].lines))
                by = ''
                if i + 1 < len(els) and els[i + 1]['k'] == 'by':
                    i += 1
                    by = els[i]['b'].text
                quote = ' '.join(qs)
                last = self.out[-1] if self.out else None
                if last and last['t'] == 'sec' and not last.get('quote'):
                    last['quote'], last['by'] = quote, by
                else:
                    self.flush()
                    self.out.append({'t': 'box', 'kind': 'advice', 'title': '', 'text': quote, 'by': by})
            elif k == 'by':
                last = self.out[-1] if self.out else None
                if last is not None and not last.get('by'):
                    last['by'] = b.text
            elif k in ('sub', 'ex'):
                if any(re.search(p, b.lines[0].text) for p in self.cfg.get('skip', [])):
                    self.flush()
                    self.skipping = True
                    i += 1
                    continue
                self.flush()
                title = b.lines[0].text
                rest = b.lines[1:]
                ex_lines = [l for l in rest if l.size == 14]
                body = [l for l in rest if l.size != 14]
                pend = {'title': title, **self.track_of(e)}
                if k == 'sub' and body:
                    blk = {'t': 'p', 'title': title, 'paras': [prose(l.text for l in body)]}
                    blk.update(self.track_of(e))
                    self.out.append(blk)
                    pend = {'title': ex_lines[0].text} if ex_lines else None
                elif k == 'sub' and ex_lines:
                    self.out.append({'t': 'p', 'title': title, 'paras': [], **self.track_of(e)})
                    pend = {'title': ex_lines[0].text}
                elif body:
                    pend['sub'] = prose(l.text for l in body)
                self.pending = pend
            elif k == 'kick':
                if self.pending and not self.pending.get('sub') and self.pending.get('title'):
                    self.pending['sub'] = b.text
                else:
                    self.flush()
                    self.pending = {'kicker': b.text}
            elif k == 'boxtitle':
                self.flush()
                self.pending = {'title': b.lines[0].text}
                rest = b.lines[1:]
                if rest:
                    self.emit(convert(rest), self.head())
            elif k == 'fig':
                self.out.append({'t': 'img', 'src': e['src'], 'alt': e['alt']})
            elif k == 'box':
                self.flush()
                self.out.append(self.build_box(e))
            elif k == 'content':
                group = [b]
                while i + 1 < len(els) and els[i + 1]['k'] == 'content' and not els[i + 1].get('track'):
                    i += 1
                    group.append(els[i]['b'])
                self.add_content(group, self.track_of(e))
            i += 1
        self.flush()
        return self.out

    def build_box(self, e):
        blocks = e['blocks']
        title, kind = '', 'note'
        if blocks and is_box_title(blocks[0]):
            first = blocks.pop(0)
            title = first.lines[0].text
            if len(first.lines) > 1:
                blocks.insert(0, Block(first.pn, {'bbox': tuple(first.bbox), 'lines': []}))
                blocks[0].lines = first.lines[1:]
                blocks[0].text = ' | '.join(l.text for l in blocks[0].lines)
                blocks[0].font, blocks[0].size, blocks[0].color = first.font, 11, 0
        if title.startswith('Warning'):
            kind = 'warning'
        elif title.startswith('Advice'):
            kind = 'advice'
        elif title.startswith('Study Tip') or e['icon']:
            kind = 'tip'
        if not title:
            # A plain highlighted panel (e.g. pronunciation rules): render its content inline.
            sub = Builder({'ids': [], 'skip': []})
            sub.run([{'k': classify(b), 'pn': b.pn, 'y': b.y, 'b': b} for b in blocks])
            return {'t': 'box', 'kind': 'panel', 'children': sub.out, **self.track_of(e)}
        if kind == 'advice':
            by = next((b.text for b in blocks if classify(b) == 'by' or b.font.startswith('Giovanni-BookItali')), '')
            text = prose(l.text for b in blocks if b.text != by for l in b.lines)
            return {'t': 'box', 'kind': 'advice', 'title': title, 'text': text, 'by': by, **self.track_of(e)}
        sub = Builder({'ids': [], 'skip': []})
        sub.run([{'k': classify(b), 'pn': b.pn, 'y': b.y, 'b': b} for b in blocks])
        blk = {'t': 'box', 'kind': kind, 'title': title, 'children': sub.out, **self.track_of(e)}
        if kind == 'tip':
            blk['img'] = 'images/study-tip.png'
        return blk


def main(chapter):
    cfg = CHAPTERS[chapter]
    doc = pymupdf.open(PDF)
    figdir = ROOT / 'assets' / 'images'
    els = []
    for pn in range(cfg['pages'][0], cfg['pages'][1] + 1):
        els += elements(doc, pn, cfg, figdir, chapter)
    blocks = Builder(cfg).run(els)
    for blk in blocks:
        if blk.get('track') and 'cd' not in blk:
            blk['cd'] = cfg['cd']
    out = ROOT / 'data' / f'{chapter}.json'
    out.write_text(json.dumps({'blocks': blocks}, ensure_ascii=False, indent=1), encoding='utf-8')
    secs = [b for b in blocks if b['t'] == 'sec']
    print(f'wrote {out}: {len(blocks)} blocks, {len(secs)} sections, '
          f'{sum(1 for b in blocks if b.get("track"))} tracks, unused ids: {len(cfg["ids"]) - len(secs)}')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'ch4')
