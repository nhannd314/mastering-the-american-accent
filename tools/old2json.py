"""Build data/<chapter>.json from the old HTML edition (old/index.php).

The old file already has clean text, letter highlighting (<strong>/<em>) and
the CD track buttons. This script maps its headings, paragraphs, lists,
tables and callouts onto the block types the site renders, cleans up the
"(" glyphs left over from the linking arcs, and adds the illustrations,
which the old edition lacks, cropped from the PDF (see pdf2json.py).

Usage (from the project root):  python tools/old2json.py ch4
"""
import html
import json
import re
import sys
from pathlib import Path

import pymupdf

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pdf2json import read_page, PDF  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OLD = ROOT / 'old' / 'index.php'

CHAPTERS = {
    'ch4': {
        'pages': (41, 72),
        'ids': ['t-sounds', 'fast-d', 'tr', 'dr', 'du', 'tu', 'ed', 'th', 'r', 'l', 'l-r', 'v', 'b-v', 'w',
                'v-w', 's-z', 'ng', 'clusters'],
        'skip': [r'^Song Lyrics'],  # copyrighted lyrics are left out
    },
    'ch5': {
        'pages': (73, 84),
        # h3 headings that are top-level sections in the book's table of contents
        'promote': ['Syllable Stress Changes'],
        # heading text -> anchor id (matches the links in data/front.json)
        'anchors': {
            'Stressed and Reduced Vowels': 'stressed', 'Dangers of Stressing the Wrong Syllable': 'dangers',
            'General Rules for Stress Placement': 'rules', 'Two-Syllable Words': 'two-syllable',
            'Noun and Verb Pairs': 'noun-verb', 'Words Ending in -tion and -ate': 'tion-ate',
            '-ate Endings of Verbs and Nouns': 'ate-endings', 'More Stressed Suffixes': 'suffixes',
            'Rules for Prefixes': 'prefixes', 'Syllable Stress Changes': 'stress-changes',
            'Reduced Vowels for Review': 'reduced-review',
        },
    },
    'ch6': {
        'pages': (85, 101),
        'toc_title': 'Chapter 6: Word Stress',
        'promote': ['Lengthening the Main Vowel in Stressed Words'],
        'anchors': {
            'Compound Nouns': 'compound', 'Proper Stress with Adjectives': 'adjectives',
            'Phrasal Verbs': 'phrasal', 'Noun Forms of Phrasal Verbs': 'phrasal-nouns',
            'Abbreviations and Numbers': 'abbreviations', 'Names of Places and People': 'names',
            'Word Stress Within a Sentence': 'sentence-stress',
            'Lengthening the Main Vowel in Stressed Words': 'lengthening',
            'Which Words Should I Stress?': 'which-words', 'Content Words': 'content',
            'Content Words in Detail: Verbs': 'content-verbs', 'Stress Nouns but Not Pronouns': 'nouns-pronouns',
            'Content Words in Detail: Adjectives': 'content-adjectives',
            'Reducing Vowels in Unstressed Words': 'reducing', 'Weak Forms': 'weak', 'Strong Forms': 'strong',
            'Thought Groups and Focus Words': 'thought-groups', 'Contrastive Stress': 'contrastive',
        },
    },
    'ch7': {
        'pages': (102, 107),
        'toc_title': 'Chapter 7: Intonation',
        'arrows': True,
        'anchors': {
            'Falling Intonation': 'falling', 'Statements': 'statements', 'Questions': 'questions',
            'Rising Intonation': 'rising', 'Non-final Intonation': 'non-final',
            'Unfinished Thoughts': 'unfinished', 'Introductory Words': 'introductory',
            'Series of Words': 'series', 'Expressing Choices': 'choices', 'Wavering Intonation': 'wavering',
        },
    },
    'ch8': {
        'pages': (108, 125),
        'toc_title': 'Chapter 8: Sound Like a True Native Speaker',
        'skip': [r'^Song Lyrics'],  # song lyrics are left out, as in Chapter 4
        'marks': True,
        'add_tracks': [('My American Accent', 4, 37)],
        # pictures in the old file -> (PDF page, y from, y to) to rebuild from the PDF text
        'inject': {'p111_0.png': (111, 628, 940), 'p113_0.png': (113, 735, 940)},
        # tables whose rows are out of line in the old file, read from the PDF instead
        'pdf_tables': [
            {'first': 'Insert a very quick', 'page': 111, 'y0': 525, 'y1': 600, 'cols': [216, 387, 476], 'heads': []},
            {'first': 'Formal, Careful', 'page': 123, 'y0': 360, 'y1': 940, 'cols': [190, 300, 415],
             'heads': ['Formal, Careful Speech', 'Informal, Relaxed Speech', 'Examples']},
            {'first': 'Formal, Careful', 'page': 124, 'y0': 325, 'y1': 600, 'cols': [185, 292, 405],
             'heads': ['Formal, Careful Speech', 'Informal, Relaxed Speech', 'Examples']},
        ],
        'anchors': {
            'Linking Words for Smoother Speech Flow': 'linking', 'Rules for Linking': 'linking-rules',
            'Linking Consonant to Vowel': 'cons-vowel', 'Linking Consonant to Same Consonant': 'cons-same',
            'Final Stop Between Consonants': 'final-stop', 'Linking Vowel to Vowel': 'vowel-vowel',
            'Linking Vowels Within a Word': 'vowels-within', 'Reducing Pronouns': 'pronouns',
            'Contractions': 'contractions', 'Commonly Contracted Words': 'contracted',
            'Conditional Tense and Contractions': 'conditional', 'Casual Versus Formal Speech': 'casual',
            'Rules and Patterns of Casual Speech': 'casual-rules', 'Commonly Confused Words': 'confused',
        },
    },
}
CHAPTERS['ch5']['toc_title'] = 'Chapter 5: Syllable Stress'
CHAPTERS['guide'] = {
    'pages': (134, 190),
    'toc_title': 'Native Language Guide',
    'languages': True,     # h1 = one language (a section), h2 = Consonants / Vowels / ... (kicker over its topics)
    'split_tables': True,  # tables that mix explanation lines with "typical mistake / should be" rows
    'syllables': (140, 'The correct number of syllables'),  # counts printed above the words
    # (pattern, replacement) on the finished text: the book's /I/ /eI/ /ou/ spellings and a few misprints
    'fixes': [
        (r'/((?:</?(?:strong|em)>)*)e((?:</?(?:strong|em)>)*)I((?:</?(?:strong|em)>)*)/', r'/\1e\2ɪ\3/'),
        (r'/((?:</?(?:strong|em)>)*)I((?:</?(?:strong|em)>)*)/', r'/\1ɪ\2/'),
        (r'/((?:</?(?:strong|em)>)*)ou((?:</?(?:strong|em)>)*)/', r'/\1oʊ\2/'),
        (r'Reiview', 'Review'), (r'pro- nounced', 'pronounced'), (r'spelling with', 'spelled with'), (r'/w” sounds', '/w/ sounds'),
        (r'inadvertantly', 'inadvertently'), (r'(\w|</(?:strong|em)>) \.$', r'\1.'),
    ],
    'anchors': {
        'Chinese': 'chinese', 'Farsi': 'farsi', 'Filipino Languages': 'filipino', 'French': 'french',
        'German': 'german', 'Indian Languages': 'indian', 'Indonesian': 'indonesian', 'Japanese': 'japanese',
        'Korean': 'korean', 'Portuguese': 'portuguese', 'Russian': 'russian', 'Spanish': 'spanish',
        'Vietnamese': 'vietnamese',
    },
}

