import Link from '@docusaurus/Link';
import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

import {EVENTS, track} from '../analytics';
import {
  ACTION_REPO,
  Action,
  Doorway,
  Hero as PageHero,
  NEW_ISSUE,
  PageShell,
  issueUrl,
  REPO,
  Section,
  Todo,
  TrackedCode,
  VisualSlot,
  styles,
} from '../components/site';

/*
 * ---------------------------------------------------------------------------
 * COPY
 *
 * All prose for the landing page lives in this one object, deliberately kept
 * apart from the markup below so it can be edited or lifted out without
 * reading any JSX.
 *
 * Two rules this file follows, from the landing page messaging brief:
 *
 *   1. Local mode leads. Everything above the fold is true without an account,
 *      without credentials and without a network call. Platform mode is one
 *      clearly-fenced section near the bottom, and is never implied earlier.
 *
 *   2. Nothing is claimed that the repository cannot currently back. Where the
 *      brief asks for a number, a logo, a demo URL or a GitLab catalog
 *      component that does not exist yet, the value is a TODO placeholder --
 *      rendered visibly, listed in LAUNCH_BLOCKERS below, and not something
 *      this page can go public with still in place.
 *
 * Technical claims here are quoted from the docs, which are the source of
 * truth: exit codes from docs/tirith-usage/exit-codes.md, the action snippet
 * and inputs from docs/tirith-usage/ci-integration.md, masking behaviour from
 * docs/tirith-usage/platform-check.md. If the two disagree, the docs win and
 * this file is stale.
 * ---------------------------------------------------------------------------
 */

/*
 * The page cannot ship publicly while any of these are unresolved. They are
 * listed here rather than only inline so that one grep -- or one glance at
 * this constant -- gives the whole set.
 */
const LAUNCH_BLOCKERS = [
  // Home
  'Proof-strip numbers and any customer logo approval (section: proof)',
  'Hero visual and the PR-2 failure GIF (sections: hero, verdict)',
  'Demo repository and PR 1-4 URLs, plus a credential-free PR 0 (section: demo)',
  'GitLab CI catalog component URL, or drop the native claim (section: pipelines)',
  'Optional platform-mode screenshot (section: modes)',
  'Traction counters on this page share the Traction page snapshot job (section: receipts)',

  // Companion pages
  'Traction: the scheduled snapshot job and traction-data.json (/traction)',
  'Traction: stars-over-time, cadence, policy-work and contributor displays (/traction)',
  'Learn: lessons 4-7 and the course shell that carries progress (/learn)',
  'Playground: encryption and location templates have no maintained example (/playground)',
  'Playground: per-template provenance before community policies are listed (/playground, /policies)',
  'Fleet: HUBSPOT_PORTAL_ID and HUBSPOT_FORM_GUID, and the matching HubSpot properties (/fleet)',
  'Policies: the advertised check count needs a status label and approval (/policies)',
  'Policies: the sign-up URL, currently routed to /fleet instead (/policies)',
  'AI: the StackGuardian MCP package name, so install commands can be generated (/ai)',
];

