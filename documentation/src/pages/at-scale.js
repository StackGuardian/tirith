import {useState} from 'react';
import Head from '@docusaurus/Head';
import Link from '@docusaurus/Link';
import useBaseUrl from '@docusaurus/useBaseUrl';
import Layout from '@theme/Layout';
import Heading from '@theme/Heading';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';

import {EVENTS, capture, track, usePageView} from '../analytics';
import TirithMark from '../components/brand/TirithMark';
import Colophon from '../components/site/Colophon';
import styles from './at-scale.module.css';
import '../css/chrome.module.css';

/*
 * ---------------------------------------------------------------------------
 * AT SCALE — the commercial page
 *
 * Was `fleet.js` on the previous site, rewritten into this one's visual world.
 *
 * Named "at scale" rather than "fleet". Fleet was borrowed vocabulary: it appeared nowhere
 * in the CLI, which calls this `tirith platform check`, and nowhere in the documentation,
 * which says "platform mode" and "your organization's policies". It also named the thing
 * you own rather than the problem you have, and "StackGuardian Fleet" read as a pricing
 * tier, which cuts against this page's own rule that OSS is not a lesser one.
 * The argument, the tables and the form carry over from that page; the chrome does not.
 *
 * Job: explain the commercial progression when a team needs to discover, standardise,
 * approve and evidence Tirith governance across many IaC repositories -- without making
 * StackGuardian a condition of OSS use.
 *
 * Two rules shape everything below, both from the brief, and both survive the port:
 *
 *   1. The first viewport must establish that Tirith OSS is free and stays that way. It
 *      does, once, in the hero lede. Once is the point: this used to be asserted in the
 *      lede, again in the comparison table and again in the FAQ, and a promise repeated
 *      three times reads as a promise the reader is expected to doubt.
 *
 *   2. The commercial CTA never outranks `Use Tirith OSS`. On this page -- the one page
 *      where a commercial CTA is legitimately primary -- the OSS route still appears
 *      beside it every time, never buried.
 *
 * Capabilities are tagged available or planned. Direct execution initiated from Tirith by
 * calling the StackGuardian workflow API is planned, not shipped, and is labelled as such
 * rather than described in the present tense.
 *
 * A NOTE ON WHAT COULD NOT BE VERIFIED: unlike the AI page, whose every claim maps to a
 * file or a command in this repository, the capability and comparison tables describe a
 * separate commercial product. They are reproduced from the source page unchanged. If any
 * of them has gone stale, it went stale there first.
 * ---------------------------------------------------------------------------
 */

const REPO = 'https://github.com/StackGuardian/tirith';
const NEW_ISSUE = `${REPO}/issues/new/choose`;

function issueUrl({template = 'general-issue.md', title} = {}) {
  const params = new URLSearchParams({template});
  if (title) params.set('title', title);
  return `${REPO}/issues/new?${params.toString()}`;
}