SPEAKER = re.compile(r'^(?!(?:Note|Notes|Example|Examples|Exceptions?|Remember|Answers?|Hint|Say)\b)'
                     r'([A-Z][A-Za-z]+(?: [A-Z][a-z]+)?):\s*(.*)$')


# ---------------------------------------------------------------------------
# Inline HTML -> "rich" text (plain text plus <strong>/<em>)

def rich(s):
    s = re.sub(r'<(?!/?(?:strong|em)>)[^>]*>', '', s)
    s = html.unescape(s).replace(' ', ' ').replace('/q/', '/θ/')
    for t in ('strong', 'em'):
        s = re.sub(rf'</{t}>(\s*)<{t}>', r'\1', s)
        s = re.sub(rf'<{t}>(\s*)</{t}>', r'\1', s)
    s = re.sub(r'(^|\s)\((?=\s|$)', r'\1', s)  # stray "(" from linking arcs
    s = re.sub(r'\s+B1(?=\s|$|<)', '', s)       # stray figure label
    s = re.sub(r'\s+', ' ', s).strip()
    # Move whitespace out of tags: "<em>t </em>" -> "<em>t</em> "
    s = re.sub(r'\s+(</(?:strong|em)>)', r'\1 ', s)
    s = re.sub(r'(<(?:strong|em)>)\s+', r' \1', s)
    # The PDF's symbol font put "q" where θ belongs, sometimes wrapped in tags: /<em>q</em>/.
    s = re.sub(r'/((?:</?(?:strong|em)>)*)q((?:</?(?:strong|em)>)*)/', r'/\1θ\2/', s)
    return re.sub(r'\s+', ' ', s).strip()


def plain(s):
    return re.sub(r'<[^>]+>', '', s)


def unwrap(s):
    """Drop tags wrapping the whole string (headings are styled already)."""
    while True:
        m = re.fullmatch(r'<(strong|em)>(.*)</\1>', s)
        if not m or re.search(rf'</{m.group(1)}>', m.group(2)):
            return s
        s = m.group(2).strip()


def heading(s):
    return unwrap(re.sub(r'</?strong>', '', rich(s)))


def strip_num(s):
    return re.sub(r'^((?:<[^>]+>)*)\s*\d+\.\s*', r'\1', s)


def is_marker(s):
    return bool(re.fullmatch(r'(\s*/[^/\s]+/\s*)+', plain(s)))


# ---------------------------------------------------------------------------
# Reading the old file into top-level elements

def elements(cfg):
    src = OLD.read_text(encoding='utf-8').split('\n')
    a, b = cfg['pages']
    start = next(i for i, l in enumerate(src) if f'id="p{a}"' in l)
    end = next(i for i, l in enumerate(src) if f'id="p{b + 1}"' in l)
    els, i, page = [], start, a
    while i < end:
        line = src[i]
        if line.startswith('<div class="tblwrap">') or line.startswith('<ol'):
            close = '</table>' if line.startswith('<div') else '</ol>'
            j = i
            while close not in src[j]:
                j += 1
            chunk = '\n'.join(src[i:j + 1])
            i = j + 1
            if close == '</ol>':
                els.append({'k': 'ol', 'items': [rich(x) for x in re.findall(r'<li>(.*?)</li>', chunk, re.S)], 'page': page})
            else:
                rows = [[rich(c) for c in re.findall(r'<td[^>]*>(.*?)</td>', r, re.S)]
                        for r in re.findall(r'<tr>(.*?)</tr>', chunk, re.S)]
                els.append({'k': 'table', 'rows': rows, 'page': page})
            continue
        i += 1
        m = re.match(r'<div class="pagemark" id="p(\d+)"', line)
        if m:
            page = int(m.group(1))
            els.append({'k': 'page', 'page': page})
            continue
        m = re.match(r'<button class="trk"[^>]*data-cd="(\d+)" data-track="(\d+)"', line)
        if m:
            els.append({'k': 'trk', 'cd': int(m.group(1)), 'track': int(m.group(2)), 'page': page})
            continue
        m = re.match(r'<(h[1-5]|p|figure)(?: [^>]*?class="([^"]*)")?[^>]*>(.*)</\1>\s*$', line)
        if not m:
            continue
        tag, cls, inner = m.group(1), m.group(2) or '', m.group(3)
        if tag == 'figure':
            # Some pages were saved as a picture only; remember where, so the text can be put back from the PDF.
            img = re.search(r'src="(?:[^"]*/)?([^"/]+)"', inner)
            if img:
                els.append({'k': 'oldfig', 'src': img.group(1), 'page': page})
            continue
        if 'ch-label' in cls or (tag == 'h1' and not (cfg.get('languages') and plain(rich(inner)).strip() in cfg['anchors'])):
            continue
        if cfg.get('languages'):
            k = {'h1': 'sec', 'h2': 'kick', 'h3': 'h3', 'h4': 'h4', 'h5': 'h5'}.get(tag)
        else:
            k = {'h2': 'sec', 'h3': 'h3', 'h4': 'h4', 'h5': 'h5'}.get(tag)
        if k == 'h3' and plain(rich(inner)).strip() in cfg.get('promote', []):
            k = 'sec'
        # A short paragraph that is bold all the way through is a small heading.
        if tag == 'p' and re.fullmatch(r'<strong>[^<]{3,60}</strong>', rich(inner)) and 'callout' not in cls:
            k = 'h5'
        text = rich(inner)
        if re.fullmatch(r'\s*(\d+\s+Mastering the American Accent|Chapter \w+:.*\d+)\s*', plain(text)):
            continue  # running footer
        if not k:
            k = 'callout' if 'callout-title' in cls else ('pind' if 'ind' in cls.split() else 'p')
            if re.fullmatch(r'(Warning: .{4,30}|Study Tip|Advice from a Successful Student)', plain(text).strip()):
                k = 'callout'
        if not plain(text).strip():
            continue
        els.append({'k': k, 'html': inner, 'text': text, 'page': page})
    return els


