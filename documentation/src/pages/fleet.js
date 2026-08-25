import {useState} from 'react';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';

import {EVENTS, capture, track, usePageView} from '../analytics';
import {
  Action,
  AssetGrid,
  DataTable,
  Hero,
  NEW_ISSUE,
  PageShell,
  issueUrl,
  REPO,
  Section,
  Todo,
  VisualSlot,
  styles,
} from '../components/site';

/*
 * ---------------------------------------------------------------------------
 * FLEET
 *
 * Job: explain the commercial progression when a team needs to discover,
 * standardise, approve and evidence Tirith governance across many IaC
 * repositories -- without making StackGuardian a condition of OSS use.
 *
 * Two rules shape everything below, and both come from the brief:
 *
 *   1. The first viewport must state that Tirith OSS is free, independent and
 *      needs no StackGuardian account. It does, in the hero body and again in
 *      the trust line.
 *
 *   2. The commercial CTA never outranks `Use Tirith OSS`. On this page --
 *      the one page where a commercial CTA is legitimately primary -- the OSS
 *      route still appears beside it every time, never buried.
 *
 * Capabilities are tagged available or planned. Direct execution initiated
 * from Tirith by calling the StackGuardian workflow API is planned, not
 * shipped, and is labelled as such rather than described in the present tense.
 * ---------------------------------------------------------------------------
 */

const STAGES = [
  ['Discover', 'Find Terraform and OpenTofu repositories and pipelines with read access; show coverage confidence and gaps.', 'available'],
  ['Prioritise', 'Rank which repositories need governance first by verified severity and exposure signals.', 'available'],
  ['Install', 'Open minimal Tirith pull requests for repository owners to review, and it does not write directly to protected branches.', 'available'],
  ['Standardise', 'Manage central policy and evaluate it continuously across GitHub Actions, GitLab CI and other pipelines.', 'available'],
  ['Approve', 'Add policy-aware approvals, credential brokering and private user-owned runners without rewriting the developer workflow.', 'available'],
  ['Remediate', 'Stage an explainable code change for human approval, with file and line evidence and an audit trail.', 'available'],
  ['Execute', 'Keep your current apply jobs, or move execution into StackGuardian for revisions, snapshots, recovery and notifications.', 'available'],
  ['Execute from Tirith', 'Tirith calling the StackGuardian workflow API directly to move from policy decision into controlled execution.', 'planned'],
];

const COMPARISON = [
  ['Evaluate a Terraform or OpenTofu plan', 'Included', 'Included'],
  ['Run with no account and no network', 'Included', 'Not applicable; connection is explicit'],
  ['Policies and results in each repository', 'Included', 'Included'],
  ['Discover IaC repositories and open rollout PRs', 'Manual', 'Included'],
  ['Central policy, history and plan visualisation', 'None', 'Included'],
  ['Approvals, credential brokering and audit', 'Use your existing CI tools', 'Included'],
  ['Assisted prioritisation and remediation', 'None', 'Included; verify entitlement'],
  ['Drift, snapshots, recovery and notifications', 'None', 'Where execution or state is connected'],
  ['Private user-owned runtime', 'Your own CI runner', 'Included'],
];

const FAQ = [
  [
    'Do I need StackGuardian to use Tirith?',
    'No. Local Tirith evaluation is Apache-2.0, runs wherever your pipeline runs, and requires no account and no network connection. That is a governance commitment rather than current behaviour. See GOVERNANCE.md.',
  ],
  [
    'What changes when I connect?',
    'You explicitly supply a StackGuardian organisation and token; there is no other switch. Tirith masks Terraform-sensitive values locally, then can send the masked plan, results, metadata and, unless you disable it with --no-source, the related source.',
  ],
  [
    'Can StackGuardian replace or control my repositories?',
    'Installation and remediation arrive as pull requests for repository owners to approve. It does not write directly to protected branches, and your existing CI and apply jobs can stay exactly as they are.',
  ],
  [
    'Can the runtime remain ours?',
    'Yes. A private runtime fully owned and operated by you is supported; its network and control-plane requirements are covered in the technical follow-up.',
  ],
  [
    'What stays open source?',
    'The policy schema, the providers, the CLI and local action contract, and the example policy library are all usable without any commercial relationship, subject to the published governance commitments.',
  ],
];

