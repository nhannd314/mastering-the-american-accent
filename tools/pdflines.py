"""PDF text lines with the book's linking marks kept:
- linking arcs (a "(" glyph printed under the gap between two words) become a tie: "come‿in"
- the tiny inserted /y/ /w/ letters ("I ʸate out") become <sup>y</sup>
- silent letters printed over a gap ("Is e nice?" with an "h" above) become <s>h</s>: "Is <s>h</s>e nice?"
Bold/italic spans keep <strong>/<em>."""
import re
import pymupdf

TIE = '‿'


def _wrap(ch, bold, ital):
    return ('<strong>' if bold else '') + ('<em>' if ital else '') + ch + ('</em>' if ital else '') + ('</strong>' if bold else '')


def _words(l):
    """[{x0, x1, html, glue}] where glue means no space before the word."""
    words, cur, last = [], None, None
    for s in l['spans']:
        small = s['size'] < 8
        bold, ital = 'Bold' in s['font'], 'Italic' in s['font']
        for c in s['chars']:
            ch = c['c']
            if ch.isspace():
                cur, last = None, c['bbox'][2]
                continue
            piece = f'<sup>{ch}</sup>' if small and ch.isalpha() else _wrap(ch, bold, ital)
            if cur is None or (last is not None and c['bbox'][0] - last > 1.2 and not cur['small'] and not small):
                cur = {'x0': c['bbox'][0], 'x1': c['bbox'][2], 'html': piece, 'small': small,
                       'glue': bool(words) and words[-1]['small']}
                words.append(cur)
            else:
                cur['x1'] = c['bbox'][2]
                cur['html'] += piece
                cur['small'] = small
            last = c['bbox'][2]
    return words


def _text(l):
    return ''.join(c['c'] for s in l['spans'] for c in s['chars']).strip()


def marked_lines(doc, pn, y0=0, y1=10_000):
    page = doc[pn - 1]
    raw = [{'bbox': l['bbox'], 'spans': [s for s in l['spans'] if s['chars']]}
           for b in page.get_text('rawdict')['blocks'] for l in b.get('lines', [])]
    raw = [l for l in raw if l['spans'] and _text(l)]
    arcs = [((c['bbox'][0] + c['bbox'][2]) / 2, c['bbox'][1])
            for l in raw if set(_text(l)) <= {'(', ' '} for s in l['spans'] for c in s['chars'] if c['c'] == '(']
    overlays = [l for l in raw if re.fullmatch(r'[a-z]', _text(l))]
    lines = []
    for l in raw:
        if set(_text(l)) <= {'(', ' '} or l in overlays:
            continue
        lines.append({'y': l['bbox'][1], 'x': l['bbox'][0], 'x1': l['bbox'][2], 'words': _words(l), 'ties': set()})
    lines.sort(key=lambda d: (round(d['y']), d['x']))
    # Join pieces of one printed line that came out as separate lines.
    merged = []
    for d in lines:
        m = merged[-1] if merged else None
        if m and abs(d['y'] - m['y']) < 3 and 0 <= d['x'] - m['x1'] < 12:
            if d['words'] and (m['words'][-1]['small'] or d['x'] - m['x1'] < 2):
                d['words'][0]['glue'] = True
            m['words'] += d['words']
            m['x1'] = d['x1']
        else:
            merged.append(d)
    lines = merged
    # Silent letters printed above the text: glue them into the word they belong to.
    for o in overlays:
        ox = (o['bbox'][0] + o['bbox'][2]) / 2
        host = next((d for d in lines if abs(d['y'] - o['bbox'][1]) < 4 and d['x'] <= ox <= d['x1'] + 4), None)
        if not host:
            continue
        ws = host['words']
        j = next((k for k, w in enumerate(ws) if w['x0'] > ox - 1), len(ws))
        h = {'x0': o['bbox'][0], 'x1': o['bbox'][2], 'html': f'<s>{_text(o)}</s>', 'small': False,
             'glue': j > 0 and o['bbox'][0] - ws[j - 1]['x1'] < 2.5}
        if j < len(ws):
            ws[j]['glue'] = True
        ws.insert(j, h)
    for ax, ay in arcs:
        for d in lines:
            ws = d['words']
            if 5 <= ay - d['y'] <= 15 and len(ws) > 1 and ws[0]['x0'] - 5 <= ax <= ws[-1]['x1'] + 5:
                k = min(range(len(ws) - 1), key=lambda j: abs(ax - (ws[j]['x1'] + ws[j + 1]['x0']) / 2))
                if abs(ax - (ws[k]['x1'] + ws[k + 1]['x0']) / 2) < 14 and not ws[k + 1]['glue']:
                    d['ties'].add(k)
    out = []
    for d in lines:
        if not (y0 <= d['y'] < y1):
            continue
        html = ''
        for j, w in enumerate(d['words']):
            if j:
                html += TIE if j - 1 in d['ties'] else ('' if w['glue'] else ' ')
            html += w['html']
        for _ in range(2):
            html = re.sub(r'</(strong|em)>(\s?)<\1>', r'\2', html)
        if re.fullmatch(r'\s*(CD ?\d*|Track ?[\d–]*|[\d–]+)\s*', re.sub(r'<[^>]+>', '', html)):
            continue  # CD/track badges in the margin, page numbers
        out.append({'y': d['y'], 'x': d['x'], 'html': html})
    return out


if __name__ == '__main__':
    import sys
    doc = pymupdf.open(sys.argv[1])
    for d in marked_lines(doc, int(sys.argv[2])):
        print(round(d['y']), round(d['x']), d['html'])