# ---------------------------------------------------------------------------
# Intonation arrows (Chapter 7): the old file kept only empty arrow rows, so the
# sentences are re-marked from the PDF and scattered numbered lines regrouped.

ARROWS = '\x02\x03↗↘'


def akey(s):
    s = re.sub(r'^\s*\d+\.\s*', '', plain(s))
    return re.sub(r'[^0-9a-z]+', '', s.lower())


def arrow_only(s):
    return not plain(s).strip(ARROWS + '  ')


def apply_arrows(els, cfg):
    from arrows import arrowed_lines
    lines = [segs for _, segs in arrowed_lines(str(PDF), range(cfg['pages'][0], cfg['pages'][1] + 1))]
    look = {}
    for i, segs in enumerate(lines):
        look.setdefault(akey(' '.join(segs)), segs)
        if i + 1 < len(lines) and len(segs) == len(lines[i + 1]) == 1:
            look.setdefault(akey(segs[0] + ' ' + lines[i + 1][0]), [segs[0] + ' ' + lines[i + 1][0]])
    for s in lines:
        for x in s:
            look.setdefault(akey(x), [x])

    def mark(s):
        hit = look.get(akey(s))
        if not hit or len(hit) != 1:
            return s.strip(ARROWS + ' ')
        return hit[0] if num_of(s) is not None else re.sub(r'^\s*\d+\.\s*', '', hit[0])

    out = []
    for el in els:
        k = el['k']
        if k in ('p', 'pind'):
            if arrow_only(el['text']):
                continue
            hit = look.get(akey(el['text']))
            if hit and num_of(el['text']) is not None:
                el = {'k': 'arow', 'rows': [hit], 'page': el['page']}
        elif k == 'ol':
            el['items'] = [mark(x) for x in el['items'] if not arrow_only(x)]
        elif k == 'table':
            rows = []
            for r in el['rows']:
                if all(arrow_only(c) for c in r):
                    continue
                hit = look.get(akey(' '.join(c for c in r if plain(c).strip())))
                filled = [j for j, c in enumerate(r) if plain(c).strip()]
                if hit and len(hit) > 1 and len(hit) == len(filled):
                    r = list(r)
                    for j, seg in zip(filled, hit):
                        r[j] = seg  # keep each segment in its column, under its header
                    rows.append(r)
                else:
                    rows.append([mark(c) for c in r])
            el['rows'] = rows
            if rows and all(num_of(r[0]) is not None for r in rows):
                el = {'k': 'arow', 'rows': [[c for c in r if plain(c).strip()] for r in rows], 'page': el['page']}
        if k in ('p', 'pind', 'h5', 'callout') and el['k'] == k:
            el['text'] = el['text'].strip(ARROWS + ' ')
        prev = next((x for x in reversed(out) if x['k'] != 'page'), None)
        if el['k'] == 'arow' and prev and prev['k'] == 'arow':
            prev['rows'] += el['rows']
            continue
        out.append(el)
    for el in out:
        if el['k'] == 'arow':
            el['k'] = 'table'
    return out


# ---------------------------------------------------------------------------
# Linking marks (Chapter 8): ties between linked words, inserted /y/ /w/ glides and
# silent letters only exist in the PDF, so matching lines are taken from there.
# Pages the old file kept only as a picture are rebuilt from the PDF as well.

DIALOG = re.compile(r'^(?:(\d+)\.\s*)?([ab])\.\s')


def mkey(s):
    """Match key that ignores the marks: drop glides/silent letters, ties count as spaces."""
    s = re.sub(r'<(sup|s)>.*?</\1>', '', s).replace('‿', ' ')
    s = re.sub(r'\s<em>[a-z](?:\s[a-z])*</em>(?=\s|$)', '', s)  # stray silent letters in the old file
    s = re.sub(r'^\s*(\d+\.\s*)?[ab]\.\s', '', plain(s))  # dialogue speaker letters
    return akey(s)


def pdf_elements(lines, page):
    """Old-file style elements from PDF lines: headings, dialogue lines, two-column numbered rows, paragraphs."""
    out, para = [], []

    def flush():
        if para:
            out.append({'k': 'p', 'text': ' '.join(para), 'html': ' '.join(para), 'page': page})
            para.clear()
    rows = {}
    for d in lines:
        rows.setdefault(round(d['y']), []).append(d['html'])
    for y in sorted(rows):
        cells = rows[y]
        if len(cells) == 1 and re.fullmatch(r'<em>[^<]+</em>', cells[0]):
            flush()
            out.append({'k': 'h4', 'html': cells[0], 'text': cells[0], 'page': page})
        elif len(cells) > 1:
            flush()
            if out and out[-1]['k'] == 'table':
                out[-1]['rows'].append(cells)
            else:
                out.append({'k': 'table', 'rows': [cells], 'page': page})
        elif DIALOG.match(plain(cells[0])) or (out and out[-1]['k'] == 'dlg' and not para):
            flush()
            if out and out[-1]['k'] == 'dlg':
                out[-1]['lines'].append(cells[0])
            else:
                out.append({'k': 'dlg', 'lines': [cells[0]], 'page': page})
        else:
            para.append(cells[0])
    flush()
    return out


