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
| `/tirith/logo/` | The mark, and where it came from | `src/pages/logo.js` |

`/logo/` is reachable only from the landing page's footer, by design — it is background for a
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

Everything below is optional and nothing is committed. Unset, each feature degrades to a
sensible state rather than failing — which is the correct behaviour for a local
`docusaurus start`, a fork's build and a contributor's checkout.

| Variable | Effect when unset |
| --- | --- |
| `POSTHOG_KEY`, `POSTHOG_HOST` | The client module never loads the script and `src/analytics.js` no-ops. |
| `HUBSPOT_PORTAL_ID`, `HUBSPOT_FORM_GUID` | The At scale enquiry form disables itself and says why. |

A HubSpot portal id and form guid are not secrets — the browser posts to them directly — but
they are supplied from the environment rather than committed so a fork's build does not point
at StackGuardian's CRM.

## Brand

The site carries the Tirith mark in the navbar, the hero letterhead, the colophon, the favicon
and the social card. See [`brand/README.md`](brand/README.md) for what each asset is for, how to
regenerate the social card, and the mark's known small-size limitation.
[`DESIGN-NOTES.md`](DESIGN-NOTES.md) describes the design system the pages are built on and what
must not change.

The idea behind the mark — the city the name comes from, the four moves that reduce it to a
plan, and why opposed gates are the product — is the `/logo/` page. Its geometry comes from
`src/data/logoStory.js`.

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
