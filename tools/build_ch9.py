"""Build data/ch9.json (Chapter 9: Memorizing the Exceptions) from the book PDF.

The old HTML edition scrambled this chapter's tables (cells of one entry spread over
several rows), so everything is read from the PDF: lines come from pdflines (which keeps
bold/italic and the dropped vowels printed above "choc late"), and table cells are
placed by the grid the book draws around them. The chapter has no CD tracks.

Run from the project root:  python tools/build_ch9.py
"""
import json
import re
import sys
from pathlib import Path

import pymupdf

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pdflines import marked_lines  # noqa: E402
from old2json import link_toc  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
doc = pymupdf.open(ROOT / 'Mastering the American Accent.pdf')


def plain(s):
    return re.sub(r'<[^>]+>', '', s)


def prose(ls):
    """Join wrapped lines, mending words hyphenated at line ends ("environ-" + "ment")."""
    out = ''
    for l in ls:
        if re.search(r'[a-z]-$', plain(out)) and re.match(r'(<[^>]+>)*[a-z]', l):
            out = out[:-1] + l
        else:
            out = f'{out} {l}' if out else l
    return re.sub(r'\s+', ' ', out).strip()


def lines(pn, y0, y1):
    return [d for d in marked_lines(doc, pn, y0, y1)]


def text(pn, y0, y1):
    return prose([d['html'] for d in lines(pn, y0, y1)])


def tidy(s):
    """The book's symbol slips: /ae/, /ou/, /I/ for /æ/, /oʊ/, /ɪ/; loose dashes and quotes."""
    s = s.replace('/ae/', '/æ/').replace('/ou/', '/oʊ/').replace('/I/', '/ɪ/')
    s = s.replace('“moo” +”zei“ +', '“moo” + “zei” +')
    return re.sub(r'(\w)\s*[-–]\s*(?=\w)', r'\1–', s) if re.fullmatch(r"[\w’ –-]+", s) else s


def unnum(s):
    return re.sub(r'^((?:<[^>]+>)*)\d+\.\s*', r'\1', s)


def grid(pn, y0, y1):
    """Rows of cells inside the table drawn between y0 and y1: each cell a list of lines (y, html)."""
    page = doc[pn - 1]
    ys, xs = set(), set()
    for d in page.get_drawings():
        r = d['rect']
        if not (y0 - 2 <= r.y0 <= y1 + 2):
            continue
        if r.height < 2 and r.width > 50:
            ys.add(round(r.y0))
        elif r.width < 2 and r.height > 10:
            xs.add(round(r.x0))
    ys, xs = sorted(ys), sorted(xs)
    rows = [[[] for _ in xs[:-1]] for _ in ys[:-1]]
    for d in marked_lines(doc, pn, y0, y1):
        mid = d['y'] + 5
        ri = next((i for i in range(len(ys) - 1) if ys[i] <= mid < ys[i + 1]), None)
        ci = next((i for i in range(len(xs) - 1) if xs[i] <= d['x'] < xs[i + 1]), None)
        if ri is not None and ci is not None:
            rows[ri][ci].append((d['y'], d['html']))
    return rows


def cell(c):
    return prose([h for _, h in sorted(c)])


def split_pairs(row):
    """A grid row holding two entries (bass / bass): each line goes to the nearest word in column 0."""
    anchors = sorted(row[0])
    out = [[[h] for _, h in anchors[i:i + 1]] + [[] for _ in row[1:]] for i in range(len(anchors))]
    for ci, c in enumerate(row[1:], 1):
        for y, h in sorted(c):
            k = min(range(len(anchors)), key=lambda i: abs(anchors[i][0] - y))
            out[k][ci].append(h)
    return [[prose(c) for c in r] for r in out]


def numbered_cols(pn, y0, y1):
    """Items numbered down columns ("1. actu<s>a</s>lly  9. ev<s>e</s>ry ..."), in number order."""
    items = {}
    for d in lines(pn, y0, y1):
        m = re.match(r'(\d+)\.\s*(.*)$', d['html'])
        items[int(m.group(1))] = m.group(2)
    return [items[k] for k in sorted(items)]


def dialogs(pages):
    """Numbered a./b. dialogues spread over (pn, y0, y1) ranges."""
    out = []
    for pn, y0, y1 in pages:
        for d in lines(pn, y0, y1):
            h = d['html']
            if re.match(r'\d+\.\s*a\.', plain(h)):
                out.append([unnum(h)])
            else:
                out[-1].append(h)
    return out


def sentences(pages):
    return [unnum(d['html']) for pn, y0, y1 in pages for d in lines(pn, y0, y1)]


blocks = []

