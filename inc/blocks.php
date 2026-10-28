<?php
// Renders one chapter content block (the "t" field selects the type).

function video_src(string $id, string $vlist): string
{
    return 'https://www.youtube-nocookie.com/embed/' . $id . '?rel=0' . ($vlist !== '' ? '&list=' . $vlist : '');
}

function render_block(array $b, array $videos, string $vlist): void
{
    $t = $b['t'];
    $isBox = $t === 'box';
    $anchor = !empty($b['id']) ? ' id="sec-' . e($b['id']) . '"' : '';
    echo "<div class=\"blk\"$anchor>";

    if ($t === 'sec') {
        echo '<div class="sec-head"><div class="sec-head-text">';
        echo '<h2>' . e($b['title']) . '</h2>';
        if (!empty($b['quote'])) {
            echo '<div class="quote">' . e($b['quote']) . '<span class="by">' . e($b['by'] ?? '') . '</span></div>';
        }
        echo '</div>' . block_track($b) . '</div>';
    }

    if ($t === 'sound') {
        echo '<div class="sound">';
        echo '<div class="sound-top"><div class="sound-sym">';
        echo '<span class="sym">' . e($b['sym']) . '</span><span class="as-in">AS IN</span><span class="word">' . e(mb_strtoupper($b['word'])) . '</span>';
        echo '</div>';
        if (!empty($b['quote'])) echo '<div class="quote sound-quote">' . e($b['quote']) . '<span class="by">' . e($b['by'] ?? '') . '</span></div>';
        echo '</div>';
        echo '<div class="lips-tongue"><span class="lt-k">Lips:</span><span>' . e($b['lips']) . '</span>';
        echo '<span class="lt-k">Tongue:</span><span>' . e($b['tongue']) . '</span>';
        foreach (['voice' => 'Voice:', 'words' => 'Words:'] as $k => $label) {
            if (!empty($b[$k])) echo '<span class="lt-k">' . $label . '</span><span>' . e($b[$k]) . '</span>';
        }
        echo '</div>';
        $own = (array)($b['video'] ?? []);
        $v = $own ? ['v' => $own[0], 'more' => array_slice($own, 1)] : ($videos[$b['id']] ?? null);
        if ($v) {
            foreach (array_merge([$v['v']], $v['more'] ?? []) as $vid) {
                echo '<div class="video"><iframe src="' . e(video_src($vid, $vlist)) . '" title="Video ' . e($b['sym']) . '" loading="lazy" '
                    . 'allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe></div>';
            }
        }
        echo '</div>';
    }

    $hasHead = (!empty($b['title']) || !empty($b['track']) || !empty($b['sub']) || !empty($b['kicker'])) && !$isBox && $t !== 'sound' && $t !== 'sec';
    if ($hasHead) {
        echo '<div class="blk-head"><div class="blk-head-text">';
        if (!empty($b['kicker'])) echo '<span class="kicker">' . e($b['kicker']) . '</span>';
        if (!empty($b['title'])) echo '<h3>' . e($b['title']) . '</h3>';
        if (!empty($b['sub'])) echo '<span class="sub">' . e($b['sub']) . '</span>';
        echo '</div>' . block_track($b) . '</div>';
    }

    switch ($t) {
        case 'p':
            echo '<div class="paras">';
            foreach ($b['paras'] as $p) echo '<p>' . e($p) . '</p>';
            echo '</div>';
            break;

        case 'quote':
            echo '<div class="quote">' . e($b['text']) . '<span class="by">' . e($b['by'] ?? '') . '</span></div>';
            break;

        case 'img':
            $w = !empty($b['w']) ? ' style="max-width:' . (int)$b['w'] . 'px"' : '';
            echo '<img class="figure" src="' . e(img_url($b['src'])) . '" alt="' . e($b['alt'] ?? '') . '"' . $w . '>';
            break;

        case 'vowels':
            echo '<div class="vowels">';
            foreach ($b['rows'] as $r) {
                echo '<div class="vrow"><span class="num">' . e($r[0]) . '</span><span class="vsym">' . e($r[1]) . '</span>'
                    . '<span>' . e($r[2]) . '</span><span class="vsent">' . e($r[3]) . '</span></div>';
            }
            echo '</div>';
            break;

        case 'spell':
            echo '<div class="spell">';
            foreach ($b['rows'] as $r) {
                echo '<div class="srow"><span class="num">' . e($r[0]) . '</span><span class="pat">' . e($r[1]) . '</span><span>' . e($r[2]) . '</span></div>';
            }
            if (!empty($b['exc'])) {
                echo '<div class="exc"><span class="kicker">exceptions</span>';
                foreach ($b['exc'] as $x) echo '<div class="exc-row"><span class="pat">' . e($x[0]) . '</span><span>' . e($x[1]) . '</span></div>';
                echo '</div>';
            }
            if (!empty($b['note'])) echo '<p class="note">' . e($b['note']) . '</p>';
            echo '</div>';
            break;

        case 'pairs':
            $h = (int)ceil(count($b['items']) / 2);
            echo '<div class="two-col">';
            foreach ([numbered(array_slice($b['items'], 0, $h)), numbered(array_slice($b['items'], $h), $h)] as $col) {
                echo '<div class="nlist">';
                foreach ($col as $r) echo '<div class="nrow"><span class="num">' . e($r['num']) . '</span><span>' . e($r['text']) . '</span></div>';
                echo '</div>';
            }
            echo '</div>';
            break;

        case 'nums':
            // Short numbered items laid out in columns (numbering runs down each column, as in the book).
            $longest = max(array_map(fn($t) => mb_strlen(strip_tags($t)), $b['items']));
            echo '<div class="nums" style="--cols:' . max(1, min(4, (int)($b['cols'] ?? 2)))
                . ';--colw:' . round(2.4 + $longest * 0.55, 1) . 'em">';
            foreach (numbered($b['items']) as $r) echo '<div class="nrow"><span class="num">' . e($r['num']) . '</span><span>' . e($r['text']) . '</span></div>';
            echo '</div>';
            break;

        case 'lines':
            echo '<div class="lines">';
            foreach ($b['lines'] as $ln) echo '<span>' . e($ln) . '</span>';
            echo '</div>';
            break;

        case 'list':
            echo '<div class="nlist nlist-loose">';
            foreach (numbered($b['items']) as $r) echo '<div class="nrow"><span class="num">' . e($r['num']) . '</span><span>' . e($r['text']) . '</span></div>';
            echo '</div>';
            break;

        case 'contrast':
            // Either one list split in two columns, or explicit groups: [{heads, rows}], numbered continuously.
            if (!empty($b['groups'])) {
                $cols = [];
                $n = 0;
                foreach ($b['groups'] as $g) {
                    $rows = [];
                    foreach ($g['rows'] as $r) $rows[++$n - 1] = $r;
                    $cols[] = [$g['heads'], $rows];
                }
            } elseif (max(array_map(fn($r) => mb_strlen(strip_tags($r[0] . $r[1])), $b['rows'])) > 48) {
                $cols = [[$b['heads'], $b['rows']]];  // long sentence pairs need the full width
            } else {
                $h = (int)ceil(count($b['rows']) / 2);
                $cols = [[$b['heads'], array_slice($b['rows'], 0, $h, true)], [$b['heads'], array_slice($b['rows'], $h, null, true)]];
            }
            echo '<div class="two-col">';
            foreach ($cols as [$heads, $rows]) {
                echo '<div class="ctab">';
                if ($heads[0] !== '' || $heads[1] !== '') {
                    echo '<div class="crow chead"><span></span><span>' . e($heads[0]) . '</span><span>' . e($heads[1]) . '</span></div>';
                }
                foreach ($rows as $j => $r) {
                    echo '<div class="crow"><span class="num">' . ($j + 1) . '.</span><span>' . e($r[0]) . '</span><span>' . e($r[1]) . '</span></div>';
                }
                echo '</div>';
            }
            echo '</div>';
            break;

        case 'cons':
            // Consonant chart rows: [[sym, words], ...optional second sound..., description]
            echo '<div class="cons' . (!empty($b['paired']) ? ' paired' : '') . '">';
            if (!empty($b['heads'])) {
                echo '<div class="cons-row cons-head">';
                foreach ($b['heads'] as $h) echo '<span>' . e($h) . '</span>';
                echo '</div>';
            }
            foreach ($b['rows'] as $r) {
                $desc = array_pop($r);
                echo '<div class="cons-row">';
                foreach ($r as [$sym, $words]) {
                    echo '<div class="cons-snd"><span class="cons-sym">' . e($sym) . '</span><span class="cons-words">' . e(implode(', ', $words)) . '</span></div>';
                }
                echo '<div class="cons-desc">' . e($desc) . '</div></div>';
            }
            echo '</div>';
            break;

        case 'box':
            render_box($b);
            break;

        case 'table':
            $minW = count($b['rows'][0]) * 110;
            $numbered = !empty($b['numbered']);
            echo '<div class="tbl-wrap"><div class="tbl" style="min-width:' . $minW . 'px">';
            if (!empty($b['heads'])) {
                echo '<div class="trow thead">' . ($numbered ? '<span class="num"></span>' : '');
                foreach ($b['heads'] as $c) echo '<span class="cell">' . e($c) . '</span>';
                echo '</div>';
            }
            foreach ($b['rows'] as $j => $r) {
                echo '<div class="trow">' . ($numbered ? '<span class="num">' . ($j + 1) . '.</span>' : '');
                foreach ($r as $c) echo '<span class="cell">' . e($c) . '</span>';
                echo '</div>';
            }
            echo '</div></div>';
            break;

        case 'dialog':
            echo '<div class="dialog">';
            $solo = count($b['items']) === 1;  // a single conversation needs no number
            foreach ($b['items'] as $j => $lines) {
                echo '<div class="nrow"><span class="num">' . ($solo ? '' : ($j + 1) . '.') . '</span><div class="dlines">';
                foreach ($lines as $ln) echo '<span>' . e($ln) . '</span>';
                echo '</div></div>';
            }
            echo '</div>';
            break;

        case 'script':
            echo '<div class="script">';
            if (!empty($b['intro'])) echo '<p>' . e($b['intro']) . '</p>';
            foreach ($b['lines'] as [$sp, $text, $ipa]) {
                echo '<div class="sline">' . ($sp !== '' ? '<span class="speaker">' . e($sp) . ':</span>' : '')
                    . '<div class="sline-body"><span class="ipa">' . e($ipa) . '</span><span>' . e($text) . '</span></div></div>';
            }
            echo '</div>';
            break;

        case 'index':
            // The book's index: letter groups of entries (with sub-entries); each page number links to that part of the site.
            $refs = function (array $it): string {
                $out = [];
                foreach ($it['refs'] as $r) {
                    [$pg, $anc] = array_pad(explode('#', (string)($r['link'] ?? ''), 2), 2, null);
                    $out[] = isset(PAGES[$pg])
                        ? '<a href="' . e(page_url($pg, $anc)) . '">' . e($r['p']) . '</a>'
                        : '<span>' . e($r['p']) . '</span>';
                }
                return $out ? '<span class="ix-refs">' . implode(', ', $out) . '</span>' : '';
            };
            echo '<nav class="ix-letters">';
            foreach ($b['groups'] as $g) echo '<a href="#ix-' . e($g['letter']) . '">' . e($g['letter']) . '</a>';
            echo '</nav><div class="ix">';
            foreach ($b['groups'] as $g) {
                echo '<div class="ix-group" id="ix-' . e($g['letter']) . '"><div class="ix-letter">' . e($g['letter']) . '</div>';
                foreach ($g['entries'] as $en) {
                    echo '<div class="ix-entry"><div class="ix-row"><span class="ix-term">' . e($en['term']) . '</span>' . $refs($en) . '</div>';
                    foreach ($en['subs'] as $s) {
                        echo '<div class="ix-row ix-sub"><span class="ix-term">' . e($s['term']) . '</span>' . $refs($s) . '</div>';
                    }
                    echo '</div>';
                }
                echo '</div>';
            }
            echo '</div>';
            break;

        case 'words':
            echo '<div class="words">';
            foreach ($b['groups'] as $g) {
                echo '<div class="wgroup">' . (!empty($g['cap']) ? '<span class="wcap">' . e($g['cap']) . '</span>' : '') . '<div class="wgrid">';
                foreach ($g['words'] as $w) echo '<span>' . e($w) . '</span>';
                echo '</div></div>';
            }
            echo '</div>';
            break;
    }

    echo '</div>';
}

