<?php
// Visitors never see PHP errors (they reveal server paths); they still go to the server's error log.
ini_set('display_errors', '0');
ini_set('log_errors', '1');

require __DIR__ . '/inc/helpers.php';
require __DIR__ . '/inc/blocks.php';

$page = $_GET['page'] ?? 'front';
if (!is_string($page) || !isset(PAGES[$page])) $page = 'front';

$keys = array_keys(PAGES);
$idx = array_search($page, $keys, true);
$prevPage = $keys[$idx - 1] ?? null;
$nextPage = $keys[$idx + 1] ?? null;

$data = load_data($page);
$chap = $page === 'front' ? null : PAGES[$page];
$ch1 = $page === 'ch1' ? $data : load_data('ch1');
$videos = $ch1['videos'] ?? [];
$vlist = $ch1['vlist'] ?? '';

// Sidebar sub-links for the current page.
$subs = [];
if ($page === 'front') {
    foreach (PAGES['front']['subs'] as $a => $label) $subs[] = [$label, '#sec-' . $a];
} else {
    foreach ($data['blocks'] as $b) {
        if (empty($b['id'])) continue;
        $label = $b['t'] === 'sound' ? $b['sym'] . ' as in ' . str_replace('*', '', $b['word']) : $b['title'];
        $subs[] = [$label, '#sec-' . $b['id']];
    }
}

$title = ($chap ? $chap['label'] : 'Front Matter') . ' — Mastering the American Accent';
?>
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title><?= e($title) ?></title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Source+Sans+3:ital,wght@0,400;0,600;0,700;0,800;1,400&family=Source+Serif+4:ital,wght@0,400;0,600;1,400&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/style.css?v=<?= filemtime(__DIR__ . '/assets/style.css') ?>">
<script>try { if (localStorage.getItem('maa-side-collapsed') === '1') document.documentElement.classList.add('side-collapsed'); } catch (e) {}</script>
</head>
<body>

<aside class="side">
  <div class="side-head">
    <div class="side-title">Mastering the American Accent</div>
    <div class="side-author">Lisa Mojsin, M.A.</div>
  </div>
  <nav class="side-nav">
    <?php foreach (PAGES as $id => $p): ?>
      <div>
        <a class="nav-item<?= $id === $page ? ' active' : '' ?>" href="<?= e(page_url($id)) ?>">
          <span><?= e($p['label']) ?></span><span class="nav-num"><?= e($p['num']) ?></span>
        </a>
        <?php if ($id === $page): ?>
          <div class="nav-subs">
            <?php foreach ($subs as [$label, $href]): ?>
              <a class="nav-sub" href="<?= e($href) ?>"><?= e($label) ?></a>
            <?php endforeach; ?>
          </div>
        <?php endif; ?>
      </div>
    <?php endforeach; ?>
    <?php if (UPCOMING): ?>
      <div class="nav-soon">Coming soon</div>
      <?php foreach (UPCOMING as $u): ?>
        <div class="nav-upcoming"><?= e($u) ?></div>
      <?php endforeach; ?>
    <?php endif; ?>
  </nav>
</aside>
<div class="backdrop"></div>

<div class="wrap">
  <header class="topbar">
    <div class="topbar-in">
      <button type="button" class="btn menu-btn" title="Toggle sidebar">☰</button>
      <div class="page-label"><?= e(PAGES[$page]['label']) ?></div>
      <div class="pager">
        <?php if ($prevPage): ?><a class="btn" href="<?= e(page_url($prevPage)) ?>">‹ Previous</a><?php else: ?><span class="btn disabled">‹ Previous</span><?php endif; ?>
        <?php if ($nextPage): ?><a class="btn btn-primary" href="<?= e(page_url($nextPage)) ?>">Next ›</a><?php else: ?><span class="btn btn-primary disabled">Next ›</span><?php endif; ?>
      </div>
    </div>
  </header>

  <main class="main">
  <?php if ($page === 'front'): ?>
    <?php require __DIR__ . '/inc/front.php'; ?>
  <?php else: ?>
    <section class="sheet chapter">
      <div class="running"><?= e($chap['running']) ?></div>
      <div class="chap-head">
        <div class="chap-kicker"><?= e($chap['kicker']) ?></div>
        <h1><?= e($chap['title']) ?></h1>
      </div>
      <?php foreach ($data['blocks'] as $b) render_block($b, $videos, $vlist); ?>
    </section>
  <?php endif; ?>
  </main>
</div>

<div class="player" hidden>
  <div class="player-in">
    <button type="button" class="player-toggle">▶</button>
    <div class="player-info">
      <span class="player-label"></span>
      <span class="player-file"></span>
    </div>
    <div class="player-seek"><div class="player-bar"><div class="player-fill"></div></div></div>
    <span class="player-time">0:00 / 0:00</span>
    <button type="button" class="player-close" title="Close">✕</button>
  </div>
</div>

<script src="assets/app.js?v=<?= filemtime(__DIR__ . '/assets/app.js') ?>"></script>
</body>
</html>
