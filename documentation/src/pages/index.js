import {useCallback, useEffect, useRef, useState} from 'react';
import Link from '@docusaurus/Link';
import Layout from '@theme/Layout';
import Heading from '@theme/Heading';

import TirithMark from '../components/brand/TirithMark';
import Colophon from '../components/site/Colophon';
import CopyField from '../components/landing/CopyField';
import PhaseJourney from '../components/landing/PhaseJourney';
import PlatformSetup from '../components/landing/PlatformSetup';
import Specimen from '../components/landing/Specimen';
import {INTEGRATIONS, SKILL_INSTALL} from '../data/demoPhases';
import {HIGHLIGHTS} from '../data/roadmap';
import {AGENT_BRIEF} from '../data/agentBrief';
import {CONTRIBUTORS} from '../data/contributors';
import styles from './index.module.css';
import '../css/chrome.module.css';

/*
 * ---------------------------------------------------------------------------
 * TIRITH — LANDING PAGE
 *
 * Visual world: Policy Specimen Sheet. This route is intentionally self-contained
 * so it can be reviewed without replacing the repository's current home page.
 *
 * WHO THIS PAGE IS WRITTEN FOR
 *   A cold, problem-aware visitor: they own a pipeline with nothing between
 *   plan and apply, and they do NOT yet know the policy-engine category. So the
 *   order is what -> why -> how -> setup -> proof -> depth. The public PRs prove
 *   the mechanism after the mechanism has been explained; they do not carry the
 *   burden of introducing the product themselves.
 *
 * COPY RULES FOR THIS FILE
 *   - Every claim is checked against the repository README and documentation/docs.
 *     Where the two disagree, the README wins.
 *   - There are no customers, logos, testimonials, benchmarks or adoption numbers
 *     for this project. Do not add any.
 * ---------------------------------------------------------------------------
 */

const REPO = 'https://github.com/StackGuardian/tirith';

/*
 * The secondary call to action, and the only ask on the page that is not "install it".
 *
 * It sits under the roadmap strip on purpose. Asking for a star next to the install command
 * competes with the install command; asking for one next to a list of unbuilt things is a
 * different request, because the reader has just been shown something they might want and
 * told it does not exist yet. Influence is the offer, and the star is the cheap version of
 * it rather than the point.
 *
 * Only the first is a ghost button and the rest are plain text. A secondary action that
 * looks primary is not secondary, and the accent on this page belongs to the copy button
 * in the hero.
 */
const involve = {
  note:
    'Influence our roadmap by asking for a feature or watching for releases.',
  /*
   * Faces, not a number. "18 contributors" is a statistic; eighteen avatars is a group of
   * people, and the claim this section makes is about people.
   *
   * The list is generated across every branch rather than from the contributors API, which
   * sees only the default branch and misses one of these eighteen. A page thanking the
   * community that leaves a contributor out is worse than no page.
   */
  community:
    'Tirith is built in the open by StackGuardian engineers and external contributors. ' +
    'It is licensed under Apache 2.0 and governed publicly. Contributions do not need to ' + 
    'be large: a tested policy, a CI example for an underserved system, or a reproducible bug ' +
    'report can be far more valuable than a star.',
  /*
   * Two buttons, then the quieter links. Four buttons would read as four equally weighted
   * decisions at the point where the page should be asking for something.
   *
   * The good-first-issue list leads, because the paragraph above says a bug report is worth
   * more than a star and the layout should not contradict the copy. The star gets the same
   * treatment rather than a louder one: it is the one ask a reader can satisfy in a second,
   * so it should not be buried in a row of text links, but order carries the hierarchy and
   * neither button shouts over the other.
   */
  primary: {
    label: 'Find a good first issue',
    href: `${REPO}/labels/good%20first%20issue`,
  },
  secondary: {
    label: 'Star on GitHub',
    href: REPO,
  },
  more: [
    {label: 'Ask for a feature', href: `${REPO}/issues/new/choose`},
    {label: 'Watch for releases', href: `${REPO}/releases`},
  ],
};