def apply_marks(els, cfg):
    from pdflines import marked_lines
    import pymupdf
    doc = pymupdf.open(str(PDF))
    look = {}
    for pn in range(cfg['pages'][0], cfg['pages'][1] + 1):
        ls = marked_lines(doc, pn)
        for i, d in enumerate(ls):
            look.setdefault(mkey(d['html']), d['html'])
            if i + 1 < len(ls):
                look.setdefault(mkey(d['html'] + ' ' + ls[i + 1]['html']), d['html'] + ' ' + ls[i + 1]['html'])

    def mark(s):
        if re.fullmatch(r'\s*(<em>[a-z]</em>\s*)+', s):
            return ''  # silent letters the old file printed on their own
        key = mkey(s)
        hit = look.get(key) if len(key) > 2 else None
        if not hit:
            return s
        if num_of(s) is None and not re.match(r'^\d+\.\s*a\.\s', plain(hit)) \
                and not (DIALOG.match(plain(hit)) and not DIALOG.match(plain(s))):
            hit = re.sub(r'^\s*\d+\.\s*', '', hit)
        return hit

    out, drop = [], False
    tables = list(cfg.get('pdf_tables', []))
    for el in els:
        k = el['k']
        if k == 'oldfig' and el['src'] in cfg.get('inject', {}):
            pn, y0, y1 = cfg['inject'][el['src']]
            out += pdf_elements(marked_lines(doc, pn, y0, y1), pn)
            drop = True  # the old file's leftovers of the picture follow
            continue
        if drop and k in ('p', 'pind'):
            continue
        if drop and k == 'trk':
            # the track belongs to the last heading of the rebuilt part
            h = max((i for i, x in enumerate(out) if x['k'] == 'h4'), default=None)
            if h is not None and not (h + 1 < len(out) and out[h + 1]['k'] == 'trk'):
                out.insert(h + 1, el)
                continue
        drop = False
        if k in ('p', 'pind'):
            el['text'] = mark(el['text'])
        elif k == 'ol':
            el['items'] = [mark(x) for x in el['items']]
        elif k == 'table':
            first = plain(next((c for r in el['rows'] for c in r if plain(c).strip()), ''))
            spec = next((t for t in tables if first.startswith(t['first'])), None)
            if spec:
                tables.remove(spec)
                out.append({'k': 'ptable', 'blk': pdf_table(doc, spec), 'page': el['page']})
                drop = True
                continue
            out += split_table([[mark(c) for c in r] for r in el['rows']], el['page'])
            continue
        out.append(el)
    return regroup_dialogs(out)


def pdf_table(doc, spec):
    """A table read from the PDF: one row per entry in the first columns; the example
    lines in the last column go to the entry they sit next to."""
    from pdflines import marked_lines
    xs = spec['cols']
    cells = sorted((d['y'], sum(d['x'] >= x - 4 for x in xs[1:]), d['html'])
                   for d in marked_lines(doc, spec['page'], spec['y0'], spec['y1']))
    last = len(xs) - 1
    anchors = []
    for y, c, h in cells:
        if c < last:
            if not anchors or y - anchors[-1]['last'] >= 8:
                anchors.append({'y': y, 'last': y, 'cols': [[] for _ in xs]})
            anchors[-1]['cols'][c].append(h)
            anchors[-1]['last'] = y
    for y, c, h in cells:
        if c == last and anchors:
            min(anchors, key=lambda a: abs(a['y'] - y))['cols'][c].append(h)
    rows = [[(' ' if i == last else ' / ').join(a['cols'][i]) for i in range(len(xs))] for a in anchors]
    blk = {'t': 'table', 'rows': rows}
    if spec['heads']:
        blk['heads'] = spec['heads']
    return blk


def split_table(rows, page):
    """A grid that mixes instruction lines (text in the first cell only) with table rows."""
    def lone(r):
        filled = [i for i, c in enumerate(r) if plain(c).strip()]
        return filled == [0] and num_of(r[0]) is None and (len(plain(r[0])) > 40 or plain(r[0]).rstrip().endswith(':'))
    if max(len(r) for r in rows) < 2 or not any(lone(r) for r in rows):
        return [{'k': 'table', 'rows': rows, 'page': page}]
    def tail(r):
        filled = [i for i, c in enumerate(r) if plain(c).strip()]
        t = plain(r[0]).strip()
        return filled == [0] and len(t) < 30 and re.match(r'[a-z]', t) and not DIALOG.match(t)
    out = []
    for r in rows:
        if out and out[-1]['k'] == 'p' and tail(r):
            t = out[-1]['text']
            out[-1]['text'] = t[:-1] + r[0].strip() if t.endswith('-') else t + ' ' + r[0].strip()
        elif lone(r):
            if out and out[-1]['k'] == 'p':
                out[-1]['text'] += ' ' + r[0]
            else:
                out.append({'k': 'p', 'text': r[0], 'html': r[0], 'page': page})
        else:
            if not out or out[-1]['k'] != 'table':
                out.append({'k': 'table', 'rows': [], 'page': page})
            out[-1]['rows'].append(r)
    return out


def regroup_dialogs(els):
    """Gather a./b. dialogue lines scattered over paragraphs, lists and one-column tables into one dialogue."""
    def lines_of(el):
        if el['k'] in ('p', 'pind'):
            return [el['text']]
        if el['k'] in ('ol', 'dlg'):
            return el['items'] if el['k'] == 'ol' else el['lines']
        if el['k'] == 'table' and all(sum(1 for c in r if plain(c).strip()) <= 1 for r in el['rows']):
            return [c for r in el['rows'] for c in r if plain(c).strip()]
        return None

    def dialogish(el):
        ls = lines_of(el)
        if not ls:
            return False
        if el['k'] in ('ol', 'dlg'):
            return True
        return all(DIALOG.match(plain(x)) or re.match(r'[a-z]', plain(x)) for x in ls)

    out, i = [], 0
    while i < len(els):
        el = els[i]
        if el['k'] in ('p', 'pind', 'ol', 'table', 'dlg') and dialogish(el):
            j, run = i, []
            while j < len(els) and (els[j]['k'] == 'page' or (els[j]['k'] in ('p', 'pind', 'ol', 'table', 'dlg') and dialogish(els[j]))):
                if els[j]['k'] != 'page':
                    run += lines_of(els[j])
                j += 1
            if sum(1 for x in run if DIALOG.match(plain(x))) >= 2:
                out.append({'k': 'dialog', 'groups': dialog_groups(run), 'page': el['page']})
                out += [x for x in els[i:j] if x['k'] == 'page']
                i = j
                continue
        if el['k'] == 'dlg':
            el = {'k': 'dialog', 'groups': dialog_groups(el['lines']), 'page': el['page']}
        out.append(el)
        i += 1
    return out


