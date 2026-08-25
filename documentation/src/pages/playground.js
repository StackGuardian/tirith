import {useState} from 'react';
import Link from '@docusaurus/Link';

import {EVENTS, capture, track, usePageView} from '../analytics';
import {
  Action,
  BUILDER_URL,
  DataTable,
  Hero,
  PageShell,
  Section,
  Todo,
  TrackedCode,
  Verdict,
  issueUrl,
  outcomeOf,
  styles,
} from '../components/site';
import fixtures from '../data/fixtures.json';

/*
 * ---------------------------------------------------------------------------
 * PLAYGROUND
 *
 * Job: let a developer experience Tirith's core contract -- plan plus policy
 * produces an explainable verdict -- before changing a repository or creating
 * an account.
 *
 * How real is this? Every verdict on this page is genuine output from the
 * Tirith engine, produced by documentation/scripts/generate-fixtures.py
 * running the real evaluator over the worked examples that ship with
 * `tirith ui`. Nothing here is mocked up.
 *
 * What it deliberately does not do is evaluate an edited policy. Tirith is
 * Python, so live evaluation means either shipping a Python runtime to every
 * visitor or standing up an endpoint that receives plans. The second option
 * contradicts the whole promise of the tool, and the first is a large amount
 * of machinery for a page whose job is comprehension. So the workbench is
 * honest about the boundary: pick a fixture, read the real verdict and the
 * real evidence, then take the exact command away and run it yourself.
 *
 * The copy says so plainly rather than implying an evaluation happened.
 * ---------------------------------------------------------------------------
 */

const EXAMPLES = fixtures.examples;

/*
 * The template gallery's collections, mapped onto the examples that actually
 * exist. The brief lists six collections; four of them have a real, tested
 * example behind them today and two do not, which is stated rather than
 * papered over with an invented policy.
 */
const COLLECTIONS = [
  ['Required metadata', 'Owner, cost centre and environment tags', 'Beginner', '01-required-tags'],
  ['Destructive change', 'Block deletes for protected resources', 'Beginner', '04-block-destroy'],
  ['Public exposure', 'Reject public storage or unrestricted ingress', 'Intermediate', '02-no-public-buckets'],
  ['Cost', 'Gate on the monthly total an Infracost breakdown reports', 'Intermediate', '03-cost-ceiling'],
  ['Workload health', 'Require Kubernetes liveness and readiness probes', 'Intermediate', '05-kubernetes-probes'],
];

const MISSING_COLLECTIONS = ['Encryption (require supported encryption attributes)', 'Location (restrict provider regions and accounts)'];

const content = {
  hero: {
    eyebrow: 'Policy workbench',
    title: 'What do you want to govern?',
    body:
      'Pick a guardrail, read the plan it runs against, and see the exact verdict Tirith returns: ' +
      'the rule, the resource, the planned action and the value behind the result. It needs no ' +
      'account, touches no repository, and uploads nothing.',
    trust: ['Real engine output', 'Public fixtures only', 'Nothing uploaded', 'No account'],
  },
  prompts: 'Describe a guardrail or start from a maintained template.',
};

function snippetFor(example) {
  return [
    '# Save the policy as .tirith/policies/' + example.key + '.json,',
    '# then evaluate the plan your pipeline already produces.',
    'tirith \\',
    '  -policy-path .tirith/policies \\',
    '  -input-path plan.json \\',
    '  --fail-on-error',
    '',
    '# exit ' + example.exitCode + ': ' + example.exitMeaning,
  ].join('\n');
}

function Workbench({example}) {
  const outcome = outcomeOf(example.result);
  return (
    <>
      <div className={styles.panes}>
        <div className={styles.pane}>
          <div className={styles.paneHead}>
            <span>Policy</span>
            <span className={styles.paneHint}>{example.result.meta?.required_provider}</span>
          </div>
          <div className={styles.paneBody}>
            <TrackedCode language="json" ciSystem="none">
              {JSON.stringify(example.policy, null, 2)}
            </TrackedCode>
          </div>
        </div>

        <div className={styles.pane}>
          <div className={styles.paneHead}>
            <span>Plan</span>
            <span className={styles.paneHint}>public fixture</span>
          </div>
          <div className={styles.paneBody}>
            <TrackedCode language="json" ciSystem="none">
              {JSON.stringify(example.input, null, 2)}
            </TrackedCode>
          </div>
        </div>
      </div>

      <Verdict example={example} />
    </>
  );
}

/**
 * The policy builder, embedded.
 *
 * It is a separate application on its own deployment, and framing somebody
 * else's app is a dependency rather than an integration: it will not follow
 * this site's theme, it is cramped on a phone, and if that deployment changes
 * or goes away this frame goes blank without telling anyone.
 *
 * So the frame is never the only route. The heading says what it is, a plain
 * link opens it standalone directly above the frame, and that link is what a
 * visitor on a narrow screen or a blocked iframe still has. Loaded lazily,
 * because most people come here to read a verdict, not to author a rule.
 */