const hero = {
  eyebrow: 'Scale IaC governance across your organisation',
  title: 'Keep Tirith local.',
  // A condition, not a counter-instruction. The previous line pair read "keep it local /
  // run in platform mode", which told the reader to do two opposite things and left them
  // to work out which one they were. Local stays the default; this names the trigger.
  dim: 'Run in platform mode when governing IaC at scale.',
  /*
   * The why, not a feature list. The previous lede described what StackGuardian does --
   * discover, prioritise, open PRs -- which reads as a capability inventory and leaves the
   * reader to work out why any of it matters. What matters is the shape of the problem: a
   * gate answers one question about one change, and none of the questions that appear at
   * fifty repositories are answerable from inside a single run.
   *
   * Every clause maps to a row tagged `available` in STAGES below -- continuous evaluation
   * to Standardise, ranked exposure to Prioritise, the staged fix to Remediate -- so the
   * argument and the table cannot drift apart.
   *
   * Deliberately NOT "auto remediation". The Remediate row says "stage an explainable code
   * change for human approval", which is a different and better thing to sell to someone
   * who owns the pipeline: nothing edits their infrastructure code unattended. Calling it
   * automatic would also contradict the page's own table two screens further down.
   *
   * The Apache-2.0 sentence moved out because the headline directly above already says
   * "Keep Tirith local". The concession is made there, which frees the lede to argue.
   *
   * No em dashes, here or anywhere a reader sees. See documentation/scripts/find-dashes.py.
   */
  lede:
    'The CLI answers one question, once: is this change allowed? At fifty repositories the ' +
    'questions that matter cannot be answered from inside a single run. StackGuardian ' +
    'evaluates policy continuously, ranks what is genuinely exposed rather than what merely ' +
    'failed, and stages each fix as a reviewable pull request with its evidence attached.',
  /*
   * Four capabilities, one promise each, and nothing else in the line. This was a list of
   * reassurances answering "what do I give up?", which is a real objection but a defensive
   * opening: it argued from what the reader keeps rather than what they get. Those four
   * points are not lost, they are in the STAGES table and the FAQ below, which is where an
   * objection belongs.
   *
   * Each maps to a row tagged `available` in STAGES: the cloud scan to Detect, the shared
   * policy set to Standardise, the ranking to Prioritise, the pull requests to Remediate
   * and Install. Nothing planned appears here.
   *
   * They render uppercase in a mono face at 0.72rem, so a promise has to survive being
   * four or five words long. Any that needs a clause belongs in a section, not here.
   */
  facts: [
    'Cloud scan writes the policy',
    'One policy set, every repo',
    'Ranked by real exposure',
    'Fixes arrive as pull requests',
  ],
};

const WHEN = [
  [
    'Keep Tirith local',
    'One or a few repositories; policies owned by the repository; your existing CI and review process are enough; no central history needed.',
  ],
  [
    'Connect StackGuardian',
    'Many repositories; policy drifting apart between them; installing the same gate by hand over and over; central approvals and evidence; credential and runtime controls; remediation across teams.',
  ],
];

const OFFER = [
  {
    name: 'Tirith OSS',
    price: '£0 · Apache-2.0',
    best: 'A developer or team governing repositories independently',
    gets:
      'Local plan evaluation, policies in your repository, actionable verdicts, a CI gate and community support',
  },
  {
    name: 'StackGuardian',
    price: 'Custom',
    best: 'Platform organisations coordinating many IaC projects',
    gets:
      'Discovery and rollout, central policies, plan visibility, approvals, audit, remediation and governed execution',
  },
];

const STAGES = [
  ['Discover', 'Find Terraform and OpenTofu repositories and pipelines with read access; show coverage confidence and gaps.', 'available'],
  ['Detect', 'Scan connected cloud accounts on a schedule against CIS, PCI DSS, NIST and HIPAA, and turn each finding into a Tirith policy the pipeline then enforces.', 'available'],
  ['Prioritise', 'Rank which repositories need governance first by verified severity and exposure signals.', 'available'],
  ['Install', 'Open minimal Tirith pull requests for repository owners to review, and it does not write directly to protected branches.', 'available'],
  ['Standardise', 'Manage central policy and evaluate it continuously across GitHub Actions, GitLab CI and other pipelines.', 'available'],
  ['Approve', 'Add policy-aware approvals, credential brokering and private user-owned runners without rewriting the developer workflow.', 'available'],
  ['Remediate', 'Stage an explainable code change for human approval, with file and line evidence and an audit trail.', 'available'],
  ['Execute', 'Keep your current apply jobs, or move execution into StackGuardian for revisions, snapshots, recovery and notifications.', 'available'],
  ['Execute from Tirith', 'Tirith calling the StackGuardian workflow API directly to move from policy decision into controlled execution.', 'planned'],
];

/*
 * Each entry is [label, brief, asset]. `asset` null keeps the pending well, which is a
 * reserved space at the right aspect ratio rather than a gap, so the page does not reflow
 * when the image lands and the amount of missing material stays visible to a reviewer.
 *
 * The three assets are StackGuardian's own product screenshots, taken from
 * stackguardian.io. Every brief below describes what is actually in its image. The briefs
 * used to be a shooting spec for screenshots nobody had taken yet, and dropping a
 * different image under an unchanged spec would have made the page describe something the
 * reader cannot see.
 *
 * They carry verdicts in colour, which the open-source pages deliberately never do. That
 * is the boundary this section already claims to draw rather than a slip: these are a
 * separate commercial product and they should not look like the rest of the site.
 */