def dialog_groups(lines):
    numbered = any(DIALOG.match(plain(x)) and DIALOG.match(plain(x)).group(1) for x in lines)
    groups, who = [], None
    for x in lines:
        m = DIALOG.match(plain(x))
        if not m and groups and re.match(r'[a-z]', plain(x)):
            groups[-1][-1] += ' ' + x  # wrapped line
            continue
        n = re.match(r'^\s*(\d+)\.\s+(?![ab]\.)', plain(x))
        if n and numbered:
            groups.append(['a. ' + re.sub(r'^\s*\d+\.\s*', '', x)])
            who = 'a'
            continue
        if m:
            who = m.group(2)
            x = re.sub(r'^\s*\d+\.\s*', '', x)
        else:
            who = 'b' if who == 'a' else 'a'
            x = f'{who}. {x}'
        if not groups or (numbered and m and m.group(1)):
            groups.append([])
        groups[-1].append(x)
    return groups


# ---------------------------------------------------------------------------
# Tables and lists

def num_of(cell):
    m = re.match(r'^\s*(\d+)\.(?:\s|$)', plain(cell))
    return int(m.group(1)) if m else None


def convert_table(rows):
    rows = [r for r in rows if any(plain(c).strip() for c in r)]
    if not rows:
        return None
    width = max(len(r) for r in rows)
    keep = [c for c in range(width) if any(c < len(r) and plain(r[c]).strip() for r in rows)]
    rows = [[r[c] if c < len(r) else '' for c in keep] for r in rows]
    width = len(keep)
    if width == 1:
        if all(num_of(r[0]) is not None for r in rows):
            return {'t': 'nums', 'cols': 1, 'items': [strip_num(r[0]) for r in rows]}
        return {'t': 'p', 'paras': [r[0] for r in rows]}

    def segs(r):
        """Numbered items in a row: [number, column of the number, [(column, cell), ...]]."""
        out = []
        for ci, c in enumerate(r):
            if not plain(c).strip():
                continue
            n = num_of(c)
            if n is not None:
                rest = strip_num(c)
                out.append([n, ci, [(ci, rest)] if plain(rest).strip() else []])
            elif out:
                out[-1][2].append((ci, c))
            else:
                return None
        return out

    def sym_row(r):
        return all(re.fullmatch(r'/[^/]+/', plain(c).strip()) for c in r if plain(c).strip())
    if width == 2 and sum(sym_row(r) for r in rows) >= 2 and any(num_of(r[0]) is not None for r in rows):
        # Pairs grouped under sound heads (/k/ /g/, /t/ /d/ ...), numbered straight through.
        top, groups = [], []
        for r in rows:
            if num_of(r[0]) is not None and groups:
                groups[-1]['rows'].append([strip_num(r[0]), r[1]])
            elif sym_row(r) or '/' in plain(' '.join(r)):
                groups.append({'heads': [unwrap(c) for c in r], 'rows': []})
            else:
                top = [unwrap(c) for c in r]
        if top:
            for g in groups:
                g['heads'] = [f'{t} {h}'.strip() for t, h in zip(top, g['heads'])]
        return {'t': 'contrast', 'groups': groups}

    parsed = [segs(r) for r in rows]
    first = next((i for i, s in enumerate(parsed) if s), None)
    # Numbered layout, as long as every row below the header is numbered (otherwise keep the grid as is).
    if first is not None and all(parsed[first:]):
        items = sorted((sg for s in parsed[first:] for sg in s), key=lambda sg: sg[0])
        for sg in list(items):
            m = re.match(r'^(.*?)\s+(\d+)\.\s+(.*)$', sg[2][-1][1]) if sg[2] else None
            n = int(m.group(2)) if m else 0
            if n > sg[0] and n not in {x[0] for x in items}:
                sg[2][-1] = (sg[2][-1][0], m.group(1))
                items.append([n, sg[1], [(sg[2][-1][0], m.group(3))]])
        items.sort(key=lambda sg: sg[0])
        w = max(len(sg[2]) for sg in items)
        per_row = max(len(s) for s in parsed[first:])
        if w == 1:
            return {'t': 'nums', 'cols': per_row, 'items': [sg[2][0][1] for sg in items]}
        # Column heads: header text sitting over each data column (and the gap before it).
        ref = max(parsed[first], key=lambda sg: len(sg[2]))
        heads, prev = [], ref[1] - 1
        for ci, _ in ref[2]:
            parts = [unwrap(r[x]) for r in rows[:first] for x in range(prev + 1, ci + 1) if plain(r[x]).strip()]
            heads.append(' '.join(parts))
            prev = ci
        heads = (heads + [''] * w)[:w]
        cells = [unwrap(c) for r in rows[:first] for c in r if plain(c).strip()]
        if '' in heads and len(cells) == w:
            heads = cells
        if not any(heads):
            heads = []
        body = [[t for _, t in sg[2]] + [''] * (w - len(sg[2])) for sg in items]
        if w == 2:
            return {'t': 'contrast', 'heads': heads or ['', ''], 'rows': body}
        blk = {'t': 'table', 'numbered': True, 'rows': body}
        if heads:
            blk['heads'] = heads
        return blk

    # Dialogue laid out as a grid: "Name:" (sometimes with the line in the same cell), text, continuations.
    who = [re.match(r'^([A-Z][a-z]+):\s*(.*)$', plain(r[0]).strip()) for r in rows]
    if width == 2 and who[0] and all(w or not plain(r[0]).strip() for w, r in zip(who, rows)):
        lines = []
        for w, r in zip(who, rows):
            text = ' '.join(x for x in ([r[0].split(':', 1)[1].strip()] if w else []) + [r[1]] if plain(x).strip())
            if w:
                lines.append([w.group(1), text, ''])
            else:
                lines[-1][1] += ' ' + text
        return {'t': 'script', 'lines': lines}
    # Phrase + italic label rows (e.g. "You did?" / curious), with instruction lines between them.
    labelled = [width == 2 and re.fullmatch(r'\s*<em>[^<]+</em>\s*', r[1]) is not None for r in rows]
    if sum(labelled) >= 3 and all(lb or not plain(r[1]).strip() for lb, r in zip(labelled, rows)):
        out = []
        for lb, r in zip(labelled, rows):
            if lb:
                if not out or out[-1]['t'] != 'table':
                    out.append({'t': 'table', 'rows': []})
                out[-1]['rows'].append([r[0], r[1].strip()])
            elif out and out[-1]['t'] == 'p':
                out[-1]['paras'][-1] += ' ' + r[0]
            else:
                out.append({'t': 'p', 'paras': [r[0]]})
        return out

    first = rows[0]
    header = len(rows) > 1 and all(
        re.fullmatch(r'\s*<(strong|em)>.*</\1>\s*', c) or plain(c).strip().endswith(':') or re.fullmatch(r'/.+/', plain(c).strip())
        for c in first if plain(c).strip())
    if header:
        return {'t': 'table', 'heads': [unwrap(c) for c in first],
                'rows': [r + [''] * (width - len(r)) for r in rows[1:]]}
    cells = [c for r in rows for c in r if plain(c).strip()]
    if all(len(plain(c)) < 30 for c in cells):
        return {'t': 'words', 'groups': [{'words': cells}]}
    return {'t': 'table', 'rows': [r + [''] * (width - len(r)) for r in rows]}