const content = {
  hero: {
    eyebrow: 'Open-source IaC governance',
    title: 'Put governance in front of every Terraform plan.',
    body:
      'Tirith plugs into the pipeline you already run, evaluates Terraform or OpenTofu plans on ' +
      'infrastructure you already control, and stops non-compliant changes before apply. A few ' +
      'lines to start. No ' +
      'account, no migration and no new policy language to program.',
    trust: [
      'Apache-2.0',
      'Runs wherever your pipeline runs',
      'No account required',
      'Terraform + OpenTofu',
    ],
    primary: {label: 'Star Tirith on GitHub', href: REPO},
    secondary: {label: 'Govern your first pipeline', to: '/docs/tirith-usage/ci-integration/'},
    announcement: {
      label: 'New',
      command: 'tirith ui',
      text:
        '— an interactive interface. Explore a failing evaluation down to the resource that ' +
        'caused it, build policies from a form, and experiment in a playground.',
      to: '/docs/tirith-usage/interactive-interface/',
      linkLabel: 'Read more',
    },
  },

  /*
   * The quick start. Three tabs because the three audiences arrive with
   * different constraints, and sending a GitLab reader to a GitHub Action is
   * how you lose them. Each tab is a complete, copyable job -- not a fragment.
   */
  start: {
    heading: 'Start where you are. Add one governance step.',
    body:
      'Keep your existing plan job. Tirith reads the plan JSON it already produces and evaluates ' +
      'policies committed under .tirith/policies. Everything runs inside the pipeline you ' +
      'already have: your GitHub or GitLab runners, your Jenkins agents, your private build ' +
      'infrastructure, and nothing is uploaded.',
    tabs: [
      {
        value: 'gha',
        label: 'GitHub Actions',
        language: 'yaml',
        code:
          '- run: terraform show -json tfplan > plan.json\n' +
          '- uses: StackGuardian/tirith-iac-governance-action@v2\n' +
          '  with: {fail-on-error: true}',
        note:
          'With a plan.json in the working directory that is the whole integration. The action ' +
          'needs pull-requests: write and checks: write to post its sticky comment and check run.',
        expandedLabel: 'Show the permissions block',
        expanded:
          'permissions:\n' +
          '  contents: read\n' +
          '  pull-requests: write   # sticky comment\n' +
          '  checks: write          # check run\n' +
          '\n' +
          'steps:\n' +
          '  - run: |\n' +
          '      terraform plan -out=tfplan -input=false\n' +
          '      terraform show -json tfplan > plan.json\n' +
          '\n' +
          '  - uses: StackGuardian/tirith-iac-governance-action@v2\n' +
          '    with: {fail-on-error: true}',
      },
      {
        value: 'gitlab',
        label: 'GitLab CI',
        language: 'yaml',
        code:
          'policy:\n' +
          '  image: python:3.12\n' +
          '  needs: [plan]\n' +
          '  script:\n' +
          '    - pip install "git+https://github.com/StackGuardian/tirith.git@1.2.0"\n' +
          '    - tirith -policy-path .tirith/policies -input-path plan.json --fail-on-error',
        note:
          'The CLI directly, which is all the action does underneath. Nothing here is ' +
          'GitLab-specific: any runner that can execute a container and produce a plan works the ' +
          'same way.',
      },
      {
        value: 'cli',
        label: 'pip / any CI',
        language: 'bash',
        code:
          '# Tirith is not on PyPI. pip install tirith installs an unrelated\n' +
          '# project of the same name -- install from git, and pin a tag so a\n' +
          '# CI job cannot change behaviour underneath you.\n' +
          'pip install "git+https://github.com/StackGuardian/tirith.git@1.2.0"\n' +
          '\n' +
          'terraform show -json tfplan > plan.json\n' +
          'tirith -policy-path .tirith/policies -input-path plan.json --fail-on-error',
        note:
          'Python 3.8 or newer. git ls-remote --tags lists the available tags; 1.2.0 is the ' +
          'newest.',
      },
    ],
  },

  proof: {
    heading: 'Policy evaluation trusted inside enterprise cloud delivery',
    body:
      'Tirith powers policy evaluation within StackGuardian deployments used by teams governing ' +
      'some of the world’s largest cloud estates.',
    stats: [
      {value: '[X]+', label: 'repositories governed'},
      {value: '[Y]+', label: 'plans evaluated'},
      {value: '[Z]+', label: 'cloud resources covered'},
      {value: '[N]', label: 'enterprise teams'},
    ],
  },

  problem: {
    heading: 'Your pipeline can plan and apply. What decides whether it should?',
    body:
      'Terraform and OpenTofu make infrastructure repeatable. They do not make every change safe, ' +
      'compliant or understood. Rules get copied between repositories, reviews depend on whoever ' +
      'is available, and a failing job often says less than the plan that caused it.',
    points: [
      {
        title: 'Different pipeline, different guardrails',
        body:
          'The same standard is implemented differently — or not at all — across repositories and ' +
          'CI systems.',
      },
      {
        title: 'A wall of findings is not a decision',
        body:
          'Teams need to know what failed, on which resource and value, and whether apply is ' +
          'allowed.',
      },
      {
        title: 'Governance should travel with the change',
        body:
          'The useful moment is after plan and before apply, inside the workflow developers ' +
          'already use.',
      },
    ],
  },

  verdict: {
    heading: 'A verdict a developer can act on.',
    body:
      'Tirith names the rule, resource, planned action and value behind the result. A failed ' +
      'policy can block the job; a tool error remains visibly different from a policy saying no; ' +
      'a check that could not run never earns a false pass.',
    points: [
      {
        title: 'Visible',
        body:
          'A sticky pull-request comment and GitHub Check put the result where the change is ' +
          'reviewed.',
      },
      {
        // Deliberately says "where it can": a check that fails because an
        // attribute is absent has no value to hang a resource address on, so
        // it reports the rule and the attribute rather than the address.
        // Promising an address every time would be a promise the engine does
        // not currently keep.
        title: 'Explainable',
        body:
          'Every result names the rule and the value behind it, and where the attribute exists ' +
          'to be read, the resource address and its create, update or delete action.',
      },
      {
        title: 'Controllable',
        body: 'Use the exit code to warn, fail or stop the path to apply.',
      },
    ],
    /*
     * The exit-code table is the concrete form of "a non-answer must not
     * masquerade as a pass", which is otherwise just a claim. Quoted from
     * docs/tirith-usage/exit-codes.md.
     */
    exitCodes: [
      {code: '0', meaning: 'Policies passed, or nothing was in scope to gate on'},
      {code: '3', meaning: 'A policy ran and said no: your change violates a rule'},
      {
        code: '1',
        meaning:
          'Tirith could not tell you either way: bad input, an unevaluable policy, every check ' +
          'skipped',
      },
    ],
    exitNote:
      '3 is not 1 by design. A pipeline can page the platform team on 1 and the change author ' +
      'on 3, and both surfaces fail closed: anything that leaves the verdict unknown exits ' +
      'non-zero regardless of --fail-on-error.',
    exitLink: {label: 'The full exit-code contract', to: '/docs/tirith-usage/exit-codes/'},
  },

  ladder: {
    heading: 'Add control one pull request at a time.',
    body:
      'Tirith does not require a migration programme. Start with one plan, learn from the ' +
      'verdict, then expand only when the next level of control earns its place.',
    stages: [
      {stage: 'Observe', outcome: 'See every evaluated plan and result in the pull request.'},
      {stage: 'Understand', outcome: 'Trace a failure to the rule, resource, action and value.'},
      {
        stage: 'Recommend',
        outcome: 'Show the smallest compliant change or route it to the right owner.',
      },
      {
        stage: 'Remediate',
        outcome: 'Fix the code and watch the same gate clear.',
      },
      {
        stage: 'Govern',
        outcome: 'Reuse policy across pipelines; optionally centralise policy, approvals and evidence.',
        optional: true,
      },
      {
        stage: 'Execute',
        outcome: 'Keep your existing apply or, when ready, move governed execution into StackGuardian.',
        optional: true,
      },
    ],
  },

  demo: {
    heading: 'A real Terraform pipeline. Four pull requests.',
    body:
      'Each one adds a little more control without replacing the pipeline. The first three are the ' +
      'whole before-apply loop: the gate arrives, it catches a real violation, and a one-line fix ' +
      'clears it.',
    /*
     * Each card reserves the asset that proves its claim. A demo section that
     * only describes four pull requests asks the reader to take the whole
     * before-apply loop on trust -- the one thing this page exists to show
     * rather than assert.
     */
    cards: [
      {
        n: '1',
        title: 'Add the gate',
        body: 'Route the plan you already produce through Tirith. No new job and no change to Terraform.',
        asset:
          'GIF of the workflow YAML diff on the left, then the pull-request comment and the ' +
          '`Tirith IaC Governance` check run appearing on the right. Keep the whole diff in ' +
          'frame: eight lines is the point.',
      },
      {
        n: '2',
        title: 'See a real violation',
        body: 'An empty Owner tag turns the check red. The resource is not created and Apply is visibly skipped.',
        asset:
          'Screenshot of the failed check expanded: the rule that fired, the resource address, its ' +
          'planned action, the missing Owner value, and the Apply job showing as skipped below it.',
      },
      {
        n: '3',
        title: 'Fix the code',
        body: 'One line satisfies the rule. The same gate clears without a ticket, exception workflow or separate console.',
        asset:
          'GIF of the one-line diff adding the tag, then the same check turning green and Apply ' +
          'becoming available. Same viewport as card 2, so the only thing that changes is the verdict.',
      },
      {
        n: '4',
        title: 'Keep deployed evidence',
        body:
          'Optional platform mode publishes a masked state snapshot after apply so proposed and ' +
          'deployed infrastructure can be reviewed together.',
        platform: true,
        asset:
          'Screenshot of the run and state snapshot in StackGuardian after apply, with the masked ' +
          'values visible as `__SG_REDACTED__` so the masking is shown rather than claimed.',
      },
    ],
    help: {
      label: 'Ask a maintainer to help with your first pipeline',
      href: issueUrl({template: 'first-pipeline-help.md'}),
    },
  },

  scanner: {
    heading: 'Use scanners for coverage. Use Tirith to govern the change.',
    body:
      'Tirith is a policy engine, but its job is not to replace every scanner or policy language. ' +
      'It turns the plan your pipeline already produces and the policies you choose into one ' +
      'enforceable decision before apply. Run Tirith policies locally; bring OPA, Checkov and ' +
      'cost findings into the same governed verdict when you use platform mode.',
    supporting:
      'The goal is fewer disconnected tools to interpret — not another list to reconcile.',
  },

  policies: {
    heading: 'Policies are JSON data, not programs.',
    body:
      'Describe the provider, the value to inspect and the condition it must satisfy. Tirith ' +
      'handles the traversal and returns the resource-level evidence.',
    code: `{
  "meta": {
    "version": "v1",
    "required_provider": "stackguardian/terraform_plan",
    "name": "Every resource carries a costcenter tag"
  },
  "evaluators": [{
    "id": "costcenter_tag_present",
    "provider_args": {
      "operation_type": "attribute",
      "terraform_resource_type": "*",
      "terraform_resource_attribute": "tags.costcenter"
    },
    "condition": {"type": "IsNotEmpty"}
  }],
  "eval_expression": "costcenter_tag_present"
}`,
    note:
      'What makes this workable is not that policy is easy, since a complicated rule is complicated in ' +
      'any language, but that there is a schema, a form-based builder, worked examples, and no ' +
      'second policy runtime to operate.',
    actions: [
      {label: 'Browse the policy catalogue', to: '/policies'},
      {label: 'Evaluate or build one', to: '/playground'},
      {label: 'Read the policy reference', to: '/docs/tirith-policies/tirith-policy-reference/'},
    ],
  },

  pipelines: {
    heading: 'One policy contract across every pipeline.',
    body:
      'Tirith is a CLI, not an integration built into one CI system. Use the native GitHub ' +
      'Action, or invoke the CLI anywhere that can run a container and produce a Terraform or ' +
      'OpenTofu plan: GitLab CI, Jenkins, CircleCI, Azure Pipelines, Buildkite, a self-hosted ' +
      'runner inside your own network, or a laptop. The policy, result shape and exit-code ' +
      'contract stay the same in every one of them.',
    /*
     * Four tiles rather than a longer list, because the point is coverage
     * rather than a directory: a reader on Jenkins or an air-gapped runner has
     * to be able to place themselves here, and an exhaustive list of CI
     * vendors would imply the ones missing from it are unsupported.
     */
    integrations: [
      {name: 'GitHub Actions', how: 'Native action', href: ACTION_REPO},
      {
        name: 'GitLab CI',
        how: 'CLI in the job',
        todo: 'catalog component URL required before claiming native',
      },
      {name: 'Jenkins, CircleCI, any container CI', how: 'CLI in a container step'},
      {name: 'Self-hosted, air-gapped, or a laptop', how: 'CLI, no network, no account'},
    ],
    secondary:
      'Tirith can also evaluate Terraform state, Kubernetes manifests, Infracost breakdowns and ' +
      'arbitrary JSON. This page stays focused on plans because that is where a decision can ' +
      'still stop an unsafe change.',
    secondaryLink: {label: 'All providers', to: '/docs/tirith-providers/providers-overview/'},
  },

  modes: {
    heading: 'Keep it local. Centralise it only when you need to.',
    columns: ['OSS local mode', 'Optional platform mode'],
    rows: [
      ['Account', 'None', 'StackGuardian organisation and token'],
      ['Policy source', 'Files in your repository', 'Centrally managed policy sets'],
      ['Evaluation', 'Wherever your pipeline runs', 'Platform workflow, after client-side masking'],
      ['Network', 'None', 'Masked plan, results and metadata; source is user-controlled'],
      ['Reporting', 'PR comment, check and CLI output', 'Central history, evidence and prioritisation'],
      ['Control', 'Warn or fail via the pipeline exit code', 'Approvals, credential brokering and governed execution'],
      ['Remediation', 'Developer fixes the code', 'Assisted remediation'],
    ],
    hook:
      'Governing more than one pipeline? StackGuardian can discover Terraform and OpenTofu ' +
      'repositories, prioritise gaps by severity and open installation pull requests for your ' +
      'approval.',
    // Predates the Fleet page and used to dump the reader on a blank issue
    // form. The page now exists and answers exactly this question.
    cta: {label: 'What fleet-wide governance involves', to: '/fleet'},
    dataHandling:
      'Credentials are what select platform mode; there is no other switch. Terraform-sensitive ' +
      'values are masked locally, by the machine running Tirith, before upload, but those ' +
      'markers are not exhaustive and a secret hardcoded in a .tf file is not masked. Use ' +
      '--no-source when source must not leave your network.',
    dataLink: {label: 'What is masked and uploaded', to: '/docs/tirith-usage/platform-check/'},
  },

  community: {
    heading: 'Open source first. Clear boundaries by design.',
    points: [
      {
        title: 'Apache-2.0',
        body: 'Use, inspect, fork and run Tirith without a StackGuardian account.',
      },
      {
        title: 'Local stays local',
        body:
          'In OSS mode policies and plans never leave the machine evaluating them, wherever that ' +
          'machine is; Tirith makes no network call.',
      },
      {
        title: 'Platform mode is explicit',
        body:
          'Credentials select platform mode. The documentation states what is masked, what is ' +
          'uploaded and how to disable source upload.',
      },
      {
        title: 'Maintainer-led',
        body: 'Tirith is governed by its maintainers, with engineering support from StackGuardian.',
      },
      {
        title: 'Built in public',
        body: 'Report bugs, propose features and challenge decisions through GitHub Issues.',
      },
    ],
    actions: [
      {label: 'Open an issue', href: NEW_ISSUE},
      {label: 'Pick a good first issue', href: `${REPO}/labels/good%20first%20issue`},
      {label: 'Read GOVERNANCE.md', href: `${REPO}/blob/main/GOVERNANCE.md`},
    ],
  },

  final: {
    heading: 'Govern the next plan — not the next platform migration.',
    body:
      'Add Tirith to one Terraform or OpenTofu pipeline, open a pull request and see the first ' +
      'evaluated plan. Keep it local for as long as that is all you need.',
    micro:
      'Apache-2.0. No account. No cloud credentials. Your infrastructure, your policies, your ' +
      'pipeline.',
  },
};