const hero = {
  title: ['Stop unsafe IaC', 'before it is applied.'],
  /*
   * Every capability here is checked against src/tirith/ before it is written down.
   *
   * SENSITIVE VALUES, and the exact shape of the claim, because this has been got wrong in
   * both directions. Tirith does read terraform's `before_sensitive` / `after_sensitive`
   * markers, in platform/redact.py, to mask flagged values client-side before anything is
   * uploaded. What it cannot do is let you write a policy *about* sensitivity: no provider
   * exposes those markers as a value a condition can test, and that is roadmap R3.
   *
   * So the claim belongs on the At scale page, where something is actually being sent, and
   * not in this lede. In local mode the document never leaves the machine, so there is
   * nothing to mask and the promise answers a question nobody asked.
   *
   * "Centralised policies" is `tirith platform check`, which does ship -- but centralised is
   * the opposite of this project's premise, so it is phrased as the option it is. The
   * commercial mode must not read as a condition of using the tool.
   *
   * The last clause is the one no competitor answers, so the sentence ends on it rather
   * than on a feature any scanner could also claim.
   */
  /*
   * The four assurances that used to sit in a band under the plate are folded in here.
   * Three of them were already being made: "checks the plan" and "failures explain why"
   * by the verdict clause, "local first" by "on your own runner". Only "policies are
   * JSON" was a claim this paragraph did not make, so only that one arrives as new words,
   * and the band goes. Net saving is about forty words and a full-width row.
   */
  lede:
    'Plug IaC governance into any pipeline you already run. Policies are JSON, not a ' +
    'program in Rego or Python. Tirith evaluates the plan on your own runner, enforces ' +
    'one policy set across repositories when you want one, and returns a single verdict ' +
    'before the change is applied.',
  // "On your own runner" is the lede's line now, so this no longer repeats it.
  actions: [
    /*
     * First here for the same reason it leads the tabs in section 03: it is not a sixth
     * platform, it is the other way of producing any of the five after it. Being first
     * also makes it the plate's opening state, which is the point -- a reader who already
     * knows they want the Action clicks past it in one move.
     *
     * It replaced the "Rather delegate?" line that used to sit under this plate. A tab
     * named Coding agent and a sentence underneath offering the same thing were the same
     * offer made twice, and the tab is the one that can carry the command.
     */
    {
      id: 'agent',
      label: 'Coding agent',
      command:
        `${SKILL_INSTALL}\n` +
        '\n' +
        '# then, in your agent:\n' +
        '"Add a Tirith policy gate to our pipeline"',
      prompt: false,
      facts: ['Any agent with a shell', 'Reads the real schema', 'You review the PR'],
      // Deliberately the shortest caveat of the six. The argument for this route is made
      // once, in section 02; repeating it here made the default tab the wordiest thing
      // above the fold.        'this one, so you need not name your CI. It drafts; the engine still decides.',
    },
    {
      id: 'github',
      label: 'GitHub Actions',
      /*
       * The plan step leads every one of these, because it is the join to the pipeline
       * the reader already has. Without it the snippet starts mid-job and plan.json
       * arrives from nowhere -- the one thing a reader has to wire up themselves is the
       * one thing the block did not show. `-input=false` because CI has no terminal to
       * prompt at, and it is the flag whose absence hangs a job rather than failing it.
       */
      command: `- run: terraform plan -out=tfplan -input=false

- uses: StackGuardian/tirith-iac-governance-action@v2
  with:
    plan-file: tfplan
    fail-on-error: true`,
      prompt: false,
      // Two, specifically: pull-requests: write for the comment, checks: write for the
      // check run. It is the only setup step the Action cannot do for you, and the one
      // thing people get wrong on a first install.
      facts: ['Needs two write permissions', 'Runs on your runner', 'No plan JSON on disk'],
    },
    {
      id: 'gitlab',
      label: 'GitLab CI',
      // Two jobs, not one: the gate consumes the plan as an artifact, and
      // the producing job is what makes that sentence mean something.
      command: `plan:
  script:
    - terraform plan -out=tfplan -input=false
    - terraform show -json tfplan > plan.json
  artifacts: {paths: [plan.json]}

tirith:
  image: python:3.12
  needs: [plan]
  script:
    - pip install "git+https://github.com/StackGuardian/tirith.git@1.2.0"
    - tirith -policy-path .tirith/policies -input-path plan.json --fail-on-error`,
      prompt: false,
      facts: ['No wrapper to install', 'Runs on your runner', 'Plan as an artifact'],
    },
    {
      id: 'bitbucket',
      label: 'Bitbucket',
      // Plan in one step, gate in the next: the snippet has to show both, and
      // the block only ever showed the second one.
      command: `- step:
    name: Terraform plan
    script:
      - terraform plan -out=tfplan -input=false
      - terraform show -json tfplan > plan.json
    artifacts: [plan.json]

- step:
    name: Policy gate
    script:
      - pip install "git+https://github.com/StackGuardian/tirith.git@1.2.0"
      - tirith -policy-path .tirith/policies -input-path plan.json --fail-on-error`,
      prompt: false,
      facts: ['Any Python 3.8 image', 'Runs on your runner', 'Two steps'],
    },
    {
      id: 'anyci',
      label: 'Any CI',
      // `tirith lint` stays commented while 1.2.0 is the pinned release: it is on main but
      // not in that tag, so a reader pasting this block would get a failing step. A comment
      // is inert in shell and in YAML, which keeps the block runnable and still shows it.
      command:
        'pip install "git+https://github.com/StackGuardian/tirith.git@1.2.0"\n' +
        '# tirith lint .tirith/policies   # not in 1.2.0 yet, on main\n' +
        'tirith -policy-path .tirith/policies -input-path plan.json --fail-on-error',
      prompt: false,
      facts: ['Gate on the exit code', 'Any runner', 'Two commands'],
    },
    {
      id: 'cli',
      label: 'Local CLI',
      /*
       * The install line is in the snippet itself. The tab whose whole job is the bare
       * command has to be runnable from what it shows.
       *
       * Not PyPI: `py-tirith` is unpublished and the bare `tirith` name belongs to an
       * unrelated monitoring package, so `pip install tirith` would quietly install
       * someone else's software. The tag is pinned for the same reason CI pins it.
       *
       * No `-input=false` on the plan here, unlike the CI tabs -- that flag exists so a
       * job fails instead of waiting for a prompt, and a terminal has someone to answer.
       *
       * prompt:false because CopyField renders a single `$`, which reads as one command
       * when there are four. Every other multi-line action does the same.
       */
      command:
        'pip install "git+https://github.com/StackGuardian/tirith.git@1.2.0"\n' +
        'terraform plan -out=tfplan\n' +
        'terraform show -json tfplan > plan.json\n' +
        'tirith --fail-on-error -policy-path .tirith/policies -input-path plan.json',
      prompt: false,
      facts: ['Nothing leaves your machine', 'Runs on your machine', 'No account'],
    },
  ],
};

