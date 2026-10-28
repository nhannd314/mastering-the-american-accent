(function () {
  const root = document.documentElement;
  const narrow = () => window.innerWidth < 900;

  // ---------- Sidebar ----------
  function setCollapsed(v) {
    root.classList.toggle('side-collapsed', v);
    try { localStorage.setItem('maa-side-collapsed', v ? '1' : '0'); } catch (e) {}
  }
  document.querySelector('.menu-btn').addEventListener('click', () => {
    if (narrow()) root.classList.toggle('side-open');
    else setCollapsed(!root.classList.contains('side-collapsed'));
  });
  document.querySelector('.backdrop').addEventListener('click', () => root.classList.remove('side-open'));
  document.querySelectorAll('.nav-sub').forEach(a => a.addEventListener('click', () => root.classList.remove('side-open')));

  // ---------- Audio player ----------
  const AUTO_NEXT = true;
  const audio = new Audio();
  audio.preload = 'none';
  const player = document.querySelector('.player');
  const $ = s => player.querySelector(s);
  const buttons = Array.from(document.querySelectorAll('.trk'));
  const order = [...new Set(buttons.map(b => b.dataset.key))];
  const srcOf = {};
  buttons.forEach(b => { srcOf[b.dataset.key] = b.dataset.src; });
  let cur = null;

  const fmt = s => { s = Math.floor(s || 0); return Math.floor(s / 60) + ':' + String(s % 60).padStart(2, '0'); };
  const isMissing = k => buttons.some(b => b.dataset.key === k && b.classList.contains('miss'));

  function paint() {
    const playing = !audio.paused;
    buttons.forEach(b => {
      const sel = b.dataset.key === cur;
      b.classList.toggle('sel', sel);
      b.classList.toggle('on', sel && playing);
      if (!b.classList.contains('miss')) {
        const [cd, n] = b.dataset.key.split('-');
        b.title = sel && playing ? 'Pause' : 'Play CD ' + cd + ' Track ' + n;
      }
    });
    $('.player-toggle').textContent = playing ? '❚❚' : '▶';
  }

  function markMissing(k) {
    buttons.filter(b => b.dataset.key === k).forEach(b => {
      b.classList.add('miss');
      b.title = 'File not found: ' + decodeURIComponent(srcOf[k]);
    });
    paint();
  }

  // play() also rejects when the browser blocks playback (NotAllowedError) or a new src
  // interrupts it (AbortError); only an unplayable source means the file is missing.
  // Files that fail to load are caught by the audio 'error' listener below.
  const failed = k => err => { if (err && err.name === 'NotSupportedError') markMissing(k); else paint(); };

  function play(k) {
    if (cur === k) {
      if (audio.paused) audio.play().catch(failed(k)); else audio.pause();
      return;
    }
    cur = k;
    audio.src = srcOf[k];
    const [cd, n] = k.split('-');
    $('.player-label').textContent = 'CD ' + cd + ' · Track ' + n;
    $('.player-file').textContent = decodeURIComponent(srcOf[k]);
    $('.player-fill').style.width = '0%';
    $('.player-time').textContent = '0:00 / 0:00';
    player.hidden = false;
    audio.play().catch(failed(k));
    paint();
  }

  function playNext() {
    let i = order.indexOf(cur);
    while (++i < order.length) if (!isMissing(order[i])) return play(order[i]);
  }

  buttons.forEach(b => b.addEventListener('click', () => play(b.dataset.key)));
  audio.addEventListener('timeupdate', () => {
    const d = audio.duration || 0;
    $('.player-fill').style.width = d ? (audio.currentTime / d * 100).toFixed(2) + '%' : '0%';
    $('.player-time').textContent = fmt(audio.currentTime) + ' / ' + fmt(d);
  });
  audio.addEventListener('play', paint);
  audio.addEventListener('pause', paint);
  audio.addEventListener('ended', () => { paint(); if (AUTO_NEXT) playNext(); });
  audio.addEventListener('error', () => { if (cur) markMissing(cur); });

  $('.player-toggle').addEventListener('click', () => cur && play(cur));
  $('.player-close').addEventListener('click', () => { audio.pause(); cur = null; player.hidden = true; paint(); });
  $('.player-seek').addEventListener('click', e => {
    const r = e.currentTarget.getBoundingClientRect();
    if (audio.duration) audio.currentTime = ((e.clientX - r.left) / r.width) * audio.duration;
  });
})();
