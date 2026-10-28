# Deploying to the VPS

## Upload these (≈ 267 MB)

| Path | What it is | Size |
|---|---|---|
| `index.php` | The only page script | 5 KB |
| `.htaccess` | Server rules: hides everything else, security headers, caching | 3 KB |
| `inc/` | PHP helpers and block renderer | 32 KB |
| `data/` | Chapter content (JSON) | 0.6 MB |
| `assets/` | `style.css`, `app.js`, `images/` | 1 MB |
| `CD1/`, `CD2/`, `CD3/`, `CD4/` | Audio tracks (MP3) | 265 MB |

## Do not upload

| Path | Why |
|---|---|
| `tools/` | Python scripts that built `data/*.json`; only needed to rebuild |
| `old/` | The old HTML edition the scripts read from |
| `img/` | Pictures of the old edition; no page uses them |
| `Mastering the American Accent.pdf` | Source book; copyrighted |
| `.idea/`, `__pycache__/` | Editor and Python caches |
| `.gitignore`, `DEPLOY.md` | Repository files (harmless, `.htaccess` hides them anyway) |

`.gitignore` keeps `old/`, `img/`, the PDF and editor files out of git. `tools/` stays in
git so the build scripts are versioned, so a `git clone`/`git pull` on the VPS also brings
`tools/` (plus `.gitignore` and this file); `.htaccess` answers any request for them with 404.

Without git, `rsync` can send the same set:

```sh
rsync -av --delete \
  --include='/index.php' --include='/.htaccess' \
  --include='/inc/***' --include='/data/***' --include='/assets/***' \
  --include='/CD[1-4]/***' --exclude='*' \
  ./ user@your-vps:/var/www/american/
```

## Server requirements

- PHP 8.0 or newer (no extensions beyond the defaults, no database).
- Apache 2.4 with `AllowOverride All` (or at least `FileInfo Indexes Options`) for the site
  directory, so `.htaccess` is read. Modules: `alias` and `headers` (both standard);
  `expires` is optional (caching).
- On nginx, `.htaccess` is ignored: block `inc/ data/ tools/ old/ img/` and dot files in the
  server block and add the headers from `.htaccess` there.

## After uploading, check

- `https://your-site/` and a chapter open normally, audio plays, the vowel videos load.
- `https://your-site/data/front.json`, `/inc/helpers.php`, `/tools/` → **404**.
- `https://your-site/CD1/` → **403** (no file listing).
- Response headers include `Content-Security-Policy` and no `X-Powered-By`.

On the VPS itself, also set in the main Apache config (not possible from `.htaccess`):
`ServerTokens Prod` and `ServerSignature Off` (hides the Apache/PHP versions), and
`expose_php = Off` in `php.ini`.

If the inline `<script>` at the top of `index.php` is ever edited, its `sha256-…` hash in the
`.htaccess` Content-Security-Policy must be recomputed, or the browser will block it.
