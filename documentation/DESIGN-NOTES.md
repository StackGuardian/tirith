# Tirith site — design notes

The design system the site is built on, and the rules that must survive an edit. It was
written for a design review of the pages while they were a prototype; the pages have since
become the site itself and live in `documentation/` in the Tirith repository.

The static export it refers to below was the review bundle — one self-contained HTML file per
page, JavaScript stripped so the files could be edited by hand. That bundle is not in the
repository. Sections 2 onwards describe the live pages and still hold.

---

## 1. What you have, and what it cannot do

| File | Page | Route in the real site |
| --- | --- | --- |
| `index.html` | Landing | `/tirith/` |
| `learn.html` | Learn — six lessons and a playground | `/tirith/learn/` |
| `ai.html` | Tirith with a coding agent | `/tirith/ai/` |
| `fleet.html` | Fleet governance (the commercial page) | `/tirith/fleet/` |
| `logo.html` | Origins — where the name and the mark come from | `/tirith/origins/` |
| `docs-example.html` | One representative documentation page | `/tirith/docs/...` |

Each file is self-contained: CSS inlined, images embedded, no build step, no server.
Double-click it.

**All JavaScript has been stripped**, which is what makes the files editable. The cost is
that anything script-driven renders in its opening state and does not respond:

- **Landing** — the specimen's threshold slider, and the five-step demo walkthrough (you
  see step 01 only).
- **Learn** — the six lesson benches and the playground. The panes show their starting
  policy and document; nothing evaluates.
- **AI / Fleet** — copy buttons, and the Fleet form's submit.
- Still working, because they need no script: the Fleet FAQ accordions (native
  `<details>`), every link, and both colour themes.

**To see dark mode**, add `data-theme="dark"` to the `<html>` tag at the top of any file.
The whole palette is token-driven, so nothing else needs changing.

**Reworking these with Claude.** One file per conversation works best — they are ~160KB
each, mostly the inlined stylesheet. Worth telling it: the page is one flat HTML file, the
design system is described below, and section 5 lists the things that must not change.

---

## 2. The design system

The visual world is a **policy specimen sheet**. The subject is a tool that reads a
document and returns a verdict, so the page is built like the artefact it describes: paper
ground, ink type, hairline rules, and measurements shown rather than decorated.

**The rules that produce the look**

- **Hairline rules instead of cards.** Almost nothing on these pages is a box with a
  shadow. Structure comes from 1px rules and shared column edges. There are no shadows and
  no gradients anywhere.
- **Square corners.** No border radius, on anything.
- **Hierarchy from scale contrast**, not from colour or weight alone. The headline is very
  large; nearly everything else is small.
- **Two hues, total.** An accent (`--tp-accent`, blue) for links and primary buttons, and
  an alarm (`--tp-alarm`, red) for a negative verdict. Everything else is ink, paper and
  rule. A pass is deliberately *not* green: colour never carries a verdict on its own, the
  word does, so the pages stay readable for a colour-blind reader.
- **One width: 96rem.** The navbar's inner row, every page's `<main>`, and the docs layout
  are all measured against it, so the logo, the section rules and the docs sidebar start on
  the same vertical line on every page.

**Type**

| Role | Face | Used for |
| --- | --- | --- |
| Display | Martian Mono | Headlines, section titles, buttons, labels |
| Text | IBM Plex Sans | Body prose |
| Mono | JetBrains Mono | Code, data, measurements, micro-labels |

Mono is used for things that genuinely *are* code, data or measurement — not as decoration.
Ligatures are disabled everywhere, because JetBrains Mono renders `--` as a single dash and
would turn `--fail-on-error` into a flag that does not exist.

**Tokens.** Colours, fonts and spacing are CSS custom properties (`--tp-*`) defined once
per page on `.page`, with a dark-theme block that redefines the same names. To change the
palette, change the token block — do not hard-code colours in rules.

The shared file that note used to ask for now exists: `src/css/custom.css` declares the whole
palette at `:root` and maps Infima's variables onto it, which is what lets the documentation
be restyled from the same tokens as the pages. The five page stylesheets still carry their own
identical block and win on specificity, so nothing about them has changed yet. Removing those
five blocks is now a deletion rather than a rewrite, and is the remaining half of the job.

**Section grammar**, shared by every page: a two-digit number, a title, an optional lede,
then the content. Numbering is per page and runs `01`, `02`, `03`…

---

## 3. The pages

### Landing — `index.html`

**Who it is for.** A cold, problem-aware visitor: they own a pipeline with nothing between
`plan` and `apply`, and they do *not* yet know that policy engines are a category.

**Why it is ordered this way.** what → why → how → setup → proof → depth. The hero states
what the tool does and what it costs you before asking anyone to read further. The real
pull requests in section 04 prove the mechanism *after* it has been explained — they are
evidence, not the introduction.

**Structure**

1. Hero — headline, lede, a tabbed install command (GitHub Actions / local CLI), and a
   four-item strip of what it costs you.
