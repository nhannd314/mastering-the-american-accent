"""Intonation arrows: the PDF prints them (MathematicalPi glyphs \x02 falling, \x03 rising) on a row of
their own above the sentence. This puts each arrow straight after the word printed beneath it."""
import sys
import pymupdf

ARROW = {'\x02': '↘', '\x03': '↗'}


def rows_of(page):
    chars = []
    for b in page.get_text('rawdict')['blocks']:
        for l in b.get('lines', []):
            for s in l['spans']:
                for c in s['chars']:
                    chars.append((c['origin'][1], c['bbox'][0], c['bbox'][2], c['c']))
    chars.sort()
    rows, cur = [], []
    for ch in chars:
        if cur and ch[0] - cur[-1][0] > 4:
            rows.append(cur)
            cur = []
        cur.append(ch)
    if cur:
        rows.append(cur)
    return [sorted(r, key=lambda c: c[1]) for r in rows]


def words_of(row):
    """Words as [x0, x1, text], plus a column break flag before words after a wide gap."""
    words, last = [], None
    for y, x0, x1, c in row:
        if c == ' ':
            last = x1 if last is None else last
            continue
        if last is None or x0 - last > 1.5 or c == ' ':
            words.append([x0, x1, c, last is not None and x0 - last > 40])
        else:
            words[-1][1] = x1
            words[-1][2] += c
        last = x1
    # spaces show up as their own chars; re-split on them
    return words


def arrowed_lines(pdf, pages):
    doc = pymupdf.open(pdf)
    out = []
    for pn in pages:
        rows = rows_of(doc[pn - 1])
        for i, r in enumerate(rows):
            arrows = [((x0 + x1) / 2, ARROW[c]) for y, x0, x1, c in r if c in ARROW]
            if not arrows or i + 1 >= len(rows) or rows[i + 1][0][0] - r[0][0] > 30:
                continue
            words = words_of(rows[i + 1])
            if not words or any(c[3] in ARROW for c in rows[i + 1]):
                continue
            marks = {}
            for ax, a in arrows:
                k = min(range(len(words)), key=lambda j: 0 if words[j][0] <= ax <= words[j][1]
                        else min(abs(ax - words[j][0]), abs(ax - words[j][1])))
                marks.setdefault(k, []).append(a)
            segs, seg = [], []
            for j, w in enumerate(words):
                if w[3] and seg:
                    segs.append(' '.join(seg))
                    seg = []
                seg.append(w[2] + ''.join(marks.get(j, [])))
            segs.append(' '.join(seg))
            out.append((pn, segs))
    return out


if __name__ == '__main__':
    for pn, segs in arrowed_lines(sys.argv[1], range(int(sys.argv[2]), int(sys.argv[3]) + 1)):
        print(pn, ' || '.join(segs))