const REPO_BANDS = ['1–10', '11–50', '51–250', '250+'];
const CI_SYSTEMS = ['GitHub Actions', 'GitLab CI', 'Azure DevOps', 'Jenkins', 'Other'];
const PROBLEMS = ['Visibility', 'Policy consistency', 'Approvals', 'Remediation', 'Audit', 'Governed execution'];

/**
 * The enquiry form.
 *
 * Submits to HubSpot's forms API directly from the browser, which is what that
 * endpoint is designed for, so a static site needs no backend. The portal id
 * and form guid come from build-time configuration rather than being committed
 * here -- and when they are absent the form disables itself and says why,
 * instead of silently posting into the void.
 *
 * Analytics never sees free text. Only the enumerated fields -- repository
 * band and primary problem -- are captured; email, organisation and the
 * context box are not.
 */
function FleetForm() {
  const {siteConfig} = useDocusaurusContext();
  const {hubspotPortalId, hubspotFormGuid} = siteConfig.customFields || {};
  const configured = Boolean(hubspotPortalId && hubspotFormGuid);

  const [state, setState] = useState('idle');
  const [started, setStarted] = useState(false);

  const onFirstInput = () => {
    if (!started) {
      setStarted(true);
      capture(EVENTS.fleetFormStart);
    }
  };

  const onSubmit = async (event) => {
    event.preventDefault();
    if (!configured) return;

    const data = new FormData(event.target);
    const band = data.get('repository_band');
    const problem = data.get('primary_problem');
    const ci = data.getAll('ci_systems');

    // Enumerated values only. Never the email, organisation or context box.
    capture(EVENTS.fleetFormSubmit, {
      repo_count_band: band,
      primary_problem: problem,
      ci_systems: ci.join(','),
    });

    setState('sending');
    try {
      const response = await fetch(
        `https://api.hsforms.com/submissions/v3/integration/submit/${hubspotPortalId}/${hubspotFormGuid}`,
        {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({
            fields: [
              {objectTypeId: '0-1', name: 'email', value: data.get('email')},
              {objectTypeId: '0-1', name: 'company', value: data.get('company')},
              {objectTypeId: '0-1', name: 'repository_band', value: band},
              {objectTypeId: '0-1', name: 'ci_systems', value: ci.join('; ')},
              {objectTypeId: '0-1', name: 'primary_problem', value: problem},
              {objectTypeId: '0-1', name: 'context', value: data.get('context') || ''},
            ],
            context: {
              pageUri: typeof window !== 'undefined' ? window.location.href : '',
              pageName: 'Tirith Fleet governance',
            },
          }),
        },
      );
      setState(response.ok ? 'sent' : 'failed');
    } catch {
      setState('failed');
    }
  };

  if (state === 'sent') {
    return (
      <p>
        <strong>Thanks.</strong> While we review your setup, govern one repository locally with
        Tirith. <Link to="/docs/tirith-usage/ci-integration/">The quick start</Link> needs no
        account and takes about two lines.
      </p>
    );
  }

  return (
    <>
      {configured ? null : (
        <Todo>
          The HubSpot portal ID and form GUID are not configured, so this form is disabled. Set{' '}
          <code>HUBSPOT_PORTAL_ID</code> and <code>HUBSPOT_FORM_GUID</code> in the docs deploy
          workflow, and create the matching HubSpot properties:{' '}
          <code>email</code>, <code>company</code>, <code>repository_band</code>,{' '}
          <code>ci_systems</code>, <code>primary_problem</code>, <code>context</code>. Until then,
          the GitHub issue route below is the working path.
        </Todo>
      )}

      <form className={styles.form} onSubmit={onSubmit} onChange={onFirstInput}>
        <div className={styles.field}>
          <label htmlFor="email">Work email</label>
          <input id="email" name="email" type="email" required disabled={!configured} />
        </div>

        <div className={styles.field}>
          <label htmlFor="company">Organisation</label>
          <input id="company" name="company" type="text" required disabled={!configured} />
        </div>

        <div className={styles.field}>
          <label htmlFor="repository_band">Approximate number of IaC repositories</label>
          <select id="repository_band" name="repository_band" disabled={!configured}>
            {REPO_BANDS.map((band) => (
              <option key={band} value={band}>
                {band}
              </option>
            ))}
          </select>
        </div>

        <fieldset className={styles.field}>
          {/* A real <legend>: `as` is not a prop React forwards, so the
              previous markup rendered a <label> with no control, leaving the
              checkbox group unlabelled for screen readers. */}
          <legend>CI systems</legend>
          <div className={styles.checkboxRow}>
            {CI_SYSTEMS.map((system) => (
              <label key={system}>
                <input type="checkbox" name="ci_systems" value={system} disabled={!configured} />
                {system}
              </label>
            ))}
          </div>
        </fieldset>

        <div className={styles.field}>
          <label htmlFor="primary_problem">Primary problem</label>
          <select id="primary_problem" name="primary_problem" disabled={!configured}>
            {PROBLEMS.map((problem) => (
              <option key={problem} value={problem}>
                {problem}
              </option>
            ))}
          </select>
        </div>

        <div className={styles.field}>
          <label htmlFor="context">Anything else (optional)</label>
          <textarea id="context" name="context" rows={4} disabled={!configured} />
          <small>
            Please do not paste source code, plan files, tokens or credentials. A sentence about how
            Terraform reaches production today is more useful than any of them.
          </small>
        </div>

        <div>
          <button
            type="submit"
            className={`button button--primary ${styles.heroPrimary}`}
            disabled={!configured || state === 'sending'}
          >
            {state === 'sending' ? 'Sending…' : 'Discuss fleet governance'}
          </button>
        </div>

        {state === 'failed' ? (
          <p className={styles.formNote}>
            That did not send. Please{' '}
            <Link href={NEW_ISSUE}>open an issue</Link> or email the maintainers instead.
          </p>
        ) : null}

        <p className={styles.formNote}>
          Submitting shares these details with StackGuardian so they can reply. Nothing you type
          here reaches the project&apos;s analytics.
        </p>
      </form>
    </>
  );
}

