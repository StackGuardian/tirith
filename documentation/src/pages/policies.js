import {useMemo, useState} from 'react';
import Link from '@docusaurus/Link';

import {EVENTS, capture, track} from '../analytics';
import {
  Action,
  Hero,
  PageShell,
  Section,
  Todo,
  TrackedCode,
  Verdict,
  issueUrl,
  styles,
} from '../components/site';
import fixtures from '../data/fixtures.json';
import coverage from '../data/coverage.json';

/*
 * ---------------------------------------------------------------------------
 * POLICIES
 *
 * Two populations of policy, shown in one grid so the relationship between
 * them is obvious rather than argued:
 *
 *   Open source -- the worked policies that ship in this repository. Real
 *   files, covered by the test suite, shown with the verdict the engine
 *   actually returns. Anyone can read, copy and run them today.
 *
 *   Platform -- the check catalogue StackGuardian maintains for its users.
 *   Shown as categories with counts and a description of the territory each
 *   one covers. Individual check IDs, titles and detection logic are
 *   deliberately absent from this page AND from this repository: they are the
 *   substance of the commercial offer, and publishing them would give it away
 *   for nothing. src/data/coverage.json carries numbers only.
 *
 * The honest framing matters here. `available` is what the platform scanner
 * can evaluate from its inputs; it is a catalogue, not a shipped feature list,
 * and the page says so rather than implying 382 checks run today.
 * ---------------------------------------------------------------------------
 */

/*
 * The starter pack in examples/, not the five worked examples bundled with `tirith ui`. These are
 * the policies meant to be copied into a real repository, and each has been run twice: against a
 * fixture built to trip it, and against a clean plan. The second run is the one usually missing
 * from a policy library -- a rule nobody has watched pass might be firing on everything.
 */
const OSS_POLICIES = fixtures.pack.map((entry) => ({
  id: entry.key,
  source: 'oss',
  title: entry.title,
  summary: '',
  severity: entry.severity,
  provider: (entry.provider || '').split('/').pop(),
  operations: entry.operations || [],
  checks: entry.evaluatorCount,
  clean: entry.clean,
  example: entry,
}));

const PLATFORM_POLICIES = coverage.categories.map((category) => ({
  id: category.code,
  source: 'platform',
  title: category.name,
  summary: category.focus,
  provider: 'repository',
  available: category.available,
  catalogue: category.catalogue,
}));

const ALL = [...OSS_POLICIES, ...PLATFORM_POLICIES];

const FILTERS = [
  ['all', 'Everything', ALL.length],
  ['oss', 'Open source', OSS_POLICIES.length],
  ['platform', 'Platform', PLATFORM_POLICIES.length],
];

/*
 * The sign-up destination. Kept as a constant with a TODO rather than guessed:
 * a wrong sign-up URL on the one page whose job is conversion is worse than a
 * visible gap.
 */
const SIGNUP_URL = null;

function OssCard({policy}) {
  const {example} = policy;
  const failing = example.result.final_result === false;
  return (
    <article className={styles.policyCard}>
      <div className={styles.policyBadges}>
        <span className={`${styles.sourceTag} ${styles.sourceOss}`}>Open source</span>
        {policy.severity ? <span className={styles.metaTag}>{policy.severity}</span> : null}
        <span className={styles.metaTag}>{policy.provider}</span>
      </div>

      <h3>{policy.title}</h3>

      <p className={styles.policyFacts}>
        {policy.checks} evaluator{policy.checks === 1 ? '' : 's'}
        {policy.operations.length ? ` · reads ${policy.operations.join(', ')}` : ''}
      </p>

      {/*
        * Both runs, side by side. Either number alone misleads: a policy only ever seen failing
        * might be firing on everything, and one only ever seen passing might be matching nothing.
        */}
      <p className={styles.policyFacts}>
        <span className={failing ? styles.evidenceFail : styles.evidencePass}>
          exit {example.exitCode} on a plan built to trip it
        </span>
        {policy.clean ? (
          <>
            {' · '}
            <span
              className={policy.clean.exitCode === 0 ? styles.evidencePass : styles.evidenceFail}
            >
              exit {policy.clean.exitCode} on a clean plan
            </span>
          </>
        ) : null}
      </p>

      <details className={styles.details}>
        <summary>Read the policy and its verdict</summary>
        <TrackedCode language="json" ciSystem="none">
          {JSON.stringify(example.policy, null, 2)}
        </TrackedCode>
        <Verdict example={example} />
      </details>

      <div className={styles.policyActions}>
        <Link
          to="/playground"
          onClick={track(EVENTS.policyExample, {policy_name: policy.id})}
        >
          Open in Playground →
        </Link>
      </div>
    </article>
  );
}