def convert_ol(items):
    items = [x for x in items if plain(x).strip()]
    if items and re.match(r'^a\.\s', plain(items[0])):
        out, nxt = [], 'b'
        for x in items:
            if re.match(r'^a\.\s', plain(x)):
                out.append([x])
                nxt = 'b'
            elif out:
                if not re.match(r'^[a-z]\.\s', plain(x)):
                    x = f'{nxt}. {x}'
                out[-1].append(x)
                nxt = 'a' if nxt == 'b' else 'b'
        return {'t': 'dialog', 'items': out}
    return {'t': 'list', 'items': items}


# ---------------------------------------------------------------------------
# Assembly

class Builder:
    def __init__(self, cfg):
        self.cfg, self.out, self.pending = cfg, [], None
        self.ids = list(cfg.get('ids', []))
        self.track = None
        self.kicker = None  # Native Language Guide: "Consonants" / "Vowels" over the topics that follow

    def take_track(self):
        t, self.track = self.track, None
        return t or {}

    def flush(self):
        p, self.pending = self.pending, None
        if p and p.get('title'):
            anchor = self.cfg.get('anchors', {}).get(plain(p['title']).strip())
            if anchor:
                p['id'] = anchor
        if p and (p.get('title') or p.get('track')):
            self.out.append({'t': 'p', 'paras': [], **p})

    def emit(self, blk):
        pend, self.pending = self.pending, None
        if pend and pend.get('title'):
            anchor = self.cfg.get('anchors', {}).get(plain(pend['title']).strip())
            if anchor:
                pend['id'] = anchor
        extra = dict(pend or {})
        for k, v in self.take_track().items():
            extra.setdefault(k, v)
        if extra.get('sub') and blk['t'] == 'p' and not extra.get('title'):
            blk['paras'].insert(0, extra.pop('sub'))
        for k, v in extra.items():
            if v and not blk.get(k):
                blk[k] = v
        last = self.out[-1] if self.out else None
        if last and not extra and last['t'] == blk['t'] and blk['t'] in ('p', 'dialog', 'list', 'script'):
            key = {'p': 'paras', 'dialog': 'items', 'list': 'items', 'script': 'lines'}[blk['t']]
            last[key] += blk[key]
            return
        self.out.append(blk)

    def run(self, els):
        i = 0
        while i < len(els):
            e = els[i]
            k = e['k']
            nxt = els[i + 1] if i + 1 < len(els) else None

            if k == 'page':
                pass
            elif k == 'fig':
                self.out.append({'t': 'img', 'src': e['src'], 'alt': e['alt'], 'w': e['w']})
            elif k == 'trk':
                t = {'cd': e['cd'], 'track': e['track']}
                last = self.out[-1] if self.out else None
                if self.pending and not self.pending.get('track'):
                    self.pending.update(t)
                elif last and last['t'] in ('sec', 'box') and not last.get('track') and not self.pending \
                        and (last['t'] == 'sec' or not last.get('children')):
                    last.update(t)
                else:
                    self.track = t
            elif k == 'sec':
                self.flush()
                self.kicker = None
                title = heading(e['html'])
                anchor = self.cfg.get('anchors', {}).get(plain(title).strip())
                blk = {'t': 'sec', 'id': anchor or (self.ids.pop(0) if self.ids else None), 'title': title}
                blk.update(self.take_track())
                self.out.append(blk)
            elif k == 'kick':
                self.flush()
                title = heading(e['html'])
                ahead = next((x for x in els[i + 1:] if x['k'] not in ('page', 'trk')), None)
                if ahead and ahead['k'] == 'h3':
                    self.kicker = title
                else:  # a part with no topics under it ("Intonation", "Linking"): it is the topic
                    self.pending = {'title': title, **self.take_track()}
                    self.kicker = None
            elif k in ('h3', 'h4'):
                title = heading(e['html'])
                if any(re.search(p, plain(title)) for p in self.cfg.get('skip', [])):
                    self.flush()
                    while i + 1 < len(els) and els[i + 1]['k'] not in ('sec', 'h3', 'h4', 'callout')                             and not (els[i + 1]['k'] == 'trk' and i + 2 < len(els)
                                     and els[i + 2]['k'] in ('sec', 'h3', 'h4', 'callout')):
                        i += 1  # (a track right before the next heading belongs to that heading)
                    self.track = None
                    i += 1
                    continue
                self.flush()
                if self.cfg.get('languages') and k == 'h3' and nxt and nxt['k'] == 'h4':
                    self.kicker = title  # "Common Vowel Errors" over its first topic
                    i += 1
                    continue
                self.pending = {'title': title, **self.take_track()}
                if self.kicker:
                    self.pending['kicker'], self.kicker = self.kicker, None
            elif k == 'h5':
                text = e['text']
                title = heading(e['html'])
                author = nxt and nxt['k'] == 'pind' and re.fullmatch(r'<em>[^<]{2,40}</em>', nxt['text'].strip())
                if plain(title).startswith(('Advice from', 'Warning', 'Study Tip')):
                    i = self.box(els, i, plain(title))
                    continue
                if author:
                    quote = re.sub(r'^(<strong>)?(\s*/[^/\s]+/)+\s*(</strong>)?\s*', '', text)
                    quote = unwrap(re.sub(r'</?strong>', '', quote))
                    last = self.out[-1] if self.out else None
                    if last and last['t'] == 'sec' and not last.get('quote'):
                        last['quote'], last['by'] = quote, plain(nxt['text'])
                    else:
                        self.emit({'t': 'quote', 'text': quote, 'by': plain(nxt['text'])})
                    i += 2
                    continue
                if self.pending and self.pending.get('title') and not self.pending.get('sub'):
                    self.pending['sub'] = plain(title)
                else:
                    self.flush()
                    self.pending = {'title': title, **self.take_track()}
            elif k == 'callout':
                i = self.box(els, i, plain(e['text']))
                continue
            elif k in ('p', 'pind'):
                i = self.paragraphs(els, i)
                continue
            elif k == 'ol':
                items = [x for x in e['items'] if plain(x).strip()]
                # A lead-in sentence ("... For example:") is not one of the numbered items.
                if len(items) > 1 and plain(items[0]).rstrip().endswith(':') and len(plain(items[0])) > 40:
                    self.emit({'t': 'p', 'paras': [items.pop(0)]})
                    self.out.append(convert_ol(items))
                else:
                    self.emit(convert_ol(items))
            elif k == 'dialog':
                self.emit({'t': 'dialog', 'items': e['groups']})
            elif k == 'ptable':
                self.emit(e['blk'])
            elif k == 'table':
                blk = convert_table(e['rows'])
                for b in (blk if isinstance(blk, list) else [blk] if blk else []):
                    self.emit(b)
            i += 1
        self.flush()
        return self.out

    def paragraphs(self, els, i):
        """Plain paragraphs, or a script (speaker lines with IPA markers above)."""
        e = els[i]
        if SPEAKER.match(plain(e['text'])) or is_marker(e['text']):
            lines, ipa = [], ''
            while i < len(els) and els[i]['k'] in ('p', 'pind'):
                t = els[i]['text']
                i += 1
                if is_marker(t):
                    ipa = re.sub(r'\s+', '  ', plain(t).strip())
                    continue
                m = SPEAKER.match(plain(t))
                if m:
                    body = re.sub(r'^[^:]*:\s*', '', t, count=1)
                    lines.append([m.group(1), body, ipa])
                elif lines and not ipa:
                    lines[-1][1] = f'{lines[-1][1]} {t}'
                else:
                    lines.append(['', t, ipa])
                ipa = ''
            self.emit({'t': 'script', 'lines': lines})
            return i
        # An indented paragraph right under an exercise title, before its list/table, is its intro.
        nxt = next((x for x in els[i + 1:] if x['k'] not in ('trk', 'page')), None)
        if e['k'] == 'pind' and self.pending and self.pending.get('title') and not self.pending.get('sub') \
                and nxt and nxt['k'] in ('ol', 'table'):
            self.pending['sub'] = e['text']
            return i + 1
        self.emit({'t': 'p', 'paras': [e['text']]})
        return i + 1

    def box(self, els, i, title):
        self.flush()
        track = self.take_track()
        j = i + 1
        body = []
        while j < len(els) and els[j]['k'] not in ('sec', 'h3', 'h4', 'callout', 'trk', 'fig') and not (
                els[j]['k'] == 'h5' and body):
            # A plain paragraph after the box's table is body text again (the box ends at its table).
            if els[j]['k'] == 'p' and any(b['k'] == 'table' for b in body):
                break
            if els[j]['k'] != 'page':
                body.append(els[j])
            j += 1
        if title.startswith('Advice'):
            by = ''
            if body and body[-1]['k'] == 'pind' and re.fullmatch(r'<em>[^<]{2,60}</em>', body[-1]['text'].strip()):
                by = plain(body.pop()['text']).strip()
            parts = []
            for b in body:
                if b['k'] == 'table':
                    parts += [c for r in b['rows'] for c in r]
                elif b.get('text'):
                    parts.append(b['text'])
            text = unwrap(re.sub(r'</em>\s*<em>', ' ', ' '.join(parts)))
            self.out.append({'t': 'box', 'kind': 'advice', 'title': title, 'text': plain(text), 'by': by, **track})
            return j
        kind = 'warning' if title.startswith('Warning') else 'tip' if title.startswith('Study Tip') else 'note'
        sub = Builder({})
        sub.run(body)
        blk = {'t': 'box', 'kind': kind, 'title': title, 'children': sub.out, **track}
        if kind == 'tip':
            blk['img'] = 'images/study-tip.png'
        self.out.append(blk)
        return j