2. `01` Why add a policy gate — three failure modes.
3. `02` Put Tirith between plan and apply — the four-step flow.
4. `03` Add Tirith to GitHub Actions — the actual YAML.
5. `04` Watch it catch a real mistake — five public demo pull requests, as a stepper.
6. `05` See exactly what a policy checks — the interactive specimen.
7. Close — start with one rule, then four doorways into the docs.

**The specimen** (section 05) is the page's set piece. One policy shown at display scale
with one draggable threshold; moving it re-evaluates a grid of resources and the verdict
readout changes with it. The verdict word is set in Martian Mono's variable *width* axis
driven by the same control, so dragging the threshold physically narrows and widens the
word. It is inert in this export.

### Learn — `learn.html`

**Job.** Take someone from "I have never written a policy" to a working one, in six steps
against a single document, adding one rule at a time.

**The thing that makes it work.** Every lesson is a live editor. In the real site the
policy actually evaluates in the browser — a documented subset of Tirith's engine
reimplemented in JavaScript — so changing a value moves the verdict, the messages and the
exit code in front of you. The page states its own limits rather than hiding them, because
a teaching tool that quietly disagrees with the real evaluator is worse than no tool.

**Structure.** Hero → a table of contents → six lessons, each *prose on the left, editor on
the right* → a free playground → an install close.

**Design note.** The prose/editor split is the page's whole shape and it is the constraint
worth respecting: the explanation has to be readable while the thing it describes is on
screen.

### AI — `ai.html`

**Job.** Show that Tirith is usable from a coding agent, without becoming vague AI-first
copy.

**The discipline that keeps it honest.** Every claim names a specific file or a specific
command, and everything on the page works today with nothing to install beyond Tirith. Each
claim was re-checked against the repository when the page was written.

**The argument.** Ask an agent for a guardrail and it writes plausible JSON against a schema
it is guessing at — `"type": "Exists"`, which is not a condition Tirith has. The engine
returns an unknown condition as an ordinary failed check with no error attached, so it is
indistinguishable from a real violation: the build goes red and someone loses an afternoon
to infrastructure that was fine. The fix is not a better prompt. It is giving the agent the
closed list, and making it run the policy before claiming the policy works.

**Structure.** Hero → `01` what goes wrong → `02` give it the vocabulary (three skill files
+ a copyable install command) → `03` give it a way to check itself (`tirith lint`, and a
table of the five traps) → `04` make it run the thing → `05` why there is no MCP server →
`06` what an agent cannot see across repositories → `07` what none of this does → close.

**Design note.** Section 02 was a three-column table in the earlier design and is now one
ruled row per file, because the path column wrapped mid-token at every width worth
supporting. Section 07 is deliberately unglamorous: a page about AI that never states its
boundaries is not trustworthy.

### Fleet governance — `fleet.html`

**Job.** Explain the commercial progression for a team that needs to discover, standardise,
approve and evidence Tirith governance across many repositories.

**Two rules that constrain the design and must survive any rework**

1. The first viewport must state that Tirith OSS is free, independent, and needs no
   StackGuardian account. It does so in the hero lede and again in the strip beside it.
2. The commercial CTA never outranks *Use Tirith OSS*. This is the one page where a
   commercial CTA is legitimately primary, and even here the open-source route appears
   beside it every time, never buried.

**Structure.** Hero → `01` which one is your problem → `02` what each one costs → `03` what
connecting adds (an eight-rung ladder) → `04` what the platform looks like → `05` full
capability comparison → `06` five FAQs → `07` the enquiry form.

**Two honesty devices worth keeping.** The eighth rung of the ladder is tagged **planned**
and dimmed, because Tirith calling the platform's workflow API is not shipped and the page
will not describe it in the present tense. And pricing says *Custom* rather than inventing
Free/Pro/Enterprise tiers.

**Section 04 is four empty wells.** The screenshots do not exist yet. They are drawn as
hatched, dashed placeholders at the 16:9 the real images will occupy, so the page will not
reflow when they land and so the amount of missing material is obvious to anyone reviewing.
They are supposed to look unfinished. When the images are captured they must come from a
demo organisation, never a customer's — those screens carry repository names, cloud
resource identifiers and run history.

**The form** posts directly to HubSpot from the browser. Only the enumerated fields
(repository band, CI systems, primary problem) are ever sent to analytics; the email,
organisation and free-text box are not, and must not be.

### Origins — `logo.html`

**Job.** Explain the idea behind the logo. Not a design record — it deliberately carries no
size specimens, no pixel thresholds, and no account of the candidate marks that were drawn
and rejected.

**The argument.** Tirith is named for Minas Tirith, a city that held because nothing reached
the summit in one move: seven walls, one gate each, every gate on the far side of the one
below. The defence was never the stone — it was the order the gates were in. The mark is
that city seen from above, reduced in four moves to a closed ring with two opposed gates,
which is a policy engine drawn as a floor plan.