/*
 * ---------------------------------------------------------------------------
 * MARKUP
 * ---------------------------------------------------------------------------
 */

function Hero() {
  const {eyebrow, title, body, trust, primary, secondary, announcement} = content.hero;
  return (
    <>
      <Link className={styles.announcement} to={announcement.to}>
        <span className={styles.announcementLabel}>{announcement.label}</span>
        <span>
          <code>{announcement.command}</code> {announcement.text}
        </span>
        <span className={styles.announcementLink}>{announcement.linkLabel} →</span>
      </Link>

      <PageHero
        eyebrow={eyebrow}
        title={title}
        body={body}
        trust={trust}
        actions={[
          {...primary, primary: true, onClick: track(EVENTS.heroStar, {source: 'hero'})},
          {...secondary, onClick: track(EVENTS.quickstart, {ci_system: 'unspecified'})},
        ]}
      >
        <VisualSlot>
          Hero visual. An animated split view: an existing pipeline YAML gains the Tirith step while
          the adjacent PR comment resolves from evaluating to a precise pass/fail verdict. A visible
          <code>local mode</code> label, and no StackGuardian UI in the first frame.
        </VisualSlot>
      </PageHero>
    </>
  );
}

function QuickStart() {
  const {heading, body, tabs} = content.start;
  return (
    <Section id="start" heading={heading}>
      <p>{body}</p>
      <Tabs groupId="ci-system" queryString>
        {tabs.map((tab) => (
          <TabItem key={tab.value} value={tab.value} label={tab.label}>
            <TrackedCode language={tab.language} ciSystem={tab.value}>
              {tab.code}
            </TrackedCode>
            <p className={styles.muted}>{tab.note}</p>
            {tab.expanded ? (
              <details className={styles.details}>
                <summary>{tab.expandedLabel}</summary>
                <TrackedCode language={tab.language} ciSystem={tab.value}>
                  {tab.expanded}
                </TrackedCode>
              </details>
            ) : null}
          </TabItem>
        ))}
      </Tabs>
    </Section>
  );
}

