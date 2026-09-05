import React, {useCallback, useEffect, useRef, useState} from 'react';
import {useLocation} from '@docusaurus/router';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import {BRAND} from './brandMarks';
import styles from './CopyPageMenu.module.css';

/**
 * Hand this page to an agent.
 *
 * Every documentation route already has a markdown twin beside it: /docs/x/y/ has
 * /docs/x/y.md, written by documentation/scripts/generate-llms-full.py. That file existed
 * for crawlers and for llms.txt, and nothing on the page pointed a human at it. This is that
 * pointer, and it is the reason this control can be four items rather than a copy button:
 * the source it copies, opens and hands to a model is one already-generated file, not the
 * rendered DOM scraped back into markdown.
 *
 * Deriving the URL rather than threading it through: the generator's convention is the route
 * plus `.md`, stated in its own comment, and re-deriving it here keeps this component from
 * needing a manifest that could drift out of date. If the generator has not been re-run
 * after a page was added, the fetch 404s and the button says so instead of copying an HTML
 * error page, which is the failure worth handling.
 */

const PROMPT = (url) =>
  `Read ${url} so I can ask you questions about it. Reply with a one-line summary when you have.`;

/*
 * Two kinds of mark, drawn differently on purpose.
 *
 * The interface glyphs below are stroked at 1.6, which is what keeps them in the same weight
 * as the hairlines everything else on this site is built from. The vendor marks in
 * brandMarks.js are solid single paths: stroking one would thicken it into a blot and would
 * also be a modification of someone's trademark. So `solid` swaps stroke for fill and leaves
 * the path exactly as published.
 */
function Icon({d, className, solid}) {
  return (
    <svg
      className={className}
      width="15"
      height="15"
      viewBox="0 0 24 24"
      fill={solid ? 'currentColor' : 'none'}
      stroke={solid ? 'none' : 'currentColor'}
      strokeWidth={solid ? undefined : '1.6'}
      strokeLinecap={solid ? undefined : 'square'}
      strokeLinejoin={solid ? undefined : 'miter'}
      aria-hidden="true">
      {solid ? <path d={d} /> : d}
    </svg>
  );
}

const ICON = {
  copy: (
    <>
      <rect x="9" y="9" width="11" height="11" />
      <path d="M5 15H4V4h11v1" />
    </>
  ),
  file: (
    <>
      <path d="M14 3H5v18h14V8z" />
      <path d="M14 3v5h5" />
    </>
  ),
  caret: <path d="M6 9l6 6 6-6" />,
};

export default function CopyPageMenu() {
  const {pathname} = useLocation();
  const {siteConfig} = useDocusaurusContext();
  const [open, setOpen] = useState(false);
  const [state, setState] = useState('idle');
  const root = useRef(null);
  const timer = useRef(null);

  useEffect(() => () => clearTimeout(timer.current), []);

  const mdPath = `${pathname.replace(/\/$/, '')}.md`;
  const mdUrl = `${siteConfig.url}${mdPath}`;

  /*
   * Close on an outside click or Escape, and return focus to the trigger on Escape only.
   * A pointer dismissal has already moved the user's attention somewhere deliberate; yanking
   * focus back would fight them. A keyboard dismissal has nowhere to land otherwise.
   */
  useEffect(() => {
    if (!open) return undefined;
    const onDown = (e) => {
      if (root.current && !root.current.contains(e.target)) setOpen(false);
    };
    const onKey = (e) => {
      if (e.key !== 'Escape') return;
      setOpen(false);
      root.current?.querySelector('[data-caret]')?.focus();
    };
    document.addEventListener('mousedown', onDown);
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('mousedown', onDown);
      document.removeEventListener('keydown', onKey);
    };
  }, [open]);

  /*
   * The async Clipboard API, then execCommand, then give up and say so.
   *
   * The fallback is not hypothetical: the API is denied outright in some embedded and
   * automated browsers even on a secure origin, and this is a page whose whole promise is
   * handing text to something else. `src/components/landing/CopyField.js` solves the same
   * problem by selecting the visible text, which cannot work here because the markdown is
   * never on the page. A detached textarea is the equivalent.
   */
  const copy = useCallback(async () => {
    setOpen(false);
    try {
      const res = await fetch(mdPath);
      const text = await res.text();
      // A missing .md is served as the site's 404 page, which is a 200 full of HTML on
      // GitHub Pages. Checking the first character catches that; checking res.ok alone
      // would not.
      if (!res.ok || text.trimStart().startsWith('<')) throw new Error('not markdown');
      try {
        await navigator.clipboard.writeText(text);
      } catch {
        const ta = document.createElement('textarea');
        ta.value = text;
        ta.setAttribute('readonly', '');
        ta.style.cssText = 'position:fixed;top:-1000px;opacity:0';
        document.body.appendChild(ta);
        ta.select();
        const ok = document.execCommand('copy');
        document.body.removeChild(ta);
        if (!ok) throw new Error('copy refused');
      }
      setState('done');
    } catch {
      setState('failed');
    }
    clearTimeout(timer.current);
    timer.current = setTimeout(() => setState('idle'), 2400);
  }, [mdPath]);

  const label = {idle: 'Copy', done: 'Copied', failed: 'Unavailable'}[state];

  const items = [
    {
      icon: ICON.copy,
      title: 'Copy page',
      note: 'Copy as Markdown format',
      onClick: copy,
    },
    {
      icon: ICON.file,
      title: 'View as Markdown',
      note: 'View as plain text',
      href: mdPath,
    },
    {
      icon: BRAND.openai,
      solid: true,
      title: 'Open in ChatGPT',
      note: 'Discuss this page in ChatGPT',
      href: `https://chatgpt.com/?hints=search&q=${encodeURIComponent(PROMPT(mdUrl))}`,
      external: true,
    },
    {
      icon: BRAND.claude,
      solid: true,
      title: 'Open in Claude',
      note: 'Discuss this page in Claude',
      href: `https://claude.ai/new?q=${encodeURIComponent(PROMPT(mdUrl))}`,
      external: true,
    },
  ];

  return (
    <div className={styles.root} ref={root}>
      <div className={styles.split}>
        <button type="button" className={styles.main} onClick={copy}>
          <Icon className={styles.glyph} d={ICON.copy} />
          {label}
        </button>
        <button
          type="button"
          data-caret
          className={styles.caret}
          aria-haspopup="menu"
          aria-expanded={open}
          aria-label="More ways to use this page"
          onClick={() => setOpen((v) => !v)}>
          <Icon className={open ? styles.caretGlyphOpen : styles.caretGlyph} d={ICON.caret} />
        </button>
      </div>

      {open && (
        <div className={styles.menu} role="menu">
          {items.map((it) =>
            it.href ? (
              <a
                key={it.title}
                className={styles.item}
                role="menuitem"
                href={it.href}
                target="_blank"
                rel={it.external ? 'noopener noreferrer' : 'noopener'}
                onClick={() => setOpen(false)}>
                <Icon className={styles.glyph} d={it.icon} solid={it.solid} />
                <span>
                  <span className={styles.itemTitle}>{it.title}</span>
                  <span className={styles.itemNote}>{it.note}</span>
                </span>
              </a>
            ) : (
              <button
                key={it.title}
                type="button"
                className={styles.item}
                role="menuitem"
                onClick={it.onClick}>
                <Icon className={styles.glyph} d={it.icon} solid={it.solid} />
                <span>
                  <span className={styles.itemTitle}>{it.title}</span>
                  <span className={styles.itemNote}>{it.note}</span>
                </span>
              </button>
            ),
          )}
        </div>
      )}
    </div>
  );
}