function PlatformCard({policy}) {
  return (
    <article className={`${styles.policyCard} ${styles.policyCardPlatform}`}>
      <div className={styles.policyBadges}>
        <span className={`${styles.sourceTag} ${styles.sourcePlatform}`}>Platform</span>
        <span className={styles.metaTag}>{policy.id}</span>
      </div>

      <h3>{policy.title}</h3>
      <p>{policy.summary}</p>

      <p className={styles.policyFacts}>
        <strong className={styles.countPill}>{policy.available}</strong> checks available
        {policy.catalogue > policy.available ? (
          <span className={styles.muted}> · {policy.catalogue} written</span>
        ) : null}
      </p>
    </article>
  );
}

export default function Policies() {
  const [filter, setFilter] = useState('all');
  const [query, setQuery] = useState('');

  const visible = useMemo(() => {
    const q = query.trim().toLowerCase();
    return ALL.filter((policy) => {
      if (filter !== 'all' && policy.source !== filter) return false;
      if (!q) return true;
      return `${policy.title} ${policy.summary || ''} ${policy.id}`.toLowerCase().includes(q);
    });
  }, [filter, query]);

  const ossShown = visible.filter((p) => p.source === 'oss').length;

  return (
    <PageShell
      title="Tirith Policies: maintained Terraform and OpenTofu guardrails"
      description="Browse the open-source Tirith policies with their real verdicts, and see the breadth of checks StackGuardian maintains for platform users."
    >
      <Hero
        eyebrow="Maintained guardrails"
        title="Guardrails you can read in one sitting."
        body="A Tirith policy is JSON data rather than a program: name the provider, the value to inspect and the condition it has to satisfy. The thirteen open-source ones below are the starter pack. Each has been run against a plan built to trip it and against a clean plan, and both verdicts are shown. The platform catalogue covers the ground a single repository's policies cannot."
        trust={['Apache-2.0', 'Tested', 'Copy and own it', 'No account for the open ones']}
        actions={[
          {label: 'Try one in the Playground', to: '/playground', primary: true},
          {label: 'Read the policy reference', to: '/docs/tirith-policies/tirith-policy-reference/'},
        ]}
      />

      <Section id="catalogue" heading="Browse the policies">
        <div className={styles.filterBar}>
          <ul className={styles.chips} role="tablist" aria-label="Filter policies by source">
            {FILTERS.map(([key, label, count]) => (
              <li key={key}>
                <button
                  type="button"
                  role="tab"
                  aria-selected={filter === key}
                  className={filter === key ? `${styles.chip} ${styles.chipActive}` : styles.chip}
                  onClick={() => setFilter(key)}
                >
                  {label} <span className={styles.chipCount}>{count}</span>
                </button>
              </li>
            ))}
          </ul>

          <input
            type="search"
            className={styles.searchInput}
            placeholder="Search policies…"
            aria-label="Search policies"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
        </div>

        <p className={styles.muted} role="status">
          Showing {visible.length} of {ALL.length}
          {ossShown ? ` · ${ossShown} you can run right now` : ''}
        </p>

        {visible.length ? (
          <div className={styles.policyGrid}>
            {visible.map((policy) =>
              policy.source === 'oss' ? (
                <OssCard key={policy.id} policy={policy} />
              ) : (
                <PlatformCard key={policy.id} policy={policy} />
              ),
            )}
          </div>
        ) : (
          <p>
            Nothing matches “{query}”. <button type="button" className={styles.chip} onClick={() => setQuery('')}>Clear the search</button>
          </p>
        )}
      </Section>

      <Section id="coverage" heading="What the platform catalogue adds" tone="quiet">
        <p>
          The starter pack gates the plan your pipeline produces. It cannot tell you that
          a repository has state committed to it, that a workflow applies without a reviewed plan,
          or that four teams pinned four different provider versions, because none of that is in a
          plan. Those questions are what the platform catalogue is for.
        </p>

        <dl className={styles.stats}>
          <div>
            <dt className={styles.statValue}>{coverage.totals.available}</dt>
            <dd>checks available to platform users</dd>
          </div>
          <div>
            <dt className={styles.statValue}>{coverage.totals.categories}</dt>
            <dd>categories, repository to estate</dd>
          </div>
          <div>
            <dt className={styles.statValue}>{coverage.totals.catalogue}</dt>
            <dd>checks written in total</dd>
          </div>
          <div>
            <dt className={styles.statValue}>{OSS_POLICIES.length}</dt>
            <dd>open source, no account</dd>
          </div>
        </dl>

        <p className={styles.muted}>
          The gap between {coverage.totals.available} and {coverage.totals.catalogue} is deliberate
          and worth stating: the remainder need evidence a repository scan cannot reach, such as a plan, a
          state file, a live cloud account, or a convention only your organisation can define. They
          are counted here rather than quietly dropped.
        </p>

        <Todo>
          Two things to settle before this page is public. First, the numbers:{' '}
          <strong>{coverage.totals.available} is a catalogue, not a shipped feature list</strong>:
          roughly {coverage.totals.shippedToday} of these run in the registry today. Either label
          the figure as coverage-in-progress or advertise the shipped count, and get the wording
          approved; a visitor who signs up expecting {coverage.totals.available} live checks and
          finds {coverage.totals.shippedToday} will not come back. Second, the sign-up destination
          below is unset, so supply the URL.
        </Todo>
      </Section>

      <Section id="signup" heading="Run all of them against your repositories" tone="finale">
        <p>
          The open-source policies stay yours: Apache-2.0, no account, evaluated wherever your
          pipeline runs. Signing up adds the checks a single plan cannot answer, across every
          repository you own, on a schedule, with the findings in one place.
        </p>

        <div className={styles.actions}>
          {SIGNUP_URL ? (
            <Action
              label="Sign up and scan your repositories"
              href={SIGNUP_URL}
              primary
              onClick={track(EVENTS.platformInterest, {stage: 'policies-signup'})}
            />
          ) : (
            <Action
              label="See what fleet governance covers"
              to="/fleet"
              primary
              onClick={track(EVENTS.platformInterest, {stage: 'policies-signup'})}
            />
          )}
          <Action label="Keep it local instead" to="/docs/tirith-usage/ci-integration/" />
        </div>

        {SIGNUP_URL ? null : (
          <Todo>
            No sign-up URL is configured, so the primary action routes to the Fleet page, which is
            a real destination, but one step longer than it should be. Supply the sign-up URL and
            set <code>SIGNUP_URL</code> in this file.
          </Todo>
        )}
      </Section>

      <Section id="contribute" heading="Contribute a guardrail">
        <p>
          A tested policy is the most useful contribution this project can receive. If your team
          relies on a rule that is not here, open an issue describing it, including the plan shape
          it needs to match, so it can be tested rather than assumed.
        </p>
        <div className={styles.actions}>
          <Action label="Propose a policy" href={issueUrl({template: 'policy-request.md'})} primary />
          <Action label="Read the policy reference" to="/docs/tirith-policies/tirith-policy-reference/" />
        </div>
        <p className={styles.muted}>
          Writing one with a coding agent? <Link to="/ai">The MCP server and skill files</Link> give
          it the closed condition list and let it evaluate a draft against a real plan, instead of
          handing you JSON that fails at run time.
        </p>
      </Section>
    </PageShell>
  );
}