/*
 * The announcement slot.
 *
 * A reusable row, not a one-off for `tirith ui`. The page's front matter is a React
 * object rather than markdown, so nothing here changes when a release ships unless
 * someone edits this file -- which is how the previous announcement went stale and
 * then disappeared entirely when the page was replaced. Keeping it as one named
 * object means the next release swaps four strings, and `null` removes the row.
 *
 * `tag` announces and `body` qualifies. The interface is genuinely new -- a tag
 * reading BETA would label it without announcing anything -- but it is also a beta,
 * and the reference page opens by saying so, so the sentence says so too rather than
 * setting a second tag a few pixels from the first.
 *
 * Two entries, and two is the cap: a row of announcements announces nothing. Each cell is
 * its own link, so a reader aiming at one cannot land on the other. An empty array removes
 * the row. The skill pack leads: it is the newer thing and the one the rest of the page is
 * built around, and the first cell is the one a reader's eye lands on.
 */
const announcements = [
  {
    id: 'skills',
    tag: 'New',
    // Named, not explained. This row is the smallest of the three places the pack appears,
    // and its whole job is that a reader learns the option exists before they start typing.
    command: 'skill pack',
    body: 'teaches your coding agent the real schema, and how to put a gate in a pipeline.',
    to: '/skills/',
    linkLabel: 'Set it up',
  },
  {
    id: 'ui',
    tag: 'New',
    // No backticks: this is JSX text, not markdown, so they would render literally.
    // The renderer sets the command in <code>.
    command: 'tirith ui',
    // A banner is read at a glance or not at all, so it carries the two things the tool is
    // for and nothing else. Validation as you type and serving the playground to a team are
    // the page it links to, not this line.
    body:
      'explores a failing evaluation down to the resource that caused it, and builds ' +
      'policies from a form.',
    to: '/docs/tirith-usage/interactive-interface/',
    linkLabel: 'Read more',
  },
];


