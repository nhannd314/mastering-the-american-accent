<?php
// Shared helpers: escaping, data loading, audio paths and the CD-track button.

const AUDIO_PATTERN = 'CD{cd}/{nn} Stopa {track}.mp3';

const PAGES = [
    'front' => ['label' => 'Front Matter', 'num' => '', 'subs' => [
        'cover' => 'Cover', 'title' => 'Title Page', 'copy' => 'Acknowledgments', 'toc' => 'Contents', 'intro' => 'Introduction',
    ]],
    'ch1' => ['label' => 'Chapter 1: The Vowel Sounds', 'num' => '1',
        'kicker' => 'Chapter One', 'title' => 'THE VOWEL SOUNDS', 'running' => 'Chapter One: THE VOWEL SOUNDS · 1–17'],
    'ch2' => ['label' => 'Chapter 2: Vowels in Detail', 'num' => '18',
        'kicker' => 'Chapter Two', 'title' => 'VOWELS IN DETAIL', 'running' => 'Chapter Two: VOWELS IN DETAIL · 18–28'],
    'ch3' => ['label' => 'Chapter 3: Consonants', 'num' => '29',
        'kicker' => 'Chapter Three', 'title' => 'CONSONANTS', 'running' => 'Chapter Three: CONSONANTS · 29–33'],
    'ch4' => ['label' => 'Chapter 4: Problematic Consonants', 'num' => '34',
        'kicker' => 'Chapter Four', 'title' => 'PROBLEMATIC CONSONANTS', 'running' => 'Chapter Four: PROBLEMATIC CONSONANTS · 34–65'],
    'ch5' => ['label' => 'Chapter 5: Syllable Stress', 'num' => '66',
        'kicker' => 'Chapter Five', 'title' => 'SYLLABLE STRESS', 'running' => 'Chapter Five: SYLLABLE STRESS · 66–77'],
    'ch6' => ['label' => 'Chapter 6: Word Stress', 'num' => '78',
        'kicker' => 'Chapter Six', 'title' => 'WORD STRESS', 'running' => 'Chapter Six: WORD STRESS · 78–94'],
    'ch7' => ['label' => 'Chapter 7: Intonation', 'num' => '95',
        'kicker' => 'Chapter Seven', 'title' => 'INTONATION', 'running' => 'Chapter Seven: INTONATION · 95–100'],
    'ch8' => ['label' => 'Chapter 8: Sound Like a True Native Speaker', 'num' => '101',
        'kicker' => 'Chapter Eight', 'title' => 'SOUND LIKE A TRUE NATIVE SPEAKER',
        'running' => 'Chapter Eight: SOUND LIKE A TRUE NATIVE SPEAKER · 101–118'],
    'ch9' => ['label' => 'Chapter 9: Memorizing the Exceptions', 'num' => '119',
        'kicker' => 'Chapter Nine', 'title' => 'MEMORIZING THE EXCEPTIONS',
        'running' => 'Chapter Nine: MEMORIZING THE EXCEPTIONS · 119–126'],
    'guide' => ['label' => 'Native Language Guide', 'num' => '127',
        'kicker' => 'Appendix', 'title' => 'NATIVE LANGUAGE GUIDE', 'running' => 'NATIVE LANGUAGE GUIDE · 127–183'],
    'index' => ['label' => 'Index', 'num' => '184',
        'kicker' => 'Back Matter', 'title' => 'INDEX', 'running' => 'INDEX · 184–186'],
];

const UPCOMING = [];

// Escapes text but keeps <strong>/<em>, which the book data uses to highlight letters,
// <sup>/<s> (inserted /y/ /w/ glides and silent letters, Chapter 8), and styles the
// intonation arrows (↗ rising, ↘ falling) used in Chapter 7.
function e($s): string
{
    $h = htmlspecialchars((string)$s, ENT_QUOTES, 'UTF-8');
    $h = preg_replace('#&lt;(/?)(strong|em|sup|s)&gt;#', '<$1$2>', $h);
    // Keep each arrow on the same line as the word it follows.
    $h = str_replace('‿', '<span class="tie">‿</span>', $h);
    return preg_replace('/([^\s<>]*)([↗↘])/u', '<span class="nw">$1<span class="into">$2</span></span>', $h);
}

function load_data(string $page): array
{
    $file = __DIR__ . '/../data/' . $page . '.json';
    return is_file($file) ? json_decode(file_get_contents($file), true) : [];
}

function page_url(string $page, ?string $anchor = null): string
{
    return '?page=' . rawurlencode($page) . ($anchor ? '#sec-' . rawurlencode($anchor) : '');
}

// Data files reference images as "images/x.png"; they live in assets/images.
function img_url(string $src): string
{
    return 'assets/' . $src;
}

function audio_rel(int $cd, int $n): string
{
    return strtr(AUDIO_PATTERN, ['{cd}' => $cd, '{nn}' => str_pad((string)$n, 2, '0', STR_PAD_LEFT), '{track}' => $n]);
}

function audio_url(int $cd, int $n): string
{
    return implode('/', array_map('rawurlencode', explode('/', audio_rel($cd, $n))));
}

function track_button(int $cd, int $n, bool $big = false): string
{
    $rel = audio_rel($cd, $n);
    $missing = !is_file(__DIR__ . '/../' . $rel);
    $title = $missing ? 'File not found: ' . $rel : "Play CD $cd Track $n";
    return sprintf(
        '<button type="button" class="trk%s%s" data-key="%d-%d" data-src="%s" title="%s">'
        . '<span class="trk-cd">CD %d</span><span class="trk-lbl">Track</span><span class="trk-n">%d</span></button>',
        $big ? ' trk-big' : '', $missing ? ' miss' : '', $cd, $n, e(audio_url($cd, $n)), e($title), $cd, $n
    );
}

function block_track(array $b): string
{
    return empty($b['track']) ? '' : track_button((int)($b['cd'] ?? 1), (int)$b['track']);
}

// Numbered rows: [['num' => '1.', 'text' => ...], ...]
function numbered(array $items, int $offset = 0): array
{
    $out = [];
    foreach (array_values($items) as $i => $t) {
        $out[] = ['num' => ($i + 1 + $offset) . '.', 'text' => $t];
    }
    return $out;
}
