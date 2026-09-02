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
import {INTEGRATIONS} from '../data/demoPhases';
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
   * One button, because four of them read as four equally weighted decisions at the point
   * where the page should be asking for one thing.
   *
   * The button is the good-first-issue list and not the star. The paragraph above it says
   * a bug report is worth more than a star, so giving the star the loudest element would
   * have the layout contradicting the copy, and starring is not contributing. The rest run
   * from the ask that takes real work down to the one that costs nothing.
   */
  primary: {
    label: 'Find a good first issue',
    href: `${REPO}/labels/good%20first%20issue`,
  },
  more: [
    {label: 'Ask for a feature', href: `${REPO}/issues/new/choose`},
    {label: 'Watch for releases', href: `${REPO}/releases`},
    {label: 'Star on GitHub', href: REPO},
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
  lede:
    'Plug IaC governance into any pipeline you already run. Tirith evaluates the plan on ' +
    'your own runner, enforces one policy set across repositories when you want one, and ' +
    'returns a single actionable verdict before the change is applied, including the ' +
    'outcome every scanner reports as success: a check that never ran.',
  // "On your own runner" is the lede's line now, so this no longer repeats it.
  actions: [
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
      caveat:
        'The Action runs Tirith on the GitHub runner and reports the verdict on the pull ' +
        'request. Handing it the binary plan rather than exporting JSON first is one step ' +
        'shorter, and renders the plan in memory, so no unmasked plan JSON is written to ' +
        'the workspace. The setup below adds the policy and the permissions.',
    },
    {
      id: 'gitlab',
      label: 'GitLab CI',
      // Two jobs, not one: the caveat says the gate consumes the plan as an artifact, and
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
      caveat:
        'No wrapper to install — GitLab calls the CLI directly, which is what the GitHub ' +
        'Action does underneath. The job consumes the plan as an artifact.',
    },
    {
      id: 'bitbucket',
      label: 'Bitbucket',
      // "Plan in one step, gate in the next" -- the caveat already promised two steps and
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
      caveat:
        'Plan in one step, gate in the next, passing plan.json between them as an ' +
        'artifact. The same CLI as every other pipeline.',
    },
    {
      id: 'anyci',
      label: 'Any CI',
      // `tirith lint` is commented, not dropped: it is in development and not in 1.2.0,
      // so a reader pasting this block would get a failing step. A comment is inert in
      // shell and in YAML, which keeps the block runnable and still shows what is coming.
      command:
        'pip install "git+https://github.com/StackGuardian/tirith.git@1.2.0"\n' +
        '# tirith lint .tirith/policies   # in dev, not in 1.2.0\n' +
        'tirith -policy-path .tirith/policies -input-path plan.json --fail-on-error',
      prompt: false,
      facts: ['Gate on the exit code', 'Any runner', 'Two commands'],
      caveat:
        'Two commands on anything that can produce a plan — Jenkins, Azure DevOps, CircleCI, ' +
        'a cron job. Gate on the exit code, which every CI system already does. The lint step ' +
        'is commented out because it has not shipped yet.',
    },
    {
      id: 'cli',
      label: 'Local CLI',
      /*
       * The install line is here rather than in the caveat, which used to say "install
       * Tirith first" and then not say how -- the one tab whose whole job is the bare
       * command was the one that could not be run from what it showed.
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
      caveat:
        'The same CLI every pipeline above calls. Point it at a policy or a directory of ' +
        'policies and the document you want to check — any JSON or YAML document, not only ' +
        'a plan.',
    },
  ],
  assurances: [
    {
      k: 'Checks the plan',
      v: 'Evaluate the proposed change while the pipeline can still stop it.',
    },
    {
      k: 'Policies are JSON',
      v: 'Describe allowed values without maintaining a program in Rego or Python.',
    },
    {
      k: 'Failures explain why',
      v: 'See which check failed, which value was rejected, and why it failed.',
    },
    {
      k: 'Local first',
      v: 'Keep policies beside your code. Organization mode remains optional.',
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
 */
const announcement = {
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
};

/*
 * Cut roughly in half. This is the first section after the hero, where a reader is still
 * deciding whether to keep going, and three points that each took two sentences to make one
 * argument were the densest thing above the fold.
 *
 * Nothing was dropped. Each point kept its concrete example, which is the part that carries
 * it, and lost the clause restating the heading: "can slip through a busy pull request"
 * after a heading reading "manual review can miss things" says the same thing twice.
 */
const gap = {
  num: '01',
  title: 'Why add a policy gate?',
  lede:
    'A valid plan can still break a rule your team depends on, and the pipeline is the ' +
    'last place that can stop it.',
  points: [
    {
      k: 'Review misses things',
      v: 'An empty owner tag, an oversized volume, a destroy hidden inside a replacement.',
    },
    {
      k: 'After apply is too late',
      v: 'Cleanup and rollback, for something the plan already showed you.',
    },
    {
      k: 'Scripts rot',
      v: 'Every one-off check carries its own parsing, exit codes and upkeep.',
    },
  ],
};

const how = {
  num: '02',
  title: 'Put Tirith between plan and apply.',
  lede:
    'Tirith fits into the pipeline you already have. Your IaC tool produces the plan, ' +
    'Tirith checks it, and the exit code tells the pipeline whether to continue.',
  steps: [
    {n: '1', k: 'Your IaC tool plans', v: 'OpenTofu or Terraform exports the proposed change as plan.json.'},
    {
      n: '2',
      k: 'Tirith reads the plan',
      v: 'The plan provider finds the resources and attributes each policy asks for, from either tool.',
      product: true,
    },
    {n: '3', k: 'Policies test the change', v: 'JSON conditions check each matching value and produce one verdict.'},
    {n: '4', k: 'CI continues or stops', v: 'A pass moves on to apply. A failure explains the rejected values and, with fail-on-error, exits 3.'},
  ],
};

const setup = {
  num: '03',
  title: 'Add Tirith to your pipeline',
  lede:
    'Three pieces make the gate work, and they are the same three everywhere: a policy, ' +
    'the plan as JSON, and Tirith running with fail-on-error. Only the way you invoke it ' +
    'changes between platforms.',
  steps: [
    {n: '1', k: 'Commit a policy', v: 'Put one or more JSON rules under .tirith/policies/.'},
    {n: '2', k: 'Export the plan', v: 'Run tofu show -json tfplan > plan.json (or terraform show).'},
    {n: '3', k: 'Run the gate', v: 'Set fail-on-error so a failed policy blocks the job.'},
  ],
  notes: [
    'OpenTofu works identically — swap terraform for tofu; the plan JSON is the same',
    'Policies are JSON files committed under .tirith/policies',
    'On GitHub the Action adds the pull-request comment and check run, which need the two write permissions',
    'Without fail-on-error, Tirith reports findings but does not block the job',
  ],
};

const proof = {
  num: '04',
  title: 'Watch it catch a real mistake',
  lede:
    'Five chapters, played out in a public demo repository on each of the three forges ' +
    'above: add the local gate, watch it block an empty Owner tag, clear the failure with ' +
    'a one-line fix, then move policy to the organization and publish state.',
};

/*
 * Both halves of this section are unshipped. The pre-commit hook needs
 * .pre-commit-hooks.yaml and the editor loop needs .vscode/tasks.json; neither file is in
 * this repository, and both drive `tirith lint`, which is not in the released CLI either
 * -- src/tirith/cli.py dispatches `platform` and `ui` and nothing else.
 *
 * Tagged rather than cut: the docs page it links to is written and the work is real. The
 * tense moves to the conditional so the section describes a plan, not a feature.
 */
const anywhere = {
  num: '05',
  title: 'Catch it before you push',
  tag: 'In dev',
  planned: true,
  lede:
    'The gate will not have to wait for CI. The same checks are being wired into a ' +
    'pre-commit hook and an editor task, which is where a policy an agent just wrote ' +
    'should be proved. Neither has shipped yet.',
};

const specimenPlate = {
  // '06' until the section above it was hidden. See the restore note there before changing.
  num: '05',
  title: 'See exactly what a policy checks',
  lede:
    'A policy answers three questions: what to read, which values to inspect, and what ' +
    'must be true. Change the threshold below and watch the verdict update.',
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
      body: 'Share policies across repositories and keep run history in StackGuardian.',
      to: '/at-scale/',
      tag: 'Optional',
    },
  ],
};