/*
 * The loop, and the strongest single reason to connect anything.
 *
 * It also resolves the boundary this page has to keep. Tirith reads documents, never a
 * cloud API: the translation corpus measured live-cloud rules at 0 of 1,372, and a
 * collector is still an open question. So detection cannot be the gate's job and is not
 * claimed as one. The platform finds what is already wrong; the policy it writes is an
 * ordinary Tirith policy, evaluated by the same open-source CLI, in the reader's own
 * pipeline. Neither half pretends to be the other.
 *
 * Written in the present tense because all of it ships. The one planned thing on this page
 * stays tagged as planned in STAGES above.
 */
const loop = {
  steps: [
    {
      n: '1',
      k: 'It scans what you already run',
      v:
        'Connected cloud accounts are checked on a schedule against CIS, PCI DSS, NIST ' +
        '800-53 and HIPAA. The result is a count of real resources failing real controls, ' +
        'not a list of things that might one day be wrong.',
    },
    {
      n: '2',
      k: 'Each finding becomes a policy',
      v:
        'A misconfiguration you already have is the best possible specification for a rule: ' +
        'somebody built it that way once, so somebody will build it that way again. The ' +
        'platform writes it as an ordinary Tirith policy.',
      product: true,
    },
    {
      n: '3',
      k: 'The gate stops it coming back',
      v:
        'That policy runs in your pipeline, on your runner, through the same open-source ' +
        'CLI as everything else on this site. The next plan that would reintroduce the ' +
        'misconfiguration does not reach apply.',
    },
  ],
  cta: {
    label: 'Scan your cloud now',
    href: 'https://app.stackguardian.io/',
  },
};

const VIEWS = [
  [
    'Policy enforcement',
    'Every evaluation across the estate, rolled up: 939 passed, 98 failed, 391 warned. The row underneath is one run, and it counts skipped checks separately from passed ones, which is the same four-outcome result the CLI returns.',
    {
      src: 'img/platform/policy-enforcement.png',
      alt: 'A policy enforcement summary: 1.4k total evaluations, 939 pass, 98 fail, 391 warn, and a single run reporting pass, failed, warning and skipped counts separately.',
    },
  ],
  [
    'Workflows',
    'The run list across an organisation, grouped by team and environment. Status is mixed on purpose: applied, planning, applying, pending, and one waiting on an approval. Policy Sets sits in the sidebar beside deployments, because the gate is part of the pipeline rather than a report about it.',
    {
      src: 'img/platform/workflows.webp',
      alt: 'A list of infrastructure workflows and workflow groups with mixed statuses including applied, pending, planning, applying and approval required.',
    },
  ],
  [
    'Benchmarks',
    'Policy sets an organisation can enforce as a pack: CIS, PCI DSS, NIST 800-53, HIPAA, GDPR, cost. Each reports fails, passes, info, skips and errors as separate tabs, and says when it last ran, which is what continuous evaluation looks like from the outside.',
    {
      src: 'img/platform/benchmarks.webp',
      alt: 'A best-practice check panel listing CIS, CISA, GDPR, HIPAA, NIST and PCI DSS benchmarks, with fail, pass, info and skip counts and a generated timestamp.',
    },
  ],
  [
    'Plan detail',
    'A single evaluated plan: the verdict, the severity, the resource and value evidence behind it, and the run snapshot. Still to come, and deliberately not substituted with something adjacent. This is the view that has to match the pull-request comment the open-source CLI already posts, because the claim is that it is the same verdict.',
    null,
  ],
];