/*
 * The delegated route, shown in three sizes rather than as a section of its own.
 *
 * It was a section once. That was wrong: handing the job to an agent is not a fourth thing
 * to do after the three steps, it is the same three steps typed at something else, and a
 * section implied a reader had to choose it deliberately rather than notice it while
 * choosing a platform. So it now appears beside the commands themselves, at whatever size
 * the surrounding surface can carry:
 *
 *   announcement  a name, in the row that already announces `tirith ui`
 *   hero          the leading tab of the install plate, with the command
 *   03 setup      the leading tab of the platform panel, with the command
 *
 * One installer string for all three, so there is one thing to keep correct.
 */
/* The installer itself lives in ../data/demoPhases, imported at the top of this file. */

/*
 * One section, two registers per step.
 *
 * This was two sections telling the same story: a four-step narrative of what happens, then
 * a three-step instruction for what you do, whose steps mapped onto the narrative almost
 * one to one (export the plan = step 1, commit a policy = step 3, run the gate = step 4).
 * Each step now carries both: the sentence says what happens, the `do` line says what you
 * type. The platform tabs sit underneath, answering "and how do I invoke that here" for
 * whichever runner you use.
 *
 * All four note bullets went to the docs, which already carry them. None of them was a
 * reason to adopt, and the CI integration page is where someone setting this up is reading.
 */
const how = {
  num: '01',
  title: 'Add Tirith to your pipeline',
  // One line. The four steps below say the rest, and the tabs make the last clause obvious.
  lede: 'Your IaC tool produces the plan, Tirith checks it, and the exit code decides.',
  steps: [
    {
      n: '1',
      k: 'Your IaC tool plans',
      do: 'tofu show -json tfplan > plan.json',
    },
    {
      n: '2',
      k: 'Tirith reads the plan',
      do: '-input-path plan.json',
      product: true,
    },
    {
      n: '3',
      k: 'Policies test the change',
      do: 'commit rules under .tirith/policies',
    },
    {
      n: '4',
      k: 'CI continues or stops',
      do: '--fail-on-error, so a violation exits 3',
    },
  ],
};

const proof = {
  num: '02',
  title: 'Watch it catch a real mistake',
  lede: 'Five chapters in a public demo repository, from first gate to published state.',
};

/*
 * Restored once `tirith lint` and `tirith fmt` landed and .pre-commit-hooks.yaml started
 * publishing both ids. The tense is present because the commands exist; the one thing this
 * repository still does not ship is .vscode/tasks.json, so the docs page gives those tasks
 * inline rather than linking to a file that is not there.
 */
const anywhere = {
  num: '03',
  title: 'Catch it before you push',
  /*
   * Corrected. This used to read "the gate does not have to wait for CI, the same checks
   * run in a pre-commit hook", which was false in the way that matters: the hooks run
   * `tirith lint` and `tirith fmt`, and both read the policy file, never the change. Shape,
   * not meaning, in lint.py's own words. The old sentence even carried its own refutation
   * ("neither needs a plan document"): a check that needs no plan cannot be the gate.
   */
  // The two cards carry the detail. This only has to draw the distinction.
  lede: 'Two checks, and only one of them needs a plan.',
};

const specimenPlate = {
  num: '04',
  title: 'See exactly what a policy checks',
  lede: 'Change the threshold below and watch the verdict update.',
};

const explore = {
  items: [
    {
      glyph: '$',
      title: 'Installation',
      body: 'Choose the GitHub Action or install the CLI for another pipeline.',
      to: '/docs/tirith-installation/quick-installation/',
    },
    {
      glyph: '{}',
      title: 'Providers',
      body: 'Learn how Tirith reads OpenTofu and Terraform plans, Kubernetes, Infracost, StackGuardian workflows, and any other JSON or YAML document.',
      to: '/docs/tirith-providers/providers-overview/',
    },
    {
      glyph: 'ui',
      title: 'tirith ui',
      body: 'Inspect failures down to the resource, build a policy from a form, validate as you type, or serve the playground to your team over HTTP.',
      to: '/docs/tirith-usage/interactive-interface/',
      tag: 'Beta',
    },
    {
      glyph: 'org',
      title: 'Tirith at scale',
      body: 'One rule scales the same way: the platform reads what you already run, your agent writes the rules to match.',
      to: '/at-scale/',
      tag: 'Optional',
    },
  ],
};