# ---------------------------------------------------------------------------
# Illustrations from the PDF

def norm(s):
    return re.sub(r'[^a-z]', '', plain(s).lower())[:40]


def add_figures(els, cfg, chapter):
    doc = pymupdf.open(PDF)
    figdir = ROOT / 'assets' / 'images'
    for pn in range(cfg['pages'][0], cfg['pages'][1] + 1):
        page, blocks, boxes, figs = read_page(doc, pn)
        for n, r in enumerate(figs, 1):
            grab = pymupdf.Rect(r.x0 - 10, r.y0 - 5, r.x1 + 10, r.y1 + 28)
            labels = [b for b in blocks if grab.contains((b.bbox.tl + b.bbox.br) / 2)
                      and (len(b.text) < 40 or r.contains(b.bbox))]
            if len(labels) > 8:
                continue  # a shaded table, not an illustration: its text comes from the old edition

            clip = pymupdf.Rect(r)
            for b in labels:
                clip |= b.bbox
            clip = clip + (-6, -6, 6, 6)
            name = f'{chapter}-{pn}-{n}.png'
            page.get_pixmap(dpi=200, clip=clip).save(figdir / name)
            fig = {'k': 'fig', 'src': 'images/' + name, 'page': pn, 'w': round(clip.width * 4 / 3),
                   'alt': re.sub(r'\s+', ' ', ' '.join(b.text.replace('|', ' ') for b in labels)).strip()}

            # Anchor: the last prose block above the figure on that page, matched in the old text.
            above = [b for b in blocks if b.bbox.y1 <= r.y0 + 5 and b not in labels and len(b.text) > 25
                     and b.size <= 12 and not b.font.startswith('Garamond')]
            pos = None
            if above:
                key = norm(max(above, key=lambda b: b.bbox.y1).lines[0].text)
                for idx, e in enumerate(els):
                    if e.get('page') == pn and key and norm(e.get('text', '')).startswith(key[:25]):
                        pos = idx + 1
                    elif e.get('page') == pn and e['k'] in ('ol', 'table') and key[:20] in norm(
                            ' '.join(e.get('items', [])) + ' '.join(c for r_ in e.get('rows', []) for c in r_)):
                        pos = idx + 1
            if pos is None:  # top of the page: put it right after the page mark
                pos = next(idx + 1 for idx, e in enumerate(els) if e['k'] == 'page' and e['page'] == pn)
            els.insert(pos, fig)
            # The old edition repeats the text drawn inside the figure (labels, captions); drop those copies.
            inside = re.sub(r'[^a-z]', '', fig['alt'].lower())
            for idx in range(min(len(els), pos + 8) - 1, max(0, pos - 6) - 1, -1):
                e = els[idx]
                if e is fig or e.get('page') != pn or e['k'] not in ('table', 'p', 'pind', 'h5'):
                    continue
                parts = [c for r_ in e.get('rows', []) for c in r_] if e['k'] == 'table' else [e['text']]
                parts = [re.sub(r'[^a-z]', '', plain(c).lower()) for c in parts]
                parts = [c for c in parts if c]
                if inside and parts and all(c in inside for c in parts):
                    del els[idx]


