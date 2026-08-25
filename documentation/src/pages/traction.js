import Link from '@docusaurus/Link';

import {EVENTS, track, usePageView} from '../analytics';
import {
  Action,
  DataTable,
  Hero,
  PageShell,
  REPO,
  Section,
  Todo,
  issueUrl,
  styles,
} from '../components/site';

/*
 * ---------------------------------------------------------------------------
 * TRACTION
 *
 * Job: make OSS momentum independently verifiable, while being candid about
 * what an accountless, telemetry-free local tool cannot observe.
 *
 * Every figure here is a placeholder, on purpose and by decision. The brief
 * specifies a scheduled server-side job that caches a versioned snapshot to
 * traction-data.json; that pipeline has not been built, and inventing numbers
 * on a page whose entire subject is verifiability would be self-defeating.
 *
 * The honest half of the page -- what these numbers do and do not measure, and
 * which metrics must not be published at all -- is real and shippable now.
 * ---------------------------------------------------------------------------
 */

const METRICS = [
  ['[X]', 'GitHub stars'],
  ['[Y]', 'Forks'],
  ['[Z]', 'Contributors'],
  ['[N]', 'Merged community PRs'],
  ['[P]', 'Maintained policies'],
  ['[R]', 'Releases'],
];

const WITHHELD = [
  ['Plans evaluated', 'Local mode has no telemetry. Any figure would count only connected platform use, and would have to say so.'],
  ['Repositories governed', 'Same reason. Private adoption is invisible by design, and that is a feature of the tool, not a gap to paper over.'],
  ['Weekly downloads', 'Unusable until the package-name collision is resolved: `tirith` on PyPI is an unrelated project, so its download count is not ours.'],
];

export default function Traction() {
  usePageView(EVENTS.tractionView);

  return (
    <PageShell
      title="Tirith Traction — GitHub Growth, Contributors and Releases"
      description="See Tirith's public GitHub stars, forks, contributors, releases and policy contributions, with links to the underlying evidence."
    >
      <Hero
        eyebrow="Public OSS receipts"
        title="The receipts behind Tirith."
        body="Stars, forks, contributors, releases and policy work, taken from public GitHub data. Local Tirith runs are deliberately private, so we do not pretend to know every repository using it."
        actions={[
          {label: 'Star Tirith on GitHub', href: REPO, primary: true, onClick: track(EVENTS.starFromTraction, {source: 'hero'})},
          {
            label: 'Become a listed adopter',
            href: issueUrl({template: 'general-issue.md', title: 'Adopter entry: '}),
            onClick: track(EVENTS.adopterIssueOpen, {source: 'hero'}),
          },
        ]}
      />

      <Section>
        <dl className={styles.stats}>
          {METRICS.map(([value, label]) => (
            <div key={label}>
              <dt className={styles.statValue}>{value}</dt>
              <dd>{label}</dd>
            </div>
          ))}
        </dl>

        <p>
          <Link href={REPO} onClick={track(EVENTS.metricSourceOpen, {source: 'traction'})}>
            See the repository on GitHub
          </Link>
        </p>

        <Todo>
          Every figure above is a placeholder and the page cannot ship with them. The brief
          specifies the fix: a scheduled job that fetches these server-side with the repository
          token, commits a versioned <code>traction-data.json</code> carrying each metric&apos;s
          source URL, query, bot exclusions and timestamp, and renders the last good snapshot with{' '}
          <em>Updated [timestamp]</em>, keeping the previous values and showing a compact stale
          state if a refresh fails, rather than dropping to zero. Do not fetch per page view: it
          burns rate limit and makes a static site depend on an API being up.
        </Todo>
      </Section>

      <Section id="transparency" heading="What GitHub activity can and cannot tell you">
        <p>
          GitHub activity shows attention, contribution and shipping. It does not prove successful
          production use. Tirith local mode intentionally sends no plan or usage telemetry, so
          adoption inside private repositories is largely invisible to us. We would rather publish a
          smaller number we can defend than a larger one we cannot.
        </p>

        <h3>Three numbers we will not print</h3>
        <DataTable columns={['Metric', 'Why not']} rows={WITHHELD} />

        <p className={styles.muted}>
          Connected StackGuardian figures, where they exist, are labelled separately and never mixed
          into the public OSS counts.
        </p>
      </Section>

      <Section id="charts" heading="The charts that should be here">
        <Todo>
          Four displays are specified and none are built: <strong>stars over time</strong>{' '}
          (cumulative daily stargazers, annotated with launch and release dates),{' '}
          <strong>shipping cadence</strong> (commits and releases over twelve months, annotating
          release days rather than rewarding noisy commits), <strong>community policy work</strong>{' '}
          (counting only reviewed, tested policies, each linked), and a{' '}
          <strong>contributor wall</strong> (opt-out, bots deduplicated, sorted by recency or
          contribution band, never by popularity). Each needs an accessible data table behind it, a
          summary that survives JavaScript being disabled, and reduced-motion behaviour.
        </Todo>
      </Section>

      <Section id="adopters" heading="Who is using it">
        <p>
          <Link href={`${REPO}/blob/main/ADOPTERS.md`}>ADOPTERS.md</Link> is opt-in and currently
          empty, which is the honest state of it. Nobody has been added without asking and nobody
          will be.
        </p>
        <p>
          Using Tirith? Add your organisation or project, named or anonymous, with whatever scope
          you are comfortable sharing. It is a pull request adding one row.
        </p>
      </Section>

      <Section id="contribute" heading="Worth more than a star" tone="finale">
        <p>
          A tested policy, a CI example for a system we do not cover well, a bug reproduction, or a
          lesson improvement. All four are more useful than a star, though stars are welcome too.
        </p>
        <div className={styles.actions}>
          <Action
            label="Find a good first issue"
            href={`${REPO}/labels/good%20first%20issue`}
            primary
            onClick={track(EVENTS.contributionCta, {kind: 'good-first-issue'})}
          />
          <Action
            label="Add an adopter entry"
            href={issueUrl({template: 'general-issue.md', title: 'Adopter entry: '})}
            onClick={track(EVENTS.adopterIssueOpen, {source: 'footer'})}
          />
        </div>
        <ul className={styles.inlineLinks}>
          <li>
            <Link
              href={issueUrl({template: 'policy-request.md'})}
              onClick={track(EVENTS.contributionCta, {kind: 'policy'})}
            >
              Contribute a policy
            </Link>
          </li>
          <li>
            <Link href={`${REPO}/blob/main/ROADMAP.md`} onClick={track(EVENTS.contributionCta, {kind: 'roadmap'})}>
              Request a roadmap item
            </Link>
          </li>
          <li>
            <Link href={issueUrl({template: 'general-issue.md', title: 'Traction data discrepancy: '})}>
              Report a discrepancy in these numbers
            </Link>
          </li>
        </ul>
      </Section>
    </PageShell>
  );
}