/*
 * The close, and the only place the "write your own rule" argument is now made.
 *
 * It was a numbered section as well, under this exact heading, which meant the page argued
 * the point in the middle and then repeated the headline at the bottom. The points moved
 * down here because this is where a reader is deciding what to do next, and the note that
 * was already here is the instruction those three points justify. Proving a policy before
 * trusting it is the skill pack's standing instruction and the docs' job, not a line the
 * close has to carry.
 *
 * The at-scale bridge folded into the explore card of the same name rather than sitting as
 * its own line: a sentence and a card linking to the same page, two lines apart, is one
 * link too many.
 */
const finale = {
  title: 'Start with one rule.',
  note:
    'A catalogue covers the mistakes everyone makes. Pick the rule only you can state: ' +
    'something your team already checks by hand.',
  points: [
    {k: 'A policy is data', v: 'JSON with conditions in it. No rule language, no plugin.'},
    {k: 'So an agent can write it', v: 'The skill pack gives it the real condition list, so it cannot invent one.'},
    {k: 'The engine decides, not the model', v: 'Same evaluator, same exit code, your runner.'},
  ],
  links: [
    {to: '/docs/tirith-installation/quick-installation/', label: 'Installation'},
    {to: '/learn/', label: 'Learn to write a policy'},
  ],
};

/* --------------------------------------------------------------------------- */

/*
 * `planned` picks .tagPlanned -- a dashed rule and faint ink -- over .betaTag's solid
 * accent. The distinction is the point: BETA is shipped and rough, IN DEV is not shipped.
 * The dashed border was already in the stylesheet for this and had never been used.
 */
function SectionHead({num, title, lede, tag, planned}) {
  return (
    <div className={styles.sectionHead}>
      <div className={styles.sectionLabel}>
        <span className={styles.sectionNum}>{num}</span>
        <Heading as="h2" className={styles.sectionTitle}>
          {title}
        </Heading>
        {tag ? (
          <span className={planned ? styles.tagPlanned : styles.betaTag}>{tag}</span>
        ) : null}
      </div>
      {lede ? <p className={styles.sectionLede}>{lede}</p> : null}
    </div>
  );
}

/*
 * Agent mode.
 *
 * The same page, in the form a machine reads. Everything here already existed as a static
 * file: this is llms.txt, imported through a generated module so the two cannot disagree,
 * and shown to whoever asked for it rather than only to crawlers.
 *
 * It replaces the page rather than sitting under it. Someone who has switched to this view
 * has said what they want, and leaving six sections of marketing below it would mean they
 * still have to scroll past the thing they just opted out of.
 *
 * The letterhead and the toggle stay, so the switch is reversible without the back button,
 * and the colophon stays because the footer is navigation.
 */
/*
 * Copies the brief and says so for a moment. The clipboard call can reject outright in an
 * insecure context or when permission is denied, so the fallback selects the pane's text
 * and tells the reader to press the shortcut: failing silently on the one control this view
 * exists for would be worse than the extra branch.
 */
function CopyBrief() {
  const [state, setState] = useState('idle');
  const timer = useRef(null);

  useEffect(() => () => clearTimeout(timer.current), []);

  const copy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(AGENT_BRIEF);
      setState('copied');
    } catch {
      const pane = document.getElementById('agent-brief-pane');
      if (pane && window.getSelection) {
        const range = document.createRange();
        range.selectNodeContents(pane);
        const sel = window.getSelection();
        sel.removeAllRanges();
        sel.addRange(range);
      }
      setState('manual');
    }
    clearTimeout(timer.current);
    timer.current = setTimeout(() => setState('idle'), 2400);
  }, []);

  const label =
    state === 'copied' ? 'Copied' : state === 'manual' ? 'Press copy' : 'Copy the brief';

  return (
    <div className={styles.agentCopy}>
      <button type="button" className={styles.btnPrimary} onClick={copy}>
        {label} <span aria-hidden="true">→</span>
      </button>
      <span className={styles.agentCopySize}>
        {(AGENT_BRIEF.length / 1024).toFixed(1)} KB of plain text
      </span>
      <span className={styles.srOnly} role="status">
        {state === 'copied' ? 'Brief copied to clipboard' : ''}
      </span>
    </div>
  );
}