function Proof() {
  const {heading, body, stats} = content.proof;
  return (
    <Section id="proof" heading={heading} tone="quiet">
      <p>{body}</p>
      <dl className={styles.stats}>
        {stats.map((stat) => (
          <div key={stat.label}>
            <dt className={styles.statValue}>{stat.value}</dt>
            <dd>{stat.label}</dd>
          </div>
        ))}
      </dl>
      <Todo>
        Replace every bracketed figure with a verified number. Add customer logos only where
        approval covers this exact Tirith-powered claim; otherwise use anonymised industry labels.
      </Todo>
    </Section>
  );
}

function Problem() {
  const {heading, body, points} = content.problem;
  return (
    <Section id="problem" heading={heading}>
      <p>{body}</p>
      <div className={styles.cards}>
        {points.map((point) => (
          <div key={point.title} className={styles.card}>
            <h3>{point.title}</h3>
            <p>{point.body}</p>
          </div>
        ))}
      </div>
    </Section>
  );
}

function Verdict() {
  const {heading, body, points, exitCodes, exitNote, exitLink} = content.verdict;
  return (
    <Section id="verdict" heading={heading}>
      <p>{body}</p>
      <div className={styles.cards}>
        {points.map((point) => (
          <div key={point.title} className={styles.card}>
            <h3>{point.title}</h3>
            <p>{point.body}</p>
          </div>
        ))}
      </div>

      <table className={styles.table}>
        <thead>
          <tr>
            <th>Exit</th>
            <th>Meaning</th>
          </tr>
        </thead>
        <tbody>
          {exitCodes.map((row) => (
            <tr key={row.code}>
              <td>
                <code>{row.code}</code>
              </td>
              <td>{row.meaning}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className={styles.muted}>{exitNote}</p>
      <p>
        <Link to={exitLink.to}>{exitLink.label}</Link>
      </p>

      <VisualSlot>
        GIF of PR 2 failing the Owner-tag rule. Highlight the resource, the missing value and Apply
        being skipped. Do not crop away the repository context.
      </VisualSlot>
    </Section>
  );
}

function Ladder() {
  const {heading, body, stages} = content.ladder;
  return (
    <Section id="adoption" heading={heading}>
      <p>{body}</p>
      <ol className={styles.ladder}>
        {stages.map((stage) => (
          <li key={stage.stage}>
            <span className={styles.ladderStage}>
              {stage.stage}
              {stage.optional ? <span className={styles.optionalTag}>optional</span> : null}
            </span>
            <span>{stage.outcome}</span>
          </li>
        ))}
      </ol>
    </Section>
  );
}

function Demo() {
  const {heading, body, cards, help} = content.demo;
  return (
    <Section id="demo" heading={heading}>
      <p>{body}</p>
      <div className={styles.cards}>
        {cards.map((card) => (
          <div
            key={card.n}
            className={card.platform ? `${styles.card} ${styles.cardPlatform}` : styles.card}
          >
            <span className={styles.cardNumber}>{card.n}</span>
            <h3>{card.title}</h3>
            <p>{card.body}</p>
            {card.platform ? <span className={styles.optionalTag}>platform mode</span> : null}
            <VisualSlot compact label={`PR ${card.n}`}>
              {card.asset}
            </VisualSlot>
            <p className={styles.muted}>
              <Todo>PR {card.n} URL</Todo>
            </p>
          </div>
        ))}
      </div>

      <Todo>
        The existing four-PR demo repository requires a StackGuardian organisation and token, so it
        demonstrates platform mode. Label it as such, and add a credential-free PR 0 or companion
        repository with <code>.tirith/policies</code> committed locally that reaches the same first
        verdict with no credentials. Supply both URLs.
      </Todo>

      <VisualSlot label="CLI">
        Terminal recording of the same evaluation run locally: the command, the per-resource results
        scrolling past, the summary line, and <code>echo $?</code> printing <code>3</code>. Proof
        that the pull-request verdict and the laptop verdict are the same verdict.
      </VisualSlot>

      <p>
        <Link href={help.href} onClick={track(EVENTS.helpIssue, {ci_system: 'unspecified'})}>
          {help.label}
        </Link>{' '}
        , which is an issue template rather than a sales form.
      </p>
    </Section>
  );
}

function Scanner() {
  const {heading, body, supporting} = content.scanner;
  return (
    <Section id="scanner" heading={heading}>
      <p>{body}</p>
      <p className={styles.pullQuote}>{supporting}</p>
    </Section>
  );
}

function Policies() {
  const {heading, body, code, note, actions} = content.policies;
  return (
    <Section id="policies" heading={heading}>
      <p>{body}</p>
      <TrackedCode language="json" ciSystem="none">
        {code}
      </TrackedCode>
      <p className={styles.muted}>{note}</p>
      <ul className={styles.inlineLinks}>
        {actions.map((action) => (
          <li key={action.label}>
            {action.to ? (
              <Link to={action.to} onClick={track(EVENTS.policyExample, {policy_name: action.label})}>
                {action.label}
              </Link>
            ) : (
              <Link href={action.href} onClick={track(EVENTS.policyExample, {policy_name: action.label})}>
                {action.label}
              </Link>
            )}
          </li>
        ))}
      </ul>
    </Section>
  );
}

function Pipelines() {
  const {heading, body, integrations, secondary, secondaryLink} = content.pipelines;
  return (
    <Section id="pipelines" heading={heading}>
      <p>{body}</p>
      <ul className={styles.integrations}>
        {integrations.map((item) => (
          <li key={item.name}>
            <strong>{item.name}</strong>
            <span className={styles.muted}>
              {item.href ? <Link href={item.href}>{item.how}</Link> : item.how}
            </span>
            {item.todo ? <Todo>{item.todo}</Todo> : null}
          </li>
        ))}
      </ul>
      <p className={styles.muted}>
        {secondary} <Link to={secondaryLink.to}>{secondaryLink.label}</Link>.
      </p>
    </Section>
  );
}

function Modes() {
  const {heading, columns, rows, hook, cta, dataHandling, dataLink} = content.modes;
  return (
    <Section id="modes" heading={heading} tone="quiet">
      <table className={styles.table}>
        <thead>
          <tr>
            <th />
            <th>{columns[0]}</th>
            <th>{columns[1]}</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(([label, local, platform]) => (
            <tr key={label}>
              <th scope="row">{label}</th>
              <td>{local}</td>
              <td className={styles.muted}>{platform}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <p>{hook}</p>
      <p>
        <Link to={cta.to} onClick={track(EVENTS.platformInterest, {stage: 'modes'})}>
          {cta.label}
        </Link>
      </p>
      <p className={styles.muted}>
        {dataHandling} <Link to={dataLink.to}>{dataLink.label}</Link>.
      </p>

      <VisualSlot>
        Screenshot of the StackGuardian plan view with policy verdict, severity, source evidence and run
        snapshot. Caption it <em>Optional platform mode</em> and keep it visually separate from the
        OSS screenshots.
      </VisualSlot>
    </Section>
  );
}

function Community() {
  const {heading, points, actions} = content.community;
  return (
    <Section id="community" heading={heading}>
      <div className={styles.cards}>
        {points.map((point) => (
          <div key={point.title} className={styles.card}>
            <h3>{point.title}</h3>
            <p>{point.body}</p>
          </div>
        ))}
      </div>
      <ul className={styles.inlineLinks}>
        {actions.map((action) => (
          <li key={action.label}>
            <Link href={action.href}>{action.label}</Link>
          </li>
        ))}
      </ul>
    </Section>
  );
}

function FinalCta() {
  const {heading, body, micro} = content.final;
  const {primary, secondary} = content.hero;
  return (
    <Section id="start-now" heading={heading} tone="finale">
      <p>{body}</p>
      <div className={styles.actions}>
        <Action {...primary} primary onClick={track(EVENTS.heroStar, {source: 'footer'})} />
        <Action {...secondary} onClick={track(EVENTS.quickstart, {ci_system: 'unspecified'})} />
      </div>
      <p className={styles.muted}>{micro}</p>
      <p className={styles.muted}>
        Already got a verdict?{' '}
        <Link
          href={issueUrl({template: 'general-issue.md', title: 'First evaluated plan: '})}
          onClick={track(EVENTS.firstPlan, {ci_system: 'unspecified', mode: 'local'})}
        >
          Tell us how the first plan went
        </Link>
        .
      </p>
    </Section>
  );
}

/*
 * The doorways to the companion pages, placed where the brief asks for them:
 * Learn straight after the quick start, Playground straight after policy
 * authoring, Fleet immediately before the StackGuardian progression, and the
 * traction counters just before the final CTA.
 *
 * Each sits at the moment the reader has just acquired the question it
 * answers -- someone who has read two lines of YAML is exactly who wants a
 * ten-minute course, and someone who has just read a policy is exactly who
 * wants to watch one evaluate.
 */

function LearnDoorway() {
  return (
    <Doorway
      title="Prefer to learn by doing?"
      body="Work through a real plan, watch a policy fail on one specific resource, and read the verdict. No account or repository required."
      cta={{label: 'Start learning', to: '/learn'}}
      onClick={track(EVENTS.learnStart, {source: 'home'})}
    />
  );
}

function PlaygroundDoorway() {
  return (
    <Doorway
      title="See a policy evaluate"
      body="Pick a guardrail, read the plan it runs against, and see the exact verdict Tirith returns: the resource, the planned action and the value behind it."
      cta={{label: 'Open Playground', to: '/playground'}}
      onClick={track(EVENTS.playgroundOpen, {source: 'home'})}
    />
  );
}

function AiDoorway() {
  return (
    <Doorway
      title="Writing these with a coding agent?"
      body="An MCP server and skill files give your agent the real condition list, the real provider operations and a real verdict, so it stops inventing schema and starts running the policy."
      cta={{label: 'Set it up', to: '/ai'}}
      onClick={track(EVENTS.aiView, {source: 'home'})}
    />
  );
}

function FleetDoorway() {
  return (
    <Doorway
      subdued
      title="Growing beyond one repository?"
      body="When policies, approvals and evidence have to stay consistent across many pipelines, there is an optional commercial path. Tirith stays Apache-2.0 either way."
      cta={{label: 'Fleet governance', to: '/fleet'}}
      onClick={track(EVENTS.platformInterest, {stage: 'home-doorway'})}
    />
  );
}

/*
 * Counters rather than claims. Every figure is a placeholder for now: the
 * scheduled job that fetches them has not been built, and inventing numbers on
 * the way to a page about verifiability would undermine both.
 */
function TractionStrip() {
  const counters = [
    ['[X]', 'stars'],
    ['[Y]', 'forks'],
    ['[Z]', 'contributors'],
    ['[R]', 'releases'],
  ];
  return (
    <Section id="receipts" heading="What the public record shows">
      <dl className={styles.stats}>
        {counters.map(([value, label]) => (
          <div key={label}>
            <dt className={styles.statValue}>{value}</dt>
            <dd>{label}</dd>
          </div>
        ))}
      </dl>
      <p className={styles.muted}>
        Public GitHub activity, linked back to the evidence. Local Tirith runs send no telemetry, so
        these count attention and contribution rather than production use.{' '}
        <Link to="/traction" onClick={track(EVENTS.tractionView, {source: 'home'})}>
          See the receipts
        </Link>
        .
      </p>
      <Todo>
        These four counters are placeholders. They are fed by the same unbuilt snapshot job as the
        Traction page. Build it once and both surfaces become real.
      </Todo>
    </Section>
  );
}

export default function Home() {
  return (
    <PageShell
      title="Tirith IaC Governance"
      description="Open-source IaC governance for any Terraform or OpenTofu pipeline. Evaluate plans locally, explain failures and stop unsafe changes before apply."
    >
      <Hero />
      <QuickStart />
      <LearnDoorway />
      <Proof />
      <Problem />
      <Verdict />
      <Ladder />
      <Demo />
      <Scanner />
      <Policies />
      <PlaygroundDoorway />
      <AiDoorway />
      <Pipelines />
      <FleetDoorway />
      <Modes />
      <Community />
      <TractionStrip />
      <FinalCta />
    </PageShell>
  );
}

export {LAUNCH_BLOCKERS};