# --- p.119: intro + Same Spelling, Different Pronunciation --------------------
blocks.append({'t': 'p', 'paras': [text(126, 430, 540), text(126, 545, 600)]})
blocks.append({'t': 'sec', 'id': 'same-spelling', 'title': plain(text(126, 610, 630))})
blocks.append({'t': 'p', 'paras': [text(126, 635, 670)]})
rows = []
for pn, y0, y1 in ((126, 676, 940), (127, 275, 505)):
    for r in grid(pn, y0, y1)[1:]:  # first grid row is the header
        rows += split_pairs(r)
blocks.append({'t': 'table', 'heads': ['', 'Pronunciation', 'Meaning'], 'rows': rows})

# --- p.120: Two Correct Pronunciations ----------------------------------------
blocks.append({'t': 'sec', 'id': 'two-correct', 'title': plain(text(127, 525, 545))})
blocks.append({'t': 'p', 'paras': [text(127, 550, 570)]})
rows = []
for word, pron, note in grid(127, 578, 765):
    # Two choices per word: each pronunciation line sits beside its note.
    pron, note = sorted(pron), sorted(note)
    for i, (_, p) in enumerate(pron):
        rows.append([unnum(cell(word)) if i == 0 else '', p, note[i][1] if i < len(note) else ''])
blocks.append({'t': 'table', 'rows': rows})

# --- p.121–122: Especially Difficult Words ------------------------------------
blocks.append({'t': 'sec', 'id': 'difficult', 'title': plain(text(128, 265, 285))})
blocks.append({'t': 'p', 'paras': [text(128, 290, 350)]})
rows = []
for pn, y0, y1 in ((128, 373, 922), (129, 275, 909)):
    rows += [[cell(c) for c in r] for r in grid(pn, y0, y1)[1:]]
for r in rows:
    r[0] = unnum(r[0])
    r[3] = r[3].replace('heirarchy', 'hierarchy')  # misprint in the book's example sentence
blocks.append({'t': 'table', 'numbered': True,
               'heads': ['Difficult Word', 'Correct Pronunciation', 'Incorrect Pronunciation', 'Example'], 'rows': rows})
blocks.append({'t': 'list', 'title': 'Practice Sentences', 'items': sentences([(130, 285, 420)])})

# --- p.123–124: Words with Dropped Syllables ----------------------------------
blocks.append({'t': 'sec', 'id': 'dropped', 'title': plain(text(130, 440, 460))})
blocks.append({'t': 'p', 'paras': [text(130, 465, 525)]})
blocks.append({'t': 'nums', 'cols': 4, 'items': numbered_cols(130, 530, 660)})
blocks.append({'t': 'dialog', 'title': 'Practice Dialogues',
               'items': dialogs([(130, 695, 920), (131, 270, 365)])})

# --- p.124: Words with Silent Letters -----------------------------------------
blocks.append({'t': 'sec', 'id': 'silent', 'title': plain(text(131, 383, 400))})
blocks.append({'t': 'p', 'paras': [text(131, 408, 425)]})
blocks.append({'t': 'table', 'rows': [[cell(a), cell(b)] for a, b in grid(131, 439, 918)]})
blocks.append({'t': 'p', 'paras': [text(131, 920, 940)]})

# --- p.125–126: Homophones -----------------------------------------------------
blocks.append({'t': 'sec', 'id': 'homophones', 'title': plain(text(132, 265, 285))})
blocks.append({'t': 'p', 'paras': [text(132, 288, 330)]})
blocks.append({'t': 'nums', 'cols': 3, 'items': numbered_cols(132, 340, 780)})
blocks.append({'t': 'list', 'title': 'Practice Sentences', 'sub': text(132, 812, 830),
               'items': sentences([(132, 835, 930), (133, 270, 330)])})
blocks.append({'t': 'dialog', 'title': 'Practice Dialogues', 'items': dialogs([(133, 375, 875)])})

def tidy_all(x):
    if isinstance(x, str):
        return tidy(x)
    if isinstance(x, list):
        return [tidy_all(v) for v in x]
    if isinstance(x, dict):
        return {k: v if k in ('t', 'id') else tidy_all(v) for k, v in x.items()}
    return x


blocks = tidy_all(blocks)
out = ROOT / 'data' / 'ch9.json'
out.write_text(json.dumps({'blocks': blocks}, ensure_ascii=False, indent=1), encoding='utf-8')
anchors = {b['title']: b['id'] for b in blocks if b['t'] == 'sec'}
link_toc('ch9', {'anchors': anchors, 'toc_title': 'Chapter 9: Memorizing the Exceptions'}, blocks)
print(f'wrote {out}: {len(blocks)} blocks')