function AgentView() {
  return (
    <section className={styles.agent}>
      <div className={styles.agentHead}>
        <div>
          <p className={styles.agentTitle}>Everything on this page, as text</p>
          <p className={styles.agentNote}>
            Written for a model rather than a reader: what Tirith is, the install command
            that actually works, and the things answers about it usually get wrong. Paste it
            into an assistant, or point the assistant at the URL below.
          </p>
        </div>
        {/*
         * A button, not a CopyField. CopyField's job is to show a command and copy it, which
         * is right for a one-line install and wrong here: the brief is already shown in the
         * pane below, and rendering it twice made the control eight kilobytes tall.
         */}
        <CopyBrief />
      </div>

      <pre className={styles.agentPane} id="agent-brief-pane">
        {AGENT_BRIEF}
      </pre>

      <ul className={styles.agentLinks}>
        <li>
          <Link href="https://stackguardian.github.io/tirith/llms.txt">llms.txt</Link>
          <span>this text, as a file</span>
        </li>
        <li>
          <Link href="https://stackguardian.github.io/tirith/llms-full.txt">llms-full.txt</Link>
          <span>every documentation page in one file</span>
        </li>
        <li>
          <Link href="https://stackguardian.github.io/tirith/docs/tirith-usage/exit-codes.md">
            any page, as markdown
          </Link>
          <span>the route plus .md, beside the HTML</span>
        </li>
        <li>
          <Link href="https://github.com/StackGuardian/tirith/tree/main/.claude/skills">
            skill packs
          </Link>
          <span>writing policies, generating a set from your IaC, migrating from Sentinel</span>
        </li>
      </ul>
    </section>
  );
}