function Builder() {
  return (
    <>
      <p>
        Authoring rather than evaluating: fill in a form and the builder assembles the JSON. It is a
        separate tool on its own deployment, shown here so you do not lose your place. You can{' '}
        <Link href={BUILDER_URL} onClick={track(EVENTS.builderOpen, {mode: 'standalone'})}>
          open it in its own tab
        </Link>{' '}
        if you would rather have the room, or if the frame below does not load.
      </p>

      <iframe
        src={BUILDER_URL}
        title="Tirith policy builder"
        loading="lazy"
        className={styles.embed}
      />

      <p className={styles.muted}>
        The builder writes a policy; it does not evaluate one. Bring what it gives you back to the
        Evaluate tab, or save it under <code>.tirith/policies</code> and run it against a real plan.
      </p>
    </>
  );
}

/**
 * The evaluate mode: choose a fixture, read the real verdict, take the command.
 *
 * Split out of the page body when the builder arrived, so the two modes are
 * two components rather than one function with a branch buried in its middle.
 */
function EvaluateMode({example, select, activeKey}) {
  return (
    <>
        <p>{content.prompts}</p>

        <ul className={styles.chips}>
          {EXAMPLES.map((item) => (
            <li key={item.key}>
              <button
                type="button"
                className={
                  item.key === activeKey ? `${styles.chip} ${styles.chipActive}` : styles.chip
                }
                aria-pressed={item.key === activeKey}
                onClick={() => select(item.key)}
              >
                {item.title}
              </button>
            </li>
          ))}
        </ul>

        <p className={styles.muted}>{example.summary}</p>

        <Workbench example={example} />

        {/*
          * Stated where a visitor would otherwise assume an evaluation just
          * ran. Being straight about this is cheaper than the credibility
          * cost of someone editing the policy, seeing nothing change, and
          * concluding the tool is broken.
          */}
        <p className={styles.muted}>
          These verdicts are produced by running the real Tirith engine over these fixtures at build
          time, not by evaluating in your browser, so the page can show you what Tirith
          returns without a plan of yours ever leaving your machine. To evaluate a policy you have
          edited, take the command below and run it locally.
        </p>

        <TrackedCode language="bash" ciSystem="cli">
          {snippetFor(example)}
        </TrackedCode>

        <ul className={styles.inlineLinks}>
          <li>
            <Link
              to="/docs/tirith-usage/ci-integration/"
              onClick={track(EVENTS.playgroundToRepo, {template_id: example.key})}
            >
              Use this in my repository
            </Link>
          </li>
          <li>
            <Link to="/learn" onClick={track(EVENTS.learnStart, {source: 'playground'})}>
              Open in Learn
            </Link>
          </li>
          <li>
            <Link to="/policies">Browse all policies</Link>
          </li>
          <li>
            <Link href={issueUrl({template: 'policy-request.md', title: 'Policy: improve '})}>
              Propose a template improvement
            </Link>
          </li>
        </ul>
    </>
  );
}