# ---------------------------------------------------------------------------
# Native Language Guide

def join_tables(els):
    """One table the old file cut in two at a page break (numbering runs on)."""
    out = []
    for e in els:
        prev = next((x for x in reversed(out) if x['k'] != 'page'), None)
        if e['k'] == 'table' and prev and prev['k'] == 'table' and out[-1]['k'] == 'page' \
                and len(e['rows'][0]) == len(prev['rows'][-1]) \
                and any(num_of(r[0]) is not None for r in e['rows']):
            n = [num_of(r[0]) for r in prev['rows'] if num_of(r[0]) is not None]
            m = next(num_of(r[0]) for r in e['rows'] if num_of(r[0]) is not None)
            if n and m == n[-1] + 1:
                prev['rows'] += e['rows']
                continue
        out.append(e)
    return out


def syllable_counts(els, pn, intro):
    """Practice sentences with the syllable count printed above some words: read from the PDF,
    each count becomes a superscript after its word. Replaces the old file's broken grid and list."""
    lines = {}
    for w in pymupdf.open(PDF)[pn - 1].get_text('words'):
        lines.setdefault(round(w[1]), []).append(w)
    sentences, counts = [], []
    for y in sorted(lines):
        ws = sorted(lines[y], key=lambda w: w[0])
        if all(w[4].isdigit() for w in ws):
            counts = ws
        elif re.fullmatch(r'\d+\.', ws[0][4]):
            body = ws[1:]
            out = [w[4] for w in body]
            for c in counts:
                cx = (c[0] + c[2]) / 2
                k = min(range(len(body)), key=lambda j: abs((body[j][0] + body[j][2]) / 2 - cx))
                out[k] = re.sub(r'^(\w+)', rf'\1<sup>{c[4]}</sup>', out[k])
            sentences.append(' '.join(out))
            counts = []
        else:
            counts = []
    at = next(i for i, e in enumerate(els) if plain(e.get('text', '')).startswith(intro))
    j = at + 1
    while j < len(els) and els[j]['k'] in ('table', 'ol', 'page'):
        j += 1
    return els[:at + 1] + [{'k': 'ol', 'items': sentences, 'page': pn}] + els[j:]


def fix_text(x, fixes):
    if isinstance(x, str):
        for a, b in fixes:
            x = re.sub(a, b, x)
        return x
    if isinstance(x, list):
        return [fix_text(v, fixes) for v in x]
    if isinstance(x, dict):
        return {k: v if k in ('t', 'id', 'src') else fix_text(v, fixes) for k, v in x.items()}
    return x


def link_toc(chapter, cfg, blocks):
    """Point the chapter's entries in the front-matter contents (data/front.json) at the new anchors."""
    path = ROOT / 'data' / 'front.json'
    front = json.loads(path.read_text(encoding='utf-8'))
    present = {b.get('id') for b in blocks if b.get('id')}
    links = {t.lower(): f'{chapter}#{i}' for t, i in cfg.get('anchors', {}).items() if i in present}
    if cfg.get('toc_title'):
        links[cfg['toc_title'].lower()] = chapter
    n = 0
    for e in front['toc']:
        if e['title'].lower() in links and not e.get('link'):
            e['link'] = links[e['title'].lower()]
            n += 1
    path.write_text(json.dumps(front, ensure_ascii=False, indent=1), encoding='utf-8')
    missing = [t for t, i in cfg.get('anchors', {}).items() if i not in present]
    print(f'contents: linked {n} entries' + (f'; anchors not found: {missing}' if missing else ''))


def main(chapter):
    cfg = CHAPTERS[chapter]
    els = elements(cfg)
    if cfg.get('arrows'):
        els = apply_arrows(els, cfg)
    for before, cd, track in cfg.get('add_tracks', []):
        # tracks the book lists ("Track 36–37") but the old file has no button for
        at = next(i for i, e in enumerate(els) if plain(e.get('text', '')).startswith(before))
        els.insert(at, {'k': 'trk', 'cd': cd, 'track': track, 'page': els[at]['page']})
    if cfg.get('marks'):
        els = apply_marks(els, cfg)
    if cfg.get('split_tables'):
        els = join_tables(els)
        els = [x for e in els for x in (split_table(e['rows'], e['page']) if e['k'] == 'table' else [e])]
    if cfg.get('syllables'):
        els = syllable_counts(els, *cfg['syllables'])
    els = [e for e in els if e['k'] != 'oldfig']
    add_figures(els, cfg, chapter)
    blocks = Builder(cfg).run(els)
    # A word hyphenated at a line end and joined back with a space: "practic- ing".
    blocks = fix_text(blocks, [(r'([a-z])- ([a-z])', r'\1\2')] + cfg.get('fixes', []))
    seen = set()
    for b in blocks:  # a heading the book repeats on the next page ("continued") keeps no second anchor
        if b.get('id') in seen:
            del b['id']
        elif b.get('id'):
            seen.add(b['id'])
    out = ROOT / 'data' / f'{chapter}.json'
    out.write_text(json.dumps({'blocks': blocks}, ensure_ascii=False, indent=1), encoding='utf-8')
    link_toc(chapter, cfg, blocks)
    secs = sum(1 for b in blocks if b['t'] == 'sec')
    figs = sum(1 for b in blocks if b['t'] == 'img')
    tracks = sorted((b.get('cd'), b['track']) for b in blocks if b.get('track'))
    print(f'wrote {out}: {len(blocks)} blocks, {secs} sections, {figs} figures, {len(tracks)} tracks'
          + (f' ({tracks[0]}..{tracks[-1]})' if tracks else ''))


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'ch4')
