<?php
// Front matter: cover, title page, acknowledgments, contents, introduction.

$tocLink = function (?string $link): ?string {
    if (!$link) return null;
    [$pg, $anc] = array_pad(explode('#', $link, 2), 2, null);
    if ($pg === 'intro') return '#sec-intro';
    return isset(PAGES[$pg]) ? page_url($pg, $anc) : null;
};
?>
<div id="sec-cover" class="cover">
  <img src="assets/images/cover.jpeg" alt="Mastering the American Accent — cover">
</div>

<section id="sec-title" class="sheet title-page">
  <img class="title-img" src="assets/images/title.png" alt="Mastering the American Accent">
  <div class="title-author">
    <div class="name">Lisa Mojsin, M.A.</div>
    <div>Director, Accurate English, Inc.</div>
    <div>Los Angeles, CA</div>
  </div>
  <div class="grow"></div>
  <img class="title-logo" src="assets/images/barrons-logo.png" alt="Barron’s">
</section>

<section id="sec-copy" class="sheet copy-page">
  <h2>Acknowledgments</h2>
  <p>This book is dedicated to my accent reduction students who came to the United States from all parts of the globe. Their drive to excel, passion for learning, amazing work ethic, and belief in the American dream have inspired me to write this book. In the words of Henry David Thoreau, “Go confidently in the direction of your dreams. Live the life you have imagined.”</p>
  <p>Thanks to all of the supportive and extremely professional people at Barron’s: Dimitry Popow, my editor; Wayne Barr for seeking me out to write this book; and Veronica Douglas for her support.</p>
  <p>I am enormously grateful to Lou Savage, “The Voice.” His is the beautiful male voice on the recordings. He was also responsible for all of the expert audio engineering and audio editing. Thank you, Lou, for being such a perfectionist with the sound and insisting on fixing the audio “mistakes” I couldn’t hear anyway.</p>
  <p>I am also grateful for the contributions of Maryam Meghan, Jack Cumming, Katarina Matolek, Mauricio Sanchez, Sabrina Stoll, Sonya Kahn, Jennie Lo, Yvette Basica, Marc Basica, and Laura Tien.</p>
  <div class="imprint">
    <div>© Copyright 2009 by Barron’s Educational Series, Inc.<br>All rights reserved. No part of this publication may be reproduced or distributed in any form or by any means without the written permission of the copyright owner.</div>
    <div>Address all inquiries to:<br>Barron’s Educational Series, Inc.<br>250 Wireless Boulevard<br>Hauppauge, NY 11788<br>www.barronseduc.com</div>
    <div>ISBN-13: 978-0-7641-4185-0 (book only)<br>ISBN-10: 0-7641-4185-6 (book only)<br>ISBN-13: 978-0-7641-9582-2 (book &amp; CD package)<br>ISBN-10: 0-7641-9582-4 (book &amp; CD package)</div>
    <div>Library of Congress Control Number 2008938576<br>Printed in the United States of America<br>9 8 7 6 5 4 3 2 1</div>
  </div>
</section>

<section id="sec-toc" class="sheet toc-page">
  <h2>Contents</h2>
  <div class="toc">
    <?php foreach ($data['toc'] as $t):
        $level = $t['level'] ?? 1;
        $href = $tocLink($t['link'] ?? null);
        $tag = $href ? 'a' : 'div';
        $cls = 'toc-row lvl' . $level . ($href ? '' : ' dead');
    ?>
      <<?= $tag ?> class="<?= $cls ?>"<?= $href ? ' href="' . e($href) . '"' : '' ?>>
        <span><?= e($t['title']) ?></span><span class="dots"></span><span><?= e($t['page']) ?></span>
      </<?= $tag ?>>
    <?php endforeach; ?>
  </div>
</section>

<section id="sec-intro" class="sheet intro-page">
  <div class="running">vi · Mastering the American Accent</div>
  <div class="intro-head">
    <h1>Introduction</h1>
    <?= track_button(1, 1, true) ?>
  </div>
  <p>This book will help non-native speakers of English learn to speak with an American accent.</p>
  <h3>Which American Accent Will This Book Teach Me?</h3>
  <p>You will learn to produce the standard American accent. Some people also call it “broadcaster English.” It’s the kind of standard, neutral speech that you hear on CNN and in educated circles. It’s a non-regional American accent, meaning that people do not associate the dialect with any particular part of the United States. It is the accent most commonly associated with educated people in the American East, Midwest, and West.</p>
  <h3>How Should I Practice?</h3>
  <p>Listen to the recorded material over and over. You will hear words and sentences pronounced followed by a pause for you to repeat after the speaker. You may want to record yourself repeating so that you can compare your accent to the accents of the speakers on this audio. Then practice the new sounds in real-life situations.</p>
  <p>There are numerous study tips throughout the book, both from the writer and from her many successful students who have greatly improved their American accent. For an individual professional analysis of your accent which will help you to study accent reduction more efficiently and tell you which sections of this book you should focus on most, please contact us at 1-800-871-1317 or visit our website at: masteringtheamericanaccent.com.</p>
</section>
