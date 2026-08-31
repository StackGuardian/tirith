# Brand assets

The mark is candidate **B, "Keep"** from the logo canvas in
[`docs/Tirith Logo.html`](../../docs/Tirith%20Logo.html) at the repository root. That
canvas holds three candidates — Primary, Keep and Ward — and is the source of truth for
the path data. Nothing here should be hand-edited; regenerate from the canvas instead.

## What is where

| File | Used by |
| --- | --- |
| `../static/img/tirith-lockup.svg` | Navbar logo, light theme (`#111318` ink) |
| `../static/img/tirith-lockup-dark.svg` | Navbar logo, dark theme (`#FAFAF9` ink) |
| `../static/img/tirith-mark.svg` | Favicon. Carries its own `prefers-color-scheme` swap |
| `../static/img/tirith-social-card.png` | `og:image` / `twitter:image`, 1200×630 |
| `../src/components/brand/TirithMark.js` | Hero letterhead and colophon, inline, `currentColor` |

Two lockup files rather than one theme-reactive SVG because the navbar swap is driven by
the site's theme toggle, which a media query inside the file cannot observe. The inline
component exists for the opposite reason: in the page it can inherit `--tp-ink` and needs
no second asset.

## Regenerating the social card

`social-card.html` is the source. It is deliberately **not** under `static/`, which is
copied verbatim into the build and would publish it as a stray page.

```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless --disable-gpu --hide-scrollbars --force-device-scale-factor=1 \
  --virtual-time-budget=8000 --window-size=1200,630 \
  --screenshot=static/img/tirith-social-card.png \
  "file://$PWD/brand/social-card.html"
```

The page pulls Martian Mono and JetBrains Mono from Google Fonts, so the render needs
network access; `--virtual-time-budget` is what gives the faces time to arrive.

## Known limitation, from the canvas

Keep is two separate shapes, and the canvas's own note is that at very small sizes it
"can read as two marks instead of one". Nothing in the page renders it below 16px for
that reason. The favicon is the one place it goes smaller, and that cut is worth
redrawing as a dedicated small version before this is treated as final.
