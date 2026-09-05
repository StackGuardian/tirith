# The Tirith site

The documentation site and the marketing pages, built with
[Docusaurus](https://docusaurus.io/) and published to
<https://stackguardian.github.io/tirith/> by
[`.github/workflows/deploy_docs.yml`](../.github/workflows/deploy_docs.yml) on every push to
`main`.

## Pages

| Route | Page | Source |
| --- | --- | --- |
| `/tirith/` | Landing | `src/pages/index.js` |
| `/tirith/learn/` | Six lessons and a browser playground | `src/pages/learn.js` |
| `/tirith/skills/` | Tirith with a coding agent | `src/pages/skills.js` |
| `/tirith/docs/…` | The documentation | `docs/`, ordered by `sidebars.js` |
| `/tirith/at-scale/` | Many repositories, one policy set — the commercial page | `src/pages/at-scale.js` |
| `/tirith/origins/` | Where the name and the mark come from | `src/pages/origins.js` |

One static asset is part of the site's contract rather than decoration:
`static/skill.sh`, served at `https://stackguardian.github.io/tirith/skill.sh`. It is the
one-line installer the Skills page, the editor documentation and `llms.txt` all point at, so
it is a published URL and moving or renaming it breaks three pages and every agent that has
read the brief. It downloads the files in `.claude/skills/tirith-policies/` and nothing else.

`/origins/` is reachable only from the landing page's footer, by design — it is background for a
reader who has finished the page, not a step towards installing anything, so it is deliberately
absent from the navbar.

## Requirements

- Node.js 18, matching the documentation CI workflows
- npm — `package-lock.json` is the committed lockfile and both docs workflows say so
  explicitly. `yarn install` would ignore it and resolve fresh, so the deployed site would not
  be built from the pinned dependency tree.

No environment variables, Tirith installation, StackGuardian account, or API key are needed to
build or preview these pages.

## Run locally

```bash
cd documentation
npm ci
npm start
```

Open <http://localhost:3000/tirith/>. Docusaurus reloads the development server when a source
file changes.

## Test the production build

```bash
cd documentation
npm run build
npm run serve
```

The build is written to `documentation/build/`, which is what the deploy workflow publishes.

## Environment

Two variables, both optional, neither committed. Unset, the analytics client never loads the
script and `src/analytics.js` no-ops: the right behaviour for a local `docusaurus start`, a
fork's build and a contributor's checkout. Only the deploy workflow supplies them, so the
published site is the one place anything is reported.

| Variable | Where it comes from | Unset |
| --- | --- | --- |
| `POSTHOG_KEY` | PostHog project API key, `phc_…` | No tracking script is loaded at all |
| `POSTHOG_HOST` | `https://eu.i.posthog.com` or `https://us.i.posthog.com` | Defaults to the EU host |

### Getting the values

In PostHog: **Settings → Project → Project API key**. It starts `phc_`. That is the *project*
key, not a personal API key (`phx_…`), which will not work here.

The host is your region, and it is the domain you log in to: `eu.posthog.com` means
`https://eu.i.posthog.com`, `us.posthog.com` means `https://us.i.posthog.com`. On EU you can
leave `POSTHOG_HOST` unset, because that is the default.

### Adding them

In the GitHub repository: **Settings → Secrets and variables → Actions**.

- `POSTHOG_KEY` goes on the **Secrets** tab (`New repository secret`).
- `POSTHOG_HOST` goes on the **Variables** tab (`New repository variable`).

The two tabs are not interchangeable: `deploy_docs.yml` reads them as
`${{ secrets.POSTHOG_KEY }}` and `${{ vars.POSTHOG_HOST }}`, so a host added as a secret is
read as empty and silently falls back to the EU default.

### The key is not a secret, and that matters

A PostHog project API key is designed to be public. It is initialised in the browser, so it
ships in the built JavaScript and anyone can read it from the deployed page. Keeping it in
GitHub secrets stops it being committed to the repository, which is worth doing, but it does
not keep it private.

What actually stops someone else sending events with it is PostHog's own
**Settings → Project → Authorized URLs**. Add the site's origin there.

### Trying it locally

```bash
POSTHOG_KEY=phc_your_key npm run build && npm run serve
```

Then look for a request to `/static/array.js` on your PostHog host. Without the variable there
is no such request, which is the check that the unset path still works.

### What it collects, and what it stores

`src/clientModules/posthog.js` is deliberately restrained, and the settings are the point:

| Setting | Effect |
| --- | --- |
| `autocapture: false` | Only the events named in `src/analytics.js` are sent. No keystrokes, no clicks on unnamed elements. |
| `disable_session_recording: true` | No replay. The forms and code blocks on these pages are exactly what a recording would capture. |
| `disable_surveys: true` | Nothing can open a dialog over the page. |
| `persistence: 'memory'` | **Cookieless.** Nothing is written to the visitor's device, so there is no cookie to consent to and no banner needed. |
| `person_profiles: 'identified_only'` | No person profile is created for an anonymous visitor. |

Memory persistence has a cost worth knowing: the id lives for the lifetime of the JavaScript
context, so client-side navigation within a visit is one id and a full reload starts a new one.
Returning visitors cannot be recognised and retention is not measurable. Counts and funnels
within a visit still work, which is what a documentation site actually needs.

Do not change `persistence` back to `localStorage+cookie` without adding a consent banner and a
privacy notice first.

## Brand

The site carries the Tirith mark in the navbar, the hero letterhead, the colophon, the favicon
and the social card. See [`brand/README.md`](brand/README.md) for what each asset is for, how to
regenerate the social card, and the mark's known small-size limitation.
[`DESIGN-NOTES.md`](DESIGN-NOTES.md) describes the design system the pages are built on and what
must not change.

The idea behind the mark — the city the name comes from, the four moves that reduce it to a
plan, and why opposed gates are the product — is the `/origins/` page. Its geometry comes from
`src/data/logoStory.js`.

### The documentation, and the design

`src/css/custom.css` declares the palette once and maps Infima's variables onto it;
`src/css/docs.css` handles the structure a variable cannot express. Together they put the
documentation in the same design as the landing pages, so the two halves of the site do not
read as two products. Three small swizzles support it: `DocBreadcrumbs` hosts the copy-page
control, `PaginatorNavLink` draws previous/next, and `Admonition` supplies the icons.

Every documentation page carries a **copy-page menu** beside its breadcrumbs: copy the
markdown, view it, or open the page in ChatGPT or Claude. It serves the `.md` twin that
`scripts/generate-llms-full.py` already writes for every route, so adding a page means
re-running that script or the menu has nothing to hand over.

The mark is Tirith's own, not StackGuardian's. This is an Apache-2.0 project that works with no
account and no vendor relationship, and flying the sponsor's logo as the page logo argues the
opposite before a word is read. StackGuardian is credited in the footer, and its blue survives
as the single accent colour.

## Playground scope and limitations

The browser playground on `/learn/` is a teaching aid, not the full Python Tirith package. It
runs locally in JavaScript and makes no request to a Tirith service.

It currently models:

- the `stackguardian/json` provider and its `get_value` operation;
- Tirith's 13 documented condition types;
- `&&`, `||`, `!`, and parentheses in `eval_expression`;
- passed, failed, and skipped results;
- Tirith-style output and `--fail-on-error` exit codes.

It does not execute the Terraform plan, Kubernetes, Infracost, or StackGuardian Workflow
providers. Other known differences are:

- regular expressions use JavaScript semantics rather than Python's `re` module;
- nested collection equality does not perform all of Tirith's normalization and sorting
  behaviour;
- some provider error severities are approximated, including the missing-key example used by
  the lessons.

The interactive specimen on the landing page is also synthetic. It evaluates curated sample
values for each provider-shaped example; it does not parse an uploaded plan, manifest, cost
breakdown, or arbitrary JSON document.

Use the installed Tirith package as the authoritative evaluator for real policies and input
documents.