export default function Fleet() {
  usePageView(EVENTS.fleetView);

  return (
    <PageShell
      title="Tirith OSS and StackGuardian Fleet Governance"
      description="Use Tirith locally for free, or connect StackGuardian to discover IaC repositories, open approved installation PRs and govern plans across your cloud estate."
    >
      <Hero
        eyebrow="From one repository to a governed fleet"
        title="Keep Tirith local. Add fleet governance when coordination becomes the hard part."
        body="Tirith is Apache-2.0 and fully usable without StackGuardian: no account, no network, no commercial relationship, and that is a published governance commitment rather than a current convenience. When policies, approvals and evidence have to stay consistent across many repositories, StackGuardian can discover your IaC pipelines, prioritise rollout and open Tirith installation pull requests for your team to approve."
        trust={['No forced migration', 'Keep your existing CI', 'Approve every installation PR', 'Private runtime available']}
        actions={[
          {label: 'Discuss fleet governance', href: '#contact', primary: true, onClick: track(EVENTS.offerCta, {offer: 'fleet'})},
          {label: 'Use Tirith OSS', to: '/docs/tirith-usage/ci-integration/', onClick: track(EVENTS.fleetToOss, {source: 'hero'})},
        ]}
      />

      <Section id="when" heading="Which one is your problem?">
        <p>
          Most teams should stay local. This page is only worth reading if the second row describes
          you.
        </p>
        <DataTable
          columns={['Choice', 'Use it when']}
          rows={[
            [
              'Keep Tirith local',
              'One or a few repositories; policies owned by the repository; your existing CI and review process are enough; no central history needed.',
            ],
            [
              'Connect StackGuardian',
              'Many repositories; policy drifting apart between them; installing the same gate by hand over and over; central approvals and evidence; credential and runtime controls; remediation across teams.',
            ],
          ]}
        />
      </Section>

      <Section id="offer" heading="What each one costs" tone="quiet">
        <DataTable
          columns={['', 'Price', 'Best for', 'What you get']}
          rows={[
            [
              'Tirith OSS',
              '£0 · Apache-2.0',
              'A developer or team governing repositories independently',
              'Local plan evaluation, policies in your repository, actionable verdicts, a CI gate and community support',
            ],
            [
              'StackGuardian Fleet',
              'Custom',
              'Platform organisations coordinating many IaC projects',
              'Discovery and rollout, central policies, plan visibility, approvals, audit, remediation and governed execution',
            ],
          ]}
        />
        <div className={styles.actions}>
          <Action
            label="Govern your first pipeline"
            to="/docs/tirith-usage/ci-integration/"
            primary
            onClick={track(EVENTS.fleetToOss, {source: 'offer'})}
          />
          <Action
            label="Discuss fleet governance"
            href="#contact"
            onClick={track(EVENTS.offerCta, {offer: 'fleet'})}
          />
        </div>
        <p className={styles.muted}>
          The £0 offer is permanent. StackGuardian pricing is <em>Custom</em> on purpose: there
          are no invented Free/Pro/Enterprise tiers here, and there will not be until commercial
          packaging is settled.
        </p>
      </Section>

      <Section id="capabilities" heading="What connecting adds">
        <ol className={styles.ladder}>
          {STAGES.map(([stage, outcome, status]) => (
            <li key={stage}>
              <span className={styles.ladderStage}>
                {stage}
                {status === 'planned' ? <span className={styles.optionalTag}>planned</span> : null}
              </span>
              <span>{outcome}</span>
            </li>
          ))}
        </ol>
        <p className={styles.muted}>
          One boundary stated plainly: moving execution into existing StackGuardian workflows is
          available today. Tirith itself calling the workflow API to initiate execution is planned
          and not shipped, so do not build a rollout plan around it yet.
        </p>
      </Section>

      <Section id="views" heading="What the platform looks like" tone="quiet">
        <p>
          Four views cover most of what a platform team does here: find the repositories, watch the
          runs, manage the policy, and read a single plan in detail. They are screenshots of a
          separate, commercial product, shown as a set and kept visually apart from the
          open-source screenshots elsewhere on this site, so the boundary stays obvious.
        </p>

        <AssetGrid>
          <VisualSlot label="Overview">
            Fleet overview. Terraform and OpenTofu repositories discovered across the
            organisation, each with its governance state: gated, gap, or not yet evaluated. Show
            coverage confidence and the gaps ranked, because the honest version of this screen has
            unknowns on it.
          </VisualSlot>

          <VisualSlot label="Workflows">
            Workflows. The run list: which pipeline, which repository, the policy verdict, who
            approved and when. Include at least one errored run alongside the passes and failures,
            so the screenshot shows the three-state result rather than a tidy green column.
          </VisualSlot>

          <VisualSlot label="Policies">
            Central policies. The policy sets an organisation enforces, their severity, and which
            repositories each one currently applies to. Show one policy in both states: enforced
            somewhere, not yet rolled out elsewhere.
          </VisualSlot>

          <VisualSlot label="Plan detail">
            Plan detail. A single evaluated plan: the verdict, severity, the resource and value
            evidence behind it, and the run snapshot. This is the view that has to match the OSS
            pull-request comment, because the claim is that it is the same verdict.
          </VisualSlot>
        </AssetGrid>

        <Todo>
          All four are unshot. Capture them from a demo organisation, never a customer&apos;s: these
          screens carry repository names, cloud resource identifiers and run history. Redact
          anything that survives the demo data, caption each one{' '}
          <em>Optional platform mode</em>, and get the same approval the proof-strip logos need
          before publishing.
        </Todo>
      </Section>

      <Section id="comparison" heading="What you already have, and what you would gain">
        <DataTable columns={['Capability', 'Tirith OSS', 'StackGuardian Fleet']} rows={COMPARISON} />
      </Section>

      <Section id="faq" heading="Five questions worth asking first">
        {FAQ.map(([question, answer]) => (
          <details key={question} className={styles.details}>
            <summary>{question}</summary>
            <p>{answer}</p>
          </details>
        ))}
        <p className={styles.muted}>
          The complete masking behaviour, including what it does not catch, is in{' '}
          <Link to="/docs/tirith-usage/platform-check/">the platform-check documentation</Link>. The
          commitments are in <Link href={`${REPO}/blob/main/GOVERNANCE.md`}>GOVERNANCE.md</Link>.
        </p>
      </Section>

      <Section id="contact" heading="Tell us how Terraform reaches production today">
        <p>
          Whatever it looks like now, we will map the shortest route from the pipelines you already
          run to consistent governance across all of them, with no execution migration, and your apply
          jobs stay where they are.
        </p>
        <FleetForm />
        <p className={styles.muted}>
          Would rather keep it public?{' '}
          <Link href={issueUrl({template: 'general-issue.md', title: 'Governing many repositories: '})}>
            Open an issue
          </Link>{' '}
          instead. For anything that is not commercially sensitive, that gets you the maintainers
          rather than a sales process.
        </p>
      </Section>
    </PageShell>
  );
}