const COMPARISON = [
  ['Evaluate a Terraform or OpenTofu plan', 'Included', 'Included'],
  ['Runs entirely on your own machine', 'Included', 'Not applicable; connection is explicit'],
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
    'No. Local evaluation is Apache-2.0 and runs wherever your pipeline runs. The commitment that it stays that way is in GOVERNANCE.md.',
  ],
  [
    'What changes when I connect?',
    'You explicitly supply a StackGuardian organisation and token; there is no other switch. Tirith masks values marked sensitive in the plan locally, then can send the masked plan, results, metadata and, unless you disable it with --no-source, the related source.',
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

/* --------------------------------------------------------------------------- */

function SectionHead({num, title, lede}) {
  return (
    <div className={styles.sectionHead}>
      <div className={styles.sectionLabel}>
        <span className={styles.sectionNum}>{num}</span>
        <Heading as="h2" className={styles.sectionTitle}>
          {title}
        </Heading>
      </div>
      {lede ? <p className={styles.sectionLede}>{lede}</p> : null}
    </div>
  );
}

/**
 * The enquiry form.
 *
 * Submits to HubSpot's forms API directly from the browser, which is what that endpoint
 * is designed for, so a static site needs no backend. The portal id and form guid come
 * from build-time configuration rather than being committed here -- and when they are
 * absent the form disables itself and says why, instead of silently posting into the void.
 *
 * Analytics never sees free text. Only the enumerated fields -- repository band, CI
 * systems and primary problem -- are captured; email, organisation and the context box
 * are not, and must not be.
 */
function EnquiryForm() {
  const {siteConfig} = useDocusaurusContext();
  const {hubspotPortalId, hubspotFormGuid} = siteConfig.customFields || {};
  const configured = Boolean(hubspotPortalId && hubspotFormGuid);

  const [state, setState] = useState('idle');
  const [started, setStarted] = useState(false);

  const onFirstInput = () => {
    if (!started) {
      setStarted(true);
      capture(EVENTS.scaleFormStart);
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
    capture(EVENTS.scaleFormSubmit, {
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
              pageName: 'Tirith at scale',
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
      <p className={styles.prose}>
        <strong>Thanks.</strong> While we review your setup, govern one repository locally
        with Tirith. <Link to="/docs/tirith-usage/ci-integration/">The quick start</Link>{' '}
        takes about two lines.
      </p>
    );
  }

  return (
    <>
      {configured ? null : (
        <p className={styles.notice} role="note">
          <span className={styles.noticeTag}>Form disabled</span>
          This build has no HubSpot form configured, so nothing here would send. Set{' '}
          <code>HUBSPOT_PORTAL_ID</code> and <code>HUBSPOT_FORM_GUID</code> at build time,
          with matching HubSpot properties for <code>email</code>, <code>company</code>,{' '}
          <code>repository_band</code>, <code>ci_systems</code>,{' '}
          <code>primary_problem</code> and <code>context</code>. Until then the issue link
          below is the working route.
        </p>
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

        {/* A real <legend>, so the checkbox group is labelled for a screen reader. */}
        <fieldset className={styles.field}>
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
            Please do not paste source code, plan files, tokens or credentials. A sentence
            about how your IaC reaches production today is more useful than any of them.
          </small>
        </div>

        <div>
          <button
            type="submit"
            className={styles.btnPrimary}
            disabled={!configured || state === 'sending'}>
            {state === 'sending' ? 'Sending…' : 'Discuss rolling this out'}
          </button>
        </div>

        {state === 'failed' ? (
          <p className={styles.formNote}>
            That did not send. Please <Link href={NEW_ISSUE}>open an issue</Link> or email
            the maintainers instead.
          </p>
        ) : null}

        <p className={styles.formNote}>
          Submitting shares these details with StackGuardian so they can reply. Nothing you
          type here reaches the project&apos;s analytics.
        </p>
      </form>
    </>
  );
}

export default function AtScale() {
  usePageView(EVENTS.scaleView);
  /*
   * Resolved once here rather than per item. useBaseUrl is a hook, and the call site below
   * sits inside a conditional inside a map, where a hook must not go. The site is served
   * under /tirith/, so a bare `img/...` src resolves against the current route and 404s on
   * every page that is not the root.
   */
  const base = useBaseUrl('/');

  return (
    <Layout
      title="Tirith at scale — many repositories, one policy set"
      description={
        'Use Tirith locally for free, or connect StackGuardian to discover IaC ' +
        'repositories, open approved installation PRs and govern plans across your cloud estate.'
      }>
      {/*
       * FAQPage structured data, generated from the FAQ array below rather than written out
       * again. Two reasons it is worth having on this page specifically: the questions are
       * the ones people actually put to a search engine or an assistant ("do I need
       * StackGuardian to use Tirith?"), and a hand-copied second version of an answer is a
       * fact that can drift out of agreement with the page it describes.
       *
       * Only this page gets it. Google's guidance is that FAQPage markup describes a real
       * FAQ that is visible on the page, and inventing one elsewhere risks the rich result
       * for the whole site.
       */}
      <Head>
        <script type="application/ld+json">
          {JSON.stringify({
            '@context': 'https://schema.org',
            '@type': 'FAQPage',
            '@id': 'https://stackguardian.github.io/tirith/at-scale/#faq',
            mainEntity: FAQ.map(([question, answer]) => ({
              '@type': 'Question',
              name: question,
              acceptedAnswer: {'@type': 'Answer', text: answer},
            })),
          })}
        </script>
      </Head>
      <main className={styles.page}>
        {/* ================= HERO ================= */}
        <header className={styles.hero}>
          <div className={styles.letterhead}>
            <TirithMark className={styles.letterheadMark} size={40} />
            <span className={styles.letterheadName}>Tirith</span>
            <span className={styles.letterheadRule} aria-hidden="true" />
            <span className={styles.letterheadNote}>{hero.eyebrow}</span>
          </div>

          <Heading as="h1" className={styles.h1}>
            {hero.title}
            <span className={styles.h1Dim}>{hero.dim}</span>
          </Heading>

          <div className={styles.heroPlate}>
            <div className={styles.heroLede}>
              <p className={styles.lede}>{hero.lede}</p>
              <div className={styles.heroLinks}>
                <a
                  className={styles.btnPrimary}
                  href="#contact"
                  onClick={track(EVENTS.offerCta, {offer: 'at-scale'})}>
                  Discuss rolling this out <span aria-hidden="true">→</span>
                </a>
                <Link
                  className={styles.btnGhost}
                  to="/docs/tirith-usage/ci-integration/"
                  onClick={track(EVENTS.scaleToOss, {source: 'hero'})}>
                  Use Tirith OSS <span aria-hidden="true">→</span>
                </Link>
              </div>
            </div>
            <div className={styles.heroAside}>
              {/*
               * The label names where these happen, which is the boundary this page has to
               * keep visible: every line below is something the platform does, none of it
               * is something the open-source CLI stops doing without it.
               */}
              <span className={styles.fieldLabel}>On the platform</span>
              <ul className={styles.facts}>
                {hero.facts.map((f) => (
                  <li key={f}>{f}</li>
                ))}
              </ul>
            </div>
          </div>
        </header>

        {/* ================= 01 WHEN ================= */}
        <section className={styles.section} id="when">
          <SectionHead
            num="01"
            title="Which one is your problem?"
            lede="Most teams should stay local. This page is only worth reading if the second row describes you."
          />
          <dl className={styles.defs}>
            {WHEN.map(([k, v]) => (
              <div className={styles.def} key={k}>
                <dt>{k}</dt>
                <dd>{v}</dd>
              </div>
            ))}
          </dl>
        </section>

        {/* ================= 02 OFFER ================= */}
        <section className={styles.section} id="offer">
          <SectionHead num="02" title="What each one costs" />
          <ul className={styles.offers}>
            {OFFER.map((o) => (
              <li key={o.name}>
                <span className={styles.offerName}>{o.name}</span>
                <span className={styles.offerPrice}>{o.price}</span>
                <span className={styles.offerBest}>{o.best}</span>
                <span className={styles.offerGets}>{o.gets}</span>
              </li>
            ))}
          </ul>
          <div className={styles.actions}>
            <Link
              className={styles.btnPrimary}
              to="/docs/tirith-usage/ci-integration/"
              onClick={track(EVENTS.scaleToOss, {source: 'offer'})}>
              Govern your first pipeline <span aria-hidden="true">→</span>
            </Link>
            <a
              className={styles.btnGhost}
              href="#contact"
              onClick={track(EVENTS.offerCta, {offer: 'at-scale'})}>
              Discuss rolling this out <span aria-hidden="true">→</span>
            </a>
          </div>
          <p className={styles.caveat}>
            Both routes are demonstrated end to end in the public demo repositories — on{' '}
            <Link href="https://github.com/StackGuardian/tirith-action-demo">GitHub</Link>,{' '}
            <Link href="https://gitlab.com/stackguardian/tirith-component-demo">GitLab</Link>{' '}
            and{' '}
            <Link href="https://bitbucket.org/__refeed__/tirith-bitbucket-demo">Bitbucket</Link>.
            Each starts with policies committed to the repository and then switches to the
            organization's, with nothing else in the pipeline changing.
          </p>
        </section>

        {/* ================= 03 CAPABILITIES ================= */}
        <section className={styles.section} id="capabilities">
          <SectionHead num="03" title="What connecting adds" />
          <ol className={styles.ladder}>
            {STAGES.map(([stage, outcome, status]) => (
              <li key={stage} data-planned={status === 'planned' ? 'true' : undefined}>
                <span className={styles.ladderStage}>
                  {stage}
                  {status === 'planned' ? (
                    <span className={styles.plannedTag}>planned</span>
                  ) : null}
                </span>
                <span className={styles.ladderOutcome}>{outcome}</span>
              </li>
            ))}
          </ol>
          <p className={styles.caveat}>
            One boundary stated plainly: moving execution into existing StackGuardian
            workflows is available today. Tirith itself calling the workflow API to initiate
            execution is planned and not shipped, so do not build a rollout plan around it
            yet.
          </p>
        </section>

        {/* ================= 04 VIEWS ================= */}
        {/* ================= 04 THE LOOP ================= */}
        <section className={styles.section} id="loop">
          <SectionHead
            num="04"
            title="Find it once, then stop it recurring"
            lede="The strongest reason to connect anything. What is already misconfigured in your cloud is the specification for the rule that keeps it from being rebuilt, and the two halves stay where they belong: the platform finds it, the open-source gate prevents it."
          />

          <ol className={styles.loop}>
            {loop.steps.map((step) => (
              <li key={step.n} data-product={step.product ? 'true' : undefined}>
                <span className={styles.loopNum}>{step.n}</span>
                <span className={styles.loopBody}>
                  <span className={styles.loopTitle}>{step.k}</span>
                  <span className={styles.loopText}>{step.v}</span>
                </span>
              </li>
            ))}
          </ol>

          {/*
           * Ghost, not primary. The enquiry form further down is this page's primary
           * conversion, and a self-serve button styled as the loudest thing in the section
           * would quietly demote it.
           */}
          <div className={styles.loopCta}>
            <Link className={styles.btnGhost} href={loop.cta.href}>
              {loop.cta.label} <span aria-hidden="true">→</span>
            </Link>
            <span className={styles.loopCtaNote}>
              Free to start, no card. Or use the form below if you would rather talk first.
            </span>
          </div>
        </section>

        {/*
         * ================= VIEWS: HIDDEN =================
         *
         * NOTE ON RESTORING: two things to settle first.
         *
         * It still carries num="04", which the section above now uses, so give it a free
         * number. And its three screenshots were judged stale and poor quality and were
         * removed from section 04 for that reason, so switching this on unchanged puts them
         * straight back. Replace them with current captures before restoring, or drop the
         * asset entries and let the reserved wells show instead.
         *
         * Hidden for now. A `false` guard rather than a comment, deliberately: JSX children
         * cannot take a line comment, and a block comment would end early at the closing
         * delimiter of the JSX comment nested inside this section. The guard also keeps the
         * markup parsed and its references live, so it cannot rot while switched off.
         *
         * To restore: change `false` to `true`. Everything it needs is still in place:
         * VIEWS above with its three assets, the files under static/img/platform, and
         * .slotImage, .slotWell, .slotTag, .slotLabel and .slotBrief in the stylesheet.
         *
         * The section numbers below are not renumbered. Moving 05 to 04 would turn
         * restoring this into a multi-file edit, and the gap in the sequence is visible only
         * to someone counting the headings.
         */}
        {false && (
          <section className={styles.section} id="views">
            <SectionHead
              num="04"
              title="What the platform looks like"
              lede="Four views cover most of what a platform team does here: find the repositories, watch the runs, manage the policy, and read a single plan in detail. They are screenshots of a separate, commercial product, kept visually apart from the open-source material elsewhere on this site so the boundary stays obvious."
            />
            <ul className={styles.slots}>
              {VIEWS.map(([label, brief, asset]) => (
                <li key={label}>
                  {/*
                   * A reserved well at the aspect ratio the real screenshot will occupy, so
                   * the page does not reflow when the image lands and so the amount of
                   * missing material is obvious to anyone reviewing the page.
                   */}
                  {asset ? (
                    <img
                      className={styles.slotImage}
                      src={`${base}${asset.src}`}
                      alt={asset.alt}
                      loading="lazy"
                    />
                  ) : (
                    <div className={styles.slotWell} role="img" aria-label={`${label}, screenshot pending`}>
                      <span className={styles.slotTag}>Asset pending</span>
                      <span className={styles.slotLabel}>{label}</span>
                    </div>
                  )}
                  <p className={styles.slotBrief}>{brief}</p>
                </li>
              ))}
            </ul>
          </section>
        )}

        {/* ================= 05 COMPARISON ================= */}
        <section className={styles.section} id="comparison">
          <SectionHead num="05" title="What you already have, and what you would gain" />
          <table className={styles.table}>
            <thead>
              <tr>
                <th scope="col">Capability</th>
                <th scope="col">Tirith OSS</th>
                <th scope="col">With StackGuardian</th>
              </tr>
            </thead>
            <tbody>
              {COMPARISON.map(([capability, oss, withSg]) => (
                <tr key={capability}>
                  <th scope="row">{capability}</th>
                  <td data-label="Tirith OSS">{oss}</td>
                  <td data-label="With StackGuardian">{withSg}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        {/* ================= 06 FAQ ================= */}
        <section className={styles.section} id="faq">
          <SectionHead num="06" title="Five questions worth asking first" />
          <div className={styles.faq}>
            {FAQ.map(([question, answer]) => (
              <details key={question} className={styles.details}>
                <summary>{question}</summary>
                <p>{answer}</p>
              </details>
            ))}
          </div>
          <p className={styles.caveat}>
            The complete masking behaviour, including what it does not catch, is in{' '}
            <Link to="/docs/tirith-usage/platform-check/">
              the platform-check documentation
            </Link>
            . The commitments are in{' '}
            <Link href={`${REPO}/blob/main/GOVERNANCE.md`}>GOVERNANCE.md</Link>.
          </p>
        </section>

        {/* ================= 07 CONTACT ================= */}
        <section className={styles.section} id="contact">
          <SectionHead
            num="07"
            title="Tell us how your IaC reaches production today"
            lede="Whatever it looks like now, we will map the shortest route from the pipelines you already run to consistent governance across all of them, with no execution migration, and your apply jobs stay where they are."
          />
          {/*
           * A booking link, not a form.
           *
           * The form asked for six fields before anyone had spoken, which is a lot to ask of
           * a reader who has just been told the open-source tool is enough for most teams.
           * The call picks a time and asks for nothing else.
           *
           * EnquiryForm is still defined above and no longer rendered. It is kept because
           * the HubSpot wiring it depends on (the portal id and form guid, supplied from the
           * environment and never committed) is still in docusaurus.config.js and in the
           * deploy workflow, and untangling that is a separate decision from this one.
           */}
          <div className={styles.bookCall}>
            <Link className={styles.btnPrimary} href="https://www.stackguardian.io/book-call">
              Book a call <span aria-hidden="true">→</span>
            </Link>
            <span className={styles.bookCallNote}>
              Thirty minutes with an engineer, not a qualification call. Bring the pipeline
              you actually run.
            </span>
          </div>

          <p className={styles.caveat}>
            Would rather keep it public?{' '}
            <Link
              href={issueUrl({
                template: 'general-issue.md',
                title: 'Governing many repositories: ',
              })}>
              Open an issue
            </Link>{' '}
            instead. For anything that is not commercially sensitive, that gets you the
            maintainers rather than a sales process.
          </p>
        </section>

        <Colophon styles={styles} />
      </main>
    </Layout>
  );
}
