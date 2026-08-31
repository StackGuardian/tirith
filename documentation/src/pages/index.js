import {useState} from 'react';
import Link from '@docusaurus/Link';
import Layout from '@theme/Layout';
import Heading from '@theme/Heading';

import TirithMark from '../components/brand/TirithMark';
import CopyField from '../components/landing/CopyField';
import PhaseJourney from '../components/landing/PhaseJourney';
import PlatformSetup from '../components/landing/PlatformSetup';
import Specimen from '../components/landing/Specimen';
import {INTEGRATIONS} from '../data/demoPhases';
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

const hero = {
  title: ['Stop unsafe IaC', 'before it is applied.'],
  lede:
    'Tirith is an open-source policy gate that checks infrastructure changes before ' +
    'OpenTofu or Terraform applies them. It reads the plan your pipeline already ' +
    'produces, tests ' +
    'it against JSON policies in your repository, and blocks the job when a rule fails.',
  cost:
    'Run it on your laptop, in GitHub Actions, or from any pipeline that can call the ' +
    'CLI. Policies are JSON files in your repository and evaluation happens on your own ' +
      'runner.',
  actions: [
    {
      id: 'github',
      label: 'GitHub Actions',
      command: `- uses: StackGuardian/tirith-iac-governance-action@v2
  with: {fail-on-error: true}`,
      prompt: false,
      facts: ['Apache-2.0', 'Runs on your runner', 'Comments on the pull request'],
      caveat:
        'The Action runs Tirith on the GitHub runner and reports the verdict on the pull ' +
        'request. The setup below adds the policy, plan export, and permissions.',
    },
    {
      id: 'gitlab',
      label: 'GitLab CI',
      command: `tirith:
  image: python:3.12
  script:
    - pip install "git+https://github.com/StackGuardian/tirith.git@1.2.0"
    - tirith -policy-path .tirith/policies -input-path plan.json --fail-on-error`,
      prompt: false,
      facts: ['Apache-2.0', 'Runs on your runner', 'Plan as an artifact'],
      caveat:
        'No wrapper to install — GitLab calls the CLI directly, which is what the GitHub ' +
        'Action does underneath. The job consumes the plan as an artifact.',
    },
    {
      id: 'bitbucket',
      label: 'Bitbucket',
      command: `- step:
    name: Policy gate
    script:
      - pip install "git+https://github.com/StackGuardian/tirith.git@1.2.0"
      - tirith -policy-path .tirith/policies -input-path plan.json --fail-on-error`,
      prompt: false,
      facts: ['Apache-2.0', 'Runs on your runner', 'Two steps'],
      caveat:
        'Plan in one step, gate in the next, passing plan.json between them as an ' +
        'artifact. The same CLI as every other pipeline.',
    },
    {
      id: 'anyci',
      label: 'Any CI',
      command:
        'pip install "git+https://github.com/StackGuardian/tirith.git@1.2.0"\n' +
        'tirith lint .tirith/policies\n' +
        'tirith -policy-path .tirith/policies -input-path plan.json --fail-on-error',
      prompt: false,
      facts: ['Apache-2.0', 'Any runner', 'Three commands'],
      caveat:
        'Three commands on anything that can produce a plan — Jenkins, Azure DevOps, CircleCI, ' +
        'a cron job. Gate on the exit code, which every CI system already does.',
    },
    {
      id: 'cli',
      label: 'Local CLI',
      command:
        'tirith --fail-on-error -policy-path .tirith/policies -input-path plan.json',
      prompt: true,
      facts: ['Apache-2.0', 'Runs on your machine', 'Works in any pipeline'],
      caveat:
        'Install Tirith first, then point the CLI at a policy or directory of policies ' +
        'and the document you want to check.',
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

const gap = {
  num: '01',
  title: 'Why add a policy gate?',
  lede:
    'OpenTofu and Terraform can produce a valid plan that still breaks a rule your team ' +
    'depends on. ' +
    'That decision needs to happen while the pipeline can still stop the change.',
  points: [
    {
      k: 'Manual review can miss things',
      v:
        'An empty owner tag, an oversized volume, or a destroy hidden inside a ' +
        'replacement can slip through a busy pull request.',
    },
    {
      k: 'After apply is too late',
      v:
        'Finding the problem after deployment means cleanup, rollback, and another ' +
        'round of review. The plan already contained the evidence.',
    },
    {
      k: 'Custom scripts are hard to maintain',
      v:
        'Every one-off check needs its own parsing, exit codes, error messages, and ' +
        'upkeep. Tirith keeps the rule in JSON and handles the pipeline behavior.',
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
    {n: '4', k: 'CI continues or stops', v: 'A pass moves on to apply. A failure explains the rejected values and exits non-zero.'},
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

const anywhere = {
  num: '05',
  title: 'Catch it before you push',
  lede:
    'The gate does not have to wait for CI. The same checks run at commit time and in ' +
    'your editor, which is where a policy an agent just wrote should be proved.',
};

const specimenPlate = {
  num: '06',
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
      body: 'Learn how Tirith reads OpenTofu and Terraform plans, Infracost, Kubernetes and JSON.',
      to: '/docs/tirith-providers/providers-overview/',
    },
    {
      glyph: 'ui',
      title: 'tirith ui',
      body: 'Inspect failures, build a policy, or experiment in the playground.',
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

function SectionHead({num, title, lede, tag}) {
  return (
    <div className={styles.sectionHead}>
      <div className={styles.sectionLabel}>
        <span className={styles.sectionNum}>{num}</span>
        <Heading as="h2" className={styles.sectionTitle}>
          {title}
        </Heading>
        {tag ? <span className={styles.betaTag}>{tag}</span> : null}
      </div>
      {lede ? <p className={styles.sectionLede}>{lede}</p> : null}
    </div>
  );
}

export default function Home() {
  const [heroActionId, setHeroActionId] = useState(hero.actions[0].id);
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
            <span className={styles.letterheadNote}>Policy as code · Apache-2.0</span>
          </div>

          <Heading as="h1" className={styles.h1}>
            {hero.title[0]}
            <span className={styles.h1Dim}>{hero.title[1]}</span>
          </Heading>

          <div className={styles.heroPlate}>
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
        </header>

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

        {/* ================= 05 RUNS ANYWHERE ================= */}
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
                    <span className={styles.integrationTitle}>{item.title}</span>
                    <span className={styles.integrationText}>{item.body}</span>
                  </span>
                  <span className={styles.cardArrow} aria-hidden="true">→</span>
                </Link>
              </li>
            ))}
          </ul>
        </section>

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
        </section>

        <footer className={styles.colophon}>
          <span className={styles.colophonBrand}>
            <TirithMark className={styles.colophonMark} size={16} />
            Tirith · StackGuardian
          </span>
          <span>Apache-2.0</span>
          {/*
           * The only route to the logo story, deliberately. It is background for
           * someone who has finished the page, not a step towards installing
           * anything, so it stays out of the navbar.
           */}
          <span>
            <Link to="/at-scale/">Tirith at scale</Link>
          </span>
          <span>
            <Link to="/logo/">The mark</Link>
          </span>
          <span>
            <Link href="https://github.com/StackGuardian/tirith">Source</Link>
          </span>
          <span>
            <Link href="https://join.slack.com/t/stackguardian-ol78820/shared_invite/zt-2ksag36j9-OjmXqQmyXudgYrV6FmesIQ">
              Slack
            </Link>
          </span>
        </footer>
      </main>
    </Layout>
  );
}
