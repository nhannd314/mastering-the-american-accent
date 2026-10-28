"""Build data/ch3.json (Chapter 3: Consonants) from the book PDF.

Text is read straight from the PDF; this script only knows the layout:
which page/block holds what, and which CD track belongs to each part.
Block indices come from pymupdf's get_text('blocks') for this exact PDF.

Run from the project root:  python tools/build_ch3.py
"""
import json
import re
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parent.parent
doc = pymupdf.open(ROOT / 'Mastering the American Accent.pdf')
_blocks = {}


def lines(pn, i):
    """Non-empty lines of block i on (1-based) PDF page pn."""
    if pn not in _blocks:
        _blocks[pn] = doc[pn - 1].get_text('blocks')
    return [l.strip() for l in _blocks[pn][i][4].split('\n') if l.strip()]


def prose(ls):
    """Join wrapped lines into one paragraph, mending words hyphenated at line ends."""
    out = ''
    for l in ls:
        if out.endswith('-') and l[:1].islower():
            out = out[:-1] + l
        else:
            out = f'{out} {l}' if out else l
    return re.sub(r'\s+', ' ', out).strip()


def para(pn, i, skip=0):
    return prose(lines(pn, i)[skip:])


def head(pn, i):
    return lines(pn, i)[0]


def unnum(s):
    return re.sub(r'^\d+\.\s*', '', s)


def sound(pn, i):
    ls = lines(pn, i)
    return [ls[0], ls[1:]]


CD = 2
blocks = []

# --- p.29: intro + Forming American Consonants -------------------------------
blocks.append({'t': 'p', 'paras': [para(36, 3)]})
blocks.append({'t': 'sec', 'id': 'forming', 'title': head(36, 4)})
blocks.append({'t': 'p', 'paras': [para(36, 5), para(36, 6), para(36, 7)]})
blocks.append({'t': 'img', 'src': 'images/mouth-diagram.png', 'alt': 'Parts of the mouth used to form consonants'})

# --- p.30: Voiceless and Voiced Consonants ------------------------------------
blocks.append({'t': 'sec', 'id': 'voicing', 'title': head(37, 1), 'cd': CD, 'track': 13})
blocks.append({'t': 'p', 'paras': [para(37, 2), para(37, 3)]})
blocks.append({
    't': 'cons', 'paired': True, 'title': prose(lines(37, 4)),
    'heads': [prose(lines(37, 5) + lines(37, 6)), prose(lines(37, 7) + lines(37, 8) + lines(37, 9)), prose(lines(37, 10))],
    'rows': [[sound(37, i), sound(37, i + 1), para(37, i + 2)] for i in range(11, 35, 3)],
})

# --- p.31: More Voiced Consonants, /h/, Vowel Length ---------------------------
blocks.append({'t': 'p', 'title': head(38, 0), 'paras': [para(38, 0, skip=1)]})
blocks.append({'t': 'cons', 'rows': [[sound(38, i), para(38, i + 1)] for i in range(5, 19, 2)]})
blocks.append({'t': 'p', 'title': head(38, 1), 'paras': [para(38, 1, skip=1)]})
blocks.append({'t': 'cons', 'rows': [[sound(38, 19), para(38, 20)]]})
blocks.append({'t': 'sec', 'id': 'vowel-length', 'title': prose(lines(38, 2)), 'cd': CD, 'track': 14})
blocks.append({'t': 'p', 'paras': [para(38, 3)]})

# --- p.32: warning + practice --------------------------------------------------
blocks.append({'t': 'box', 'kind': 'warning', 'title': head(39, 7), 'text': para(39, 0)})

labels = lines(39, 8)  # voiceless | voiced | voiceless | voiced
groups = []
for sym_block, row_blocks in ((9, (10, 11, 12)), (13, (14, 15, 16))):
    syms = lines(39, sym_block)  # left pair, right pair
    rows = [lines(39, r) for r in row_blocks]  # num, a, b, num, a, b
    for side in (0, 1):
        groups.append({
            'heads': [f'{labels[0]} {syms[side * 2]}', f'{labels[1]} {syms[side * 2 + 1]}'],
            'rows': [r[side * 3 + 1: side * 3 + 3] for r in rows],
        })
blocks.append({'t': 'contrast', 'title': head(39, 1), 'cd': CD, 'track': 15, 'groups': groups})

ps = lines(39, 3)  # voiceless | voiced | then sentence pairs
blocks.append({'t': 'table', 'title': head(39, 2), 'cd': CD, 'track': 16, 'numbered': True,
               'heads': ps[:2], 'rows': [[unnum(ps[i]), ps[i + 1]] for i in range(2, len(ps), 2)]})
blocks.append({'t': 'list', 'title': head(39, 4), 'cd': CD, 'track': 17, 'items': [unnum(l) for l in lines(39, 5)]})

# --- p.33: Stops and Continuants ------------------------------------------------
blocks.append({'t': 'sec', 'id': 'stops', 'title': head(40, 0), 'cd': CD, 'track': 18})
blocks.append({'t': 'p', 'paras': [para(40, 1)]})
blocks.append({'t': 'p', 'title': head(40, 2), 'cd': CD, 'track': 19, 'paras': [para(40, 2, skip=1), para(40, 3)]})
blocks.append({'t': 'table', 'title': head(40, 4), 'sub': para(40, 4, skip=1), 'cd': CD, 'track': 20, 'numbered': True,
               'heads': lines(40, 10), 'rows': [lines(40, i)[1:] for i in range(11, 15)]})
blocks.append({'t': 'p', 'title': head(40, 5), 'cd': CD, 'track': 21, 'paras': [para(40, 5, skip=1)]})
pairs = sorted(lines(40, 8), key=lambda s: int(s.split('.')[0]))
blocks.append({'t': 'pairs', 'title': prose(lines(40, 6)), 'sub': para(40, 7), 'cd': CD, 'track': 22,
               'items': [unnum(p) for p in pairs]})

out = ROOT / 'data' / 'ch3.json'
out.write_text(json.dumps({'blocks': blocks}, ensure_ascii=False, indent=1), encoding='utf-8')
print(f'wrote {out} ({len(blocks)} blocks)')