export default function Home() {
  const [heroActionId, setHeroActionId] = useState(hero.actions[0].id);
  const [agent, setAgent] = useState(false);
  const heroAction = hero.actions.find((action) => action.id === heroActionId);

  return (
    <Layout
      title="Tirith - complete IaC governance"
      description={
        'Tirith is an Apache-2.0 policy gate that checks OpenTofu and Terraform plans against ' +
        'JSON ' +
        'policies before apply. Run it locally or in CI without an account.'
      }>
      <main className={styles.page}>
        {/*
         * A band between the navbar and the sheet, not the sheet's first line.
         *
         * It began inside <header>, above the letterhead, which read correctly on this
         * page alone and pushed the letterhead ~66px below where it sits on learn,
         * skills, at-scale and logo -- so moving between pages made the Tirith row jump.
         * Out here it is the navbar's neighbour, .hero's top padding opens every page on
         * the same line, and the strip still precedes the letterhead.
         *
         * Each cell is a link across its full width -- a reader aiming at "Read more"
         * should not be able to miss and hit nothing -- but the row is no longer one
         * link, because it now carries two destinations.
         */}
        {announcements.length ? (
          <div className={styles.announce}>
            {announcements.map((item) => (
              <Link className={styles.announceItem} key={item.id} to={item.to}>
                <span className={styles.betaTag}>{item.tag}</span>
                <span className={styles.announceBody}>
                  <code className={styles.announceCommand}>{item.command}</code>{' '}
                  {item.body}
                </span>
                <span className={styles.announceLink}>
                  {item.linkLabel} <span aria-hidden="true">→</span>
                </span>
              </Link>
            ))}
          </div>
        ) : null}

        {/* ================= HERO ================= */}
        <header className={styles.hero}>
          {/*
           * The sheet's letterhead. The mark, the name and the one-line statement of
           * what this is, on a single ruled row -- the same device the section heads
           * use, so the page opens in its own language rather than with a logo
           * floating above unrelated type.
           *
           * The wordmark is set in the page's own display face here, not drawn: the
           * navbar directly above already carries the drawn lockup, and repeating it
           * at two sizes a few pixels apart reads as a mistake.
           */}
          <div className={styles.letterhead}>
            <TirithMark className={styles.letterheadMark} size={40} />
            <span className={styles.letterheadName}>Tirith</span>
            <span className={styles.letterheadRule} aria-hidden="true" />
            <span className={styles.letterheadNote}>Open-source IaC governance · Apache-2.0</span>
            {/*
             * Two buttons rather than a checkbox or a switch: the states are named, so
             * nobody has to work out which way "on" points. aria-pressed carries the state
             * to a screen reader, which a pair of plain buttons otherwise would not.
             */}
            <div className={styles.modeToggle} role="group" aria-label="View this page as">
              <button
                type="button"
                className={styles.modeButton}
                data-active={!agent ? 'true' : undefined}
                aria-pressed={!agent}
                onClick={() => setAgent(false)}>
                Human
              </button>
              <button
                type="button"
                className={styles.modeButton}
                data-active={agent ? 'true' : undefined}
                aria-pressed={agent}
                onClick={() => setAgent(true)}>
                Agent
              </button>
            </div>
          </div>

          {agent ? null : (
            <>
            <Heading as="h1" className={styles.h1}>
              {hero.title[0]}
              <span className={styles.h1Dim}>{hero.title[1]}</span>
            </Heading>

            {/*
             * Install first, prose second -- in the DOM, not just visually. Reordering with
             * CSS `order` would leave the tab sequence running right-to-left across the
             * plate: a keyboard user would reach the copy button before the tabs that decide
             * what it copies. Both columns hold controls, so source order has to match.
             */}
            <div className={styles.heroPlate}>
              <div className={styles.heroAction}>
                <div className={styles.actionTabs} aria-label="Choose how to run Tirith">
                  {hero.actions.map((action) => (
                    <button
                      type="button"
                      key={action.id}
                      className={styles.actionTab}
                      data-active={action.id === heroAction.id ? 'true' : undefined}
                      aria-pressed={action.id === heroAction.id}
                      onClick={() => setHeroActionId(action.id)}>
                      {action.label}
                    </button>
                  ))}
                </div>
                <CopyField
                  key={heroAction.id}
                  command={heroAction.command}
                  label={`hero-${heroAction.id}`}
                  prompt={heroAction.prompt}
                />
                <ul className={styles.facts}>
                  {heroAction.facts.map((f) => (
                    <li key={f}>{f}</li>
                  ))}
                </ul>
              </div>

              <div className={styles.heroLede}>
                <p className={styles.lede}>{hero.lede}</p>
                <div className={styles.heroLinks}>
                  <a className={styles.btnPrimary} href="#setup">
                    Add the gate <span aria-hidden="true">→</span>
                  </a>
                  <Link
                    className={styles.btnGhost}
                    to="/docs/tirith-installation/quick-installation/">
                    Other installation paths <span aria-hidden="true">→</span>
                  </Link>
                </div>
              </div>
            </div>

            </>
          )}
        </header>

        {agent ? (
          <AgentView />
        ) : (
          <>
          {/* ================= 01 ADD IT TO YOUR PIPELINE ================= */}
          <section className={styles.section} id="setup">
            <SectionHead {...how} />
            <ol className={styles.howFlow}>
              {how.steps.map((step) => (
                <li className={step.product ? styles.howProduct : undefined} key={step.n}>
                  <span className={styles.howNum}>{step.n}</span>
                  <h3>{step.k}</h3>
                  {/* What you type for that step, so the flow is also the instructions. */}
                  <p className={styles.howDo}>
                    <code>{step.do}</code>
                  </p>
                </li>
              ))}
            </ol>
            <div className={styles.quickCode}>
              <PlatformSetup />
            </div>
            <div className={styles.quickLinks}>
              <Link to="/docs/tirith-installation/quick-installation/">
                Full installation guide <span aria-hidden="true">→</span>
              </Link>
              <Link to="/learn/">
                Start with a worked policy <span aria-hidden="true">→</span>
              </Link>
            </div>

          </section>

          {/* ================= 02 REAL PROOF ================= */}
          <section className={styles.section}>
            <SectionHead {...proof} />
            <PhaseJourney />
          </section>

          {/* ================= 03 RUNS ANYWHERE ================= */}
          <section className={styles.section}>
            <SectionHead {...anywhere} />
            <ul className={styles.integrations}>
              {INTEGRATIONS.map((item) => (
                <li key={item.title}>
                  <Link className={styles.integration} to={item.to}>
                    <span className={styles.integrationGlyph} aria-hidden="true">
                      {item.glyph}
                    </span>
                    <span className={styles.integrationBody}>
                      <span className={styles.integrationTitle}>
                        {item.title}
                        {item.inDev ? (
                          <span className={styles.tagPlanned}>In dev</span>
                        ) : null}
                      </span>
                      <span className={styles.integrationText}>{item.body}</span>
                    </span>
                    <span className={styles.cardArrow} aria-hidden="true">→</span>
                  </Link>
                </li>
              ))}
            </ul>
          </section>

          {/* ================= 04 THE SPECIMEN ================= */}
          <section className={styles.section}>
            <SectionHead {...specimenPlate} />
            <Specimen />
          </section>

          {/* ================= CLOSE ================= */}
          <section className={styles.finale}>
            <div className={styles.finaleGrid}>
              <div>
                <Heading as="h2" className={styles.finaleTitle}>
                  {finale.title}
                </Heading>
                <p className={styles.finaleNote}>{finale.note}</p>
              </div>
              <div className={styles.finaleLinks}>
                {finale.links.map((l, index) => (
                  <Link
                    className={index === 0 ? styles.btnPrimary : styles.btnGhost}
                    key={l.to}
                    to={l.to}>
                    {l.label} <span aria-hidden="true">→</span>
                  </Link>
                ))}
              </div>
            </div>
            <dl className={styles.defs}>
              {finale.points.map((pt) => (
                <div className={styles.def} key={pt.k}>
                  <dt>{pt.k}</dt>
                  <dd>{pt.v}</dd>
                </div>
              ))}
            </dl>
            <p className={styles.routeLabel}>Explore the focused guides</p>
            <ul className={styles.exploreCards}>
              {explore.items.map((item) => (
                <li key={item.title}>
                  <Link className={styles.exploreCard} to={item.to}>
                    <span className={styles.exploreGlyph} aria-hidden="true">
                      {item.glyph}
                    </span>
                    <span className={styles.exploreBody}>
                      <span className={styles.exploreTitle}>
                        {item.title}
                        {item.tag ? <span className={styles.betaTag}>{item.tag}</span> : null}
                      </span>
                      <span className={styles.exploreText}>{item.body}</span>
                    </span>
                    <span className={styles.cardArrow} aria-hidden="true">→</span>
                  </Link>
                </li>
              ))}
            </ul>

            {/*
             * Four lines and a link, inside the existing finale rather than as a section 07.
             * The home page's job is to say that work is happening and where to read about
             * it; reproducing the roadmap here would push the shipped material further down
             * the page to describe things nobody can use yet.
             *
             * Every row is tagged, and the tags are the same two the roadmap page uses.
             */}
            <p className={styles.routeLabel}>Being built next</p>
            <ul className={styles.aheadStrip}>
              {HIGHLIGHTS.map((h) => (
                <li key={h.title}>
                  <span className={styles.aheadHead}>
                    <span className={styles.aheadTitle}>{h.title}</span>
                    <span className={h.status === 'inDev' ? styles.betaTag : styles.tagPlanned}>
                      {h.status === 'inDev' ? 'In dev' : 'Planned'}
                    </span>
                  </span>
                  <span className={styles.aheadBody}>{h.body}</span>
                </li>
              ))}
            </ul>
            <p className={styles.aheadMore}>
              <Link to="/roadmap/">
                The whole roadmap, and roughly when <span aria-hidden="true">→</span>
              </Link>
            </p>

            <div className={styles.involve}>
              <Heading as="h2" className={styles.sectionTitle}>
                Get involved
              </Heading>
              {/*
                 * Captioned rather than labelled from above, because the heading now names
                 * the section rather than the row: without a line of its own the faces are
                 * a group of strangers the reader has no way to place.
                 */}
              <figure className={styles.contributors}>
                <ul className={styles.faces}>
                  {CONTRIBUTORS.map((c) => (
                    <li key={c.login}>
                      <Link href={`https://github.com/${c.login}`} title={c.login}>
                        <img
                          className={styles.face}
                          src={`https://avatars.githubusercontent.com/u/${c.id}?s=96&v=4`}
                          alt={c.login}
                          width={40}
                          height={40}
                          loading="lazy"
                        />
                      </Link>
                    </li>
                  ))}
                </ul>
                <figcaption className={styles.contributorsNote}>
                  Built by the community.
                </figcaption>
              </figure>
              <p className={styles.involveNote}>{involve.community}</p>
              <p className={styles.involveNote}>{involve.note}</p>
              {/* Wrapped, because bare grid children would stretch the buttons full width. */}
              <div className={styles.involveLinks}>
                <Link className={styles.btnGhost} href={involve.primary.href}>
                  {involve.primary.label} <span aria-hidden="true">→</span>
                </Link>
                <Link className={styles.btnGhost} href={involve.secondary.href}>
                  {involve.secondary.label} <span aria-hidden="true">→</span>
                </Link>
              </div>
              <div className={styles.involveMore}>
                {involve.more.map((l) => (
                  <Link key={l.label} href={l.href}>
                    {l.label}
                  </Link>
                ))}
              </div>
            </div>
          </section>
          </>
        )}

        <Colophon styles={styles} />
      </main>
    </Layout>
  );
}