const finale = {
  title: 'Start with one rule.',
  note:
    'Choose something your team already checks by hand, commit it as a JSON policy, ' +
    'and run it against the next plan.',
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
          <Link href="https://github.com/StackGuardian/tirith/tree/main/.claude/skills/tirith-policies">
            skill pack
          </Link>
          <span>drop-in instructions for a coding agent</span>
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
      title="Tirith — open-source policy checks for OpenTofu and Terraform plans"
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
         * The whole row is the link -- a reader aiming at "Read more" should not be able
         * to miss and hit nothing.
         */}
        {announcement ? (
          <Link className={styles.announce} to={announcement.to}>
            <span className={styles.betaTag}>{announcement.tag}</span>
            <span className={styles.announceBody}>
              <code className={styles.announceCommand}>{announcement.command}</code>{' '}
              {announcement.body}
            </span>
            <span className={styles.announceLink}>
              {announcement.linkLabel} <span aria-hidden="true">→</span>
            </span>
          </Link>
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
                <p className={styles.caveat}>{heroAction.caveat}</p>
              </div>

              <div className={styles.heroLede}>
                <p className={styles.lede}>{hero.lede}</p>
                <p className={styles.cost}>{hero.cost}</p>
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

            {/* What it costs you, before anything asks the visitor to read further. */}
            <ul className={styles.assure}>
              {hero.assurances.map((a) => (
                <li key={a.k}>
                  <span className={styles.assureK}>{a.k}</span>
                  <span className={styles.assureV}>{a.v}</span>
                </li>
              ))}
            </ul>
            </>
          )}
        </header>

        {agent ? (
          <AgentView />
        ) : (
          <>
          {/* ================= 01 GAP ================= */}
          <section className={styles.section}>
            <SectionHead {...gap} />
            <dl className={styles.defs}>
              {gap.points.map((p) => (
                <div className={styles.def} key={p.k}>
                  <dt>{p.k}</dt>
                  <dd>{p.v}</dd>
                </div>
              ))}
            </dl>
          </section>

          {/* ================= 02 HOW IT WORKS ================= */}
          <section className={styles.section}>
            <SectionHead {...how} />
            <ol className={styles.howFlow}>
              {how.steps.map((step) => (
                <li className={step.product ? styles.howProduct : undefined} key={step.n}>
                  <span className={styles.howNum}>{step.n}</span>
                  <h3>{step.k}</h3>
                  <p>{step.v}</p>
                </li>
              ))}
            </ol>
          </section>

          {/* ================= 03 QUICK START ================= */}
          <section className={styles.section} id="setup">
            <SectionHead {...setup} />
            <div className={styles.quickStart}>
              <ol className={styles.quickSteps}>
                {setup.steps.map((step) => (
                  <li key={step.n}>
                    <span className={styles.stepNum}>{step.n}</span>
                    <div>
                      <h3>{step.k}</h3>
                      <p>{step.v}</p>
                    </div>
                  </li>
                ))}
              </ol>
              <div className={styles.quickCode}>
                <PlatformSetup />
              </div>
            </div>
            <ul className={styles.quickNotes}>
              {setup.notes.map((note) => (
                <li key={note}>{note}</li>
              ))}
            </ul>
            <div className={styles.quickLinks}>
              <Link to="/docs/tirith-installation/quick-installation/">
                Full installation guide <span aria-hidden="true">→</span>
              </Link>
              <Link to="/learn/">
                Start with a worked policy <span aria-hidden="true">→</span>
              </Link>
            </div>
          </section>

          {/* ================= 04 REAL PROOF ================= */}
          <section className={styles.section}>
            <SectionHead {...proof} />
            <PhaseJourney />
          </section>

          {/*
           * ================= RUNS ANYWHERE: HIDDEN =================
           *
           * Removed for now. Both halves of it were unshipped anyway: the pre-commit hook
           * needs .pre-commit-hooks.yaml and the editor loop needs .vscode/tasks.json, and
           * both drive `tirith lint`, none of which are in the released package. It was
           * already tagged In dev for that reason, so the page lost a tag rather than a
           * feature.
           *
           * A `false` guard rather than a comment: JSX children cannot take a line comment,
           * and the guard keeps the markup parsed so it cannot rot while switched off.
           *
           * TO RESTORE: change `false` to `true`, and put `specimenPlate.num` back to '06'.
           * It was moved to '05' to close the gap this left, because the section numerals are
           * set large on this page and 04 followed by 06 reads as a fault rather than a
           * choice. `anywhere` and the INTEGRATIONS import are both still in place.
           */}
          {false && (
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
          )}

          {/* ================= 05 THE SPECIMEN ================= */}
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
              {/* Wrapped, because a bare grid child would stretch the button full width. */}
              <div className={styles.involveLinks}>
                <Link className={styles.btnGhost} href={involve.primary.href}>
                  {involve.primary.label} <span aria-hidden="true">→</span>
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