**Structure.** Hero → `01` the city the name comes from → `02` the four-move reduction, with
diagrams → `03` opposed gates are the product.

**Design note.** This page is linked only from footers. It is background for someone who has
finished a product page, not a step toward installing anything.

### Docs, at `/tirith/docs/…`

The moment a visitor crosses from the designed pages into the documentation is historically
where a site stops feeling like one site. It used to be that here: stock Infima below the
navbar, which meant rounded pills, card shadows, a system typeface and six syntax colours.

It is now built from the same tokens. Two files do it, and the split is the point:

- **`src/css/custom.css`** declares the palette and maps Infima's variables onto it. One
  block moves the fonts, the accent and every corner radius at once, `--ifm-global-radius: 0`
  being the single line that squares the whole theme.
- **`src/css/docs.css`** handles only what a variable cannot express: hairlines where Infima
  draws cards, micro-labels where it draws sentence case, a rule above every `h2` so a long
  reference page has the same spine as a landing page, and a heading scale stepped down from
  the pages because documentation is read rather than scanned.

Three swizzles support it, all of them wrappers rather than ejections: `DocBreadcrumbs` hosts
the copy-page control, `PaginatorNavLink` draws previous/next, `Admonition` supplies icons.

**Syntax highlighting is one theme for both colour schemes**, defined in
`docusaurus.config.js` entirely in custom properties. That is not a shortcut:
prism-react-renderer writes its colours as inline `style` attributes on the token spans, and
an inline style cannot be overridden from a stylesheet, so naming variables is the only way
the highlighting can answer to the light/dark switch at all. Two hues, like everything else:
a key is ink, a value is the accent.

**The copy-page control** beside the breadcrumbs hands the page to an agent: copy the
markdown, view it, or open it in ChatGPT or Claude. It serves the `.md` twin that
`scripts/generate-llms-full.py` writes for every route, so it is a pointer at something that
already existed rather than a scrape of the rendered DOM.

Its last two items are **the only place on this site that draws a logo other than Tirith's
own**, which is a deliberate exception to the rule below and the reason it is written down.
The marks are the official single-path versions from simple-icons, unmodified, in
`src/components/docs/brandMarks.js`. The justification is recognition: "Open in ChatGPT"
beside a generic speech bubble is a control a reader has to read, and beside the real mark it
is one they can see. Every other glyph in the menu is stroked at the same hairline weight as
the rest of the design; these two are filled, because stroking a wordless trademark thickens
it into a blot and is a modification of someone else's mark.

The page bodies are authored Markdown and are not part of this design work.

---

## 4. Navigation

**Top bar:** Learn · AI · Fleet · Docs on the left; Policy Builder · GitHub on the right.

Recently trimmed. It used to also carry Install, Providers and Tirith UI as direct links
into the documentation sidebar, which made the bar read as a sitemap rather than a route
through the product. Those three are reachable from **Docs**.

**The Origins page** is intentionally absent from the bar and reachable only from footers.

**Footers** are a single ruled colophon strip, not a multi-column sitemap.

---

## 5. Constraints a redesign must not break

Design is open. These are not.

1. **No invented social proof.** There are no customers, logos, testimonials, benchmarks or
   adoption numbers for this project. Do not add any, including as placeholders — a
   greyed-out logo wall implies customers that do not exist.
2. **Claims are checked against the repository.** Every command, flag, file path and exit
   code on these pages was verified against the Tirith source. If a redesign rewrites body
   copy, the technical claims have to survive intact.
3. **The exit-code distinction.** `3` means a policy said no; `1` means Tirith could not
   tell you either way. Anywhere this appears, both halves must stay.
4. **The OSS/commercial boundary.** Fleet's two rules in section 3 above.
5. **Colour never carries a verdict alone.** Always a word too.
6. **Contrast and focus.** Body text stays at the current contrast, and every interactive
   element keeps a visible focus ring. The forms keep their real `<label>`s and the checkbox
   group keeps its `<legend>`.
7. **Wide content scrolls inside its own box.** Tables and code blocks may scroll
   horizontally; the page body must never.
8. **Both themes.** Every colour is a token with a dark-theme counterpart. A redesign that
   hard-codes a hex breaks dark mode silently.

---

## 6. Known weaknesses, if you are looking for what to fix

Honest list, from the people who built it:

- **The token block is duplicated** across five stylesheets. First thing to refactor.
- **The landing hero and the mark's letterhead** both set "Tirith" within ~100px of each
  other. It reads as repetition on a wide screen.
- **Section counts vary** — the AI page runs to `07`, the mark page to `03`. Whether the
  numbering should be consistent across pages is an open question.
- **Fleet section 04** is entirely placeholder, as described.
- **The Learn page has no footer colophon**, unlike every other page.
- **Long headline wraps.** The display face is wide, and several headlines break to four or
  five lines at large sizes. It is deliberate, but it is the most divisive thing here.