function render_box(array $b): void
{
    $kind = $b['kind'];
    $track = block_track($b);

    // Boxes built from the PDF carry nested blocks instead of fixed fields.
    if (isset($b['children'])) {
        $cls = ['warning' => 'box-warn', 'panel' => 'box-soft box-panel'][$kind] ?? 'box-soft';
        echo '<div class="' . $cls . ' box-nested">';
        if ($kind === 'tip' && !empty($b['img'])) echo '<img class="box-icon" src="' . e(img_url($b['img'])) . '" alt="">';
        echo '<div class="box-body">';
        if (($b['title'] ?? '') !== '' || $track) {
            echo '<div class="box-top"><div class="box-title' . ($kind === 'warning' ? '' : ' soft') . '">' . e($b['title'] ?? '') . '</div>' . $track . '</div>';
        }
        foreach ($b['children'] as $c) render_block($c, [], '');
        echo '</div></div>';
        return;
    }

    if ($kind === 'warning') {
        echo '<div class="box-warn"><div class="box-top"><div class="box-title-wrap"><div class="box-title">' . e($b['title']) . '</div>';
        if (!empty($b['dont'])) echo '<span class="dont">DO NOT SAY</span>';
        echo '</div>' . $track . '</div>';
        echo '<p>' . e($b['text']) . '</p>';
        if (!empty($b['rows'])) {
            echo '<div class="wtab"><span class="wh">' . e($b['heads'][0]) . '</span><span class="wh">' . e($b['heads'][1]) . '</span>';
            foreach ($b['rows'] as $r) echo '<span>' . e($r[0]) . '</span><span>' . e($r[1]) . '</span>';
            echo '</div>';
        }
        if (!empty($b['text2'])) echo '<p>' . e($b['text2']) . '</p>';
        echo '</div>';
    } elseif ($kind === 'advice') {
        echo '<div class="box-soft"><div class="box-top"><div class="box-title soft">' . e($b['title']) . '</div>' . $track . '</div>';
        echo '<p class="advice">' . e($b['text']) . '</p><div class="advice-by">' . e($b['by']) . '</div></div>';
    } elseif ($kind === 'tip') {
        echo '<div class="box-soft box-tip"><img src="' . e(img_url($b['img'])) . '" alt="">';
        echo '<div class="tip-body"><div class="box-top"><div class="box-title soft">' . e($b['title']) . '</div>' . $track . '</div>';
        echo '<p>' . e($b['text']) . '</p></div></div>';
    }
}