export default function Playground() {
  usePageView(EVENTS.playgroundOpen);
  const [activeKey, setActiveKey] = useState(EXAMPLES[0].key);
  const [mode, setMode] = useState('evaluate');
  const example = EXAMPLES.find((item) => item.key === activeKey) || EXAMPLES[0];

  const select = (key) => {
    setActiveKey(key);
    const chosen = EXAMPLES.find((item) => item.key === key);
    // Only the template id travels, never policy or plan content.
    capture(EVENTS.templateSelect, {template_id: key});
    capture(EVENTS.evaluationOutcome, {
      template_id: key,
      outcome: outcomeOf(chosen?.result).key,
    });
  };

  return (
    <PageShell
      title="Tirith Playground — Test Terraform and OpenTofu Policies"
      description="Run Tirith policies against safe Terraform/OpenTofu plan fixtures, inspect resource-level results and export a working policy to your pipeline."
    >
      {/*
        * Both hero actions land on the workbench directly below, and set the
        * mode on the way. The page's whole claim is that a plan plus a policy
        * produces an explainable verdict, so the primary action names the
        * thing worth seeing -- a failure -- rather than saying "get started".
        * Four of the five bundled examples fail, and the failing ones are the
        * ones that teach anything.
        */}
      <Hero
        {...content.hero}
        actions={[
          {
            label: 'See a failing verdict',
            href: '#workbench',
            primary: true,
            onClick: () => setMode('evaluate'),
          },
          {
            label: 'Build a policy from a form',
            href: '#workbench',
            onClick: () => {
              setMode('build');
              capture(EVENTS.builderOpen, {mode: 'embedded', source: 'hero'});
            },
          },
        ]}
      />

      <Section id="workbench" heading="Read a verdict, or write a rule">
        <ul className={styles.chips} role="tablist" aria-label="Playground mode">
          {[
            ['evaluate', 'Evaluate a policy'],
            ['build', 'Build a policy'],
          ].map(([key, label]) => (
            <li key={key}>
              <button
                type="button"
                role="tab"
                aria-selected={mode === key}
                className={mode === key ? `${styles.chip} ${styles.chipActive}` : styles.chip}
                onClick={() => {
                  setMode(key);
                  if (key === 'build') capture(EVENTS.builderOpen, {mode: 'embedded'});
                }}
              >
                {label}
              </button>
            </li>
          ))}
        </ul>

        {mode === 'build' ? <Builder /> : <EvaluateMode example={example} select={select} activeKey={activeKey} />}
      </Section>
      <Section id="outcomes" heading="Four outcomes, and why the difference matters">
        <p>
          Most tools have two states: green and red. Tirith has four, because “the check could not
          run” and “the check ran and said no” call for completely different responses: one pages
          the platform team, the other pages the change author.
        </p>
        <DataTable
          columns={['Outcome', 'Exit', 'What it means']}
          rows={[
            ['Passed', '0', 'Every check that ran passed. Inspect the resources evaluated before exporting the rule.'],
            ['Failed', '3', 'This change would be blocked. Open each result to see the planned action and value.'],
            [
              'Unevaluated',
              '1',
              'Tirith could not reach a policy answer. This is not a pass — review the provider input, match count and policy diagnostics.',
            ],
            [
              'Tool error',
              '1',
              'The evaluation did not complete. Your policy did not fail; fix the execution error and run it again.',
            ],
          ]}
        />
        <p className={styles.muted}>
          Both surfaces fail closed: anything that leaves the verdict unknown exits non-zero
          regardless of <code>--fail-on-error</code>.{' '}
          <Link to="/docs/tirith-usage/exit-codes/">The full exit-code contract</Link>.
        </p>
      </Section>

      <Section id="templates" heading="The rest of the guardrails">
        <p>
          Load any of these into the workbench above. All of them ship with Tirith and are covered
          by its test suite, so the verdict you read here is the verdict you get on your own
          machine.
        </p>
        <DataTable
          columns={['Collection', 'Example', 'Level', 'Open']}
          rows={COLLECTIONS.map(([name, example_, level, key]) => [
            name,
            example_,
            level,
            <button
              key={key}
              type="button"
              className={styles.chip}
              onClick={() => {
                select(key);
                if (typeof document !== 'undefined') {
                  document.getElementById('workbench')?.scrollIntoView({behavior: 'smooth'});
                }
              }}
            >
              Load
            </button>,
          ])}
        />
        <Todo>
          Two collections in the brief have no maintained example behind them yet:{' '}
          {MISSING_COLLECTIONS.join('; ')}. Add tested examples under{' '}
          <code>src/tirith/tui/examples/</code> and rerun{' '}
          <code>documentation/scripts/generate-fixtures.py</code>. They will appear here and in{' '}
          <code>tirith ui</code> at the same time. Template provenance (maintainer, last review,
          Tirith version, tested fixture count) is not yet recorded per example and needs a manifest
          before community policies are listed alongside maintained ones.
        </Todo>
      </Section>

      <Section id="privacy" heading="There is nothing here to upload" tone="quiet">
        <p>Nothing, and it is built so that there is nothing to do.</p>
        <ul>
          <li>
            <strong>No upload path exists.</strong> The verdicts are precomputed and served as
            static JSON. There is no evaluation endpoint, so there is nowhere for a plan to be sent
            even by accident.
          </li>
          <li>
            <strong>Analytics records template ids and outcomes only</strong>, never policy text,
            plan content, source or free-form input.
          </li>
          <li>
            <strong>No credentials, no Terraform.</strong> The page does not run Terraform or fetch
            provider credentials; it renders evaluations of supplied plan JSON.
          </li>
        </ul>
        <p className={styles.muted}>
          If live evaluation of your own plan is added later, it will say what it does before you
          give it anything, and running the CLI locally will remain the private option.
        </p>
      </Section>

      <Section id="next" heading="Take it to a real pipeline" tone="finale">
        <p>
          The policy above is a file. Commit it under <code>.tirith/policies</code>, add one step to
          the job you already run, and the same verdict shows up on your pull requests.
        </p>
        <div className={styles.actions}>
          <Action
            label="Govern your first pipeline"
            to="/docs/tirith-usage/ci-integration/"
            primary
            onClick={track(EVENTS.playgroundToRepo, {template_id: example.key})}
          />
          <Action label="Take the course" to="/learn" />
        </div>
      </Section>
    </PageShell>
  );
}
