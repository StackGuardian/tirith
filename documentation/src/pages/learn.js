import Link from '@docusaurus/Link';

import {EVENTS, track, usePageView} from '../analytics';
import {
  Action,
  Hero,
  PageShell,
  REPO,
  Section,
  Todo,
  TrackedCode,
  Verdict,
  issueUrl,
  styles,
} from '../components/site';
import fixtures from '../data/fixtures.json';

/*
 * ---------------------------------------------------------------------------
 * LEARN
 *
 * Job: turn an interested developer into someone who can explain a Tirith
 * verdict and add the first local check, without reading the reference docs.
 *
 * This is the course outline plus a fully worked first lesson, not seven
 * interactive lessons. The distinction is deliberate and is stated on the page:
 * lesson one is complete and real -- the plan, the policy and the verdict below
 * are the actual engine output for a fixture that ships with Tirith -- and the
 * remaining six are specified but not yet built.
 *
 * Shipping one honest lesson beats shipping seven shells. A visitor who works
 * through what is here can already read a verdict, which is the thing the page
 * exists to teach.
 * ---------------------------------------------------------------------------
 */

// Lesson one uses the tags example: it fails, and it fails on one resource out
// of two, which is the clearest possible illustration of resource-level
// evidence. A wholly-failing fixture teaches less.
const LESSON_ONE = fixtures.examples.find((e) => e.key === '01-required-tags');

const CURRICULUM = [
  {
    n: 1,
    title: 'Meet the plan',
    task: 'Identify create, update and delete actions in a supplied plan JSON.',
    ladder: 'Understand',
    ready: true,
  },
  {
    n: 2,
    title: 'Get the first verdict',
    task: 'Run a maintained policy against the fixture and distinguish pass, fail, unevaluated and tool error.',
    ladder: 'Observe',
    ready: true,
  },
  {
    n: 3,
    title: 'Read the evidence',
    task: 'Trace the failed result to rule, resource, action and before/after value.',
    ladder: 'Understand',
    ready: true,
  },
  {
    n: 4,
    title: 'Write a readable policy',
    task: 'Modify a JSON rule that requires an Owner tag; validate the schema and its test coverage.',
    ladder: 'Control',
  },
  {
    n: 5,
    title: 'Break it, then fix it',
    task: 'Remove the tag, see apply become unsafe, then make the one-line fix and re-run.',
    ladder: 'Remediate',
  },
  {
    n: 6,
    title: 'Add it to CI',
    task: 'Choose GitHub Actions, GitLab CI or the CLI and copy a pinned, local-mode snippet.',
    ladder: 'Govern',
  },
  {
    n: 7,
    title: 'Choose what comes next',
    task: 'Keep policies local, contribute one, or look at optional fleet governance.',
    ladder: 'Continue',
  },
];

const content = {
  hero: {
    eyebrow: 'Learn Tirith by doing',
    title: 'From Terraform plan to governed change — in one short course.',
    body:
      'Work through a real plan, watch a policy fail on a specific resource, and take the same ' +
      'check to a pipeline. Everything runs against public fixtures. No StackGuardian account and ' +
      'no private repository required.',
    trust: ['Free', 'Self-paced', 'Public fixtures', 'No account'],
  },
};

function LessonOne() {
  const example = LESSON_ONE;
  const planned = example.input.resource_changes || [];

  return (
    <>
      <p>
        Here is a Terraform plan with two resources in it. Before reading any policy, read the plan:
        every entry in <code>resource_changes</code> carries an address, the actions Terraform
        intends, and the values it will apply.
      </p>

      <ul className={styles.integrations}>
        {planned.map((change) => (
          <li key={change.address}>
            <code className={styles.resourceAddress}>{change.address}</code>
            <span className={styles.actionTag}>{(change.change?.actions || []).join(', ')}</span>
          </li>
        ))}
      </ul>

      <p>
        Now the guardrail. It is a JSON file, not a program: name the provider, name the value to
        inspect, and name the condition it has to satisfy.
      </p>

      <TrackedCode language="json" ciSystem="none">
        {JSON.stringify(example.policy, null, 2)}
      </TrackedCode>

      <p>
        <code>terraform_resource_type: "*"</code> means every resource in the plan is in scope, and{' '}
        <code>IsNotEmpty</code> means the value has to be present and non-blank. Run it, and Tirith
        returns this:
      </p>

      <Verdict example={example} />

      <p>
        <strong>Read what that says.</strong> The rule did not simply fail. It was checked
        against both resources and reported on each one separately: it passed on{' '}
        <code>aws_instance.web</code>, naming the resource, its planned <code>create</code> action
        and the value it found, <code>product-123</code>. That per-resource evidence is the whole
        point of evaluating the plan rather than the source.
      </p>

      <p>
        Now notice what the failing line does <em>not</em> say. It tells you the attribute{' '}
        <code>tags.costcenter</code> was not found, but it does not name the resource it was looking
        at. When an attribute is missing there is no value to attach a resource to, so the failure
        arrives without an address. You find the culprit by looking at the plan for the resource
        that has no such tag, which here is <code>aws_s3_bucket.assets</code>. Worth knowing before
        you meet it in a pipeline: a policy that checks for the presence of something reports
        differently from one that checks the shape of something that exists.
      </p>

      <p>
        And the exit code is <code>{example.exitCode}</code>, not <code>1</code>. Three means a
        check ran and said no. One would mean Tirith could not tell you either way. A pipeline that
        treats every non-zero code alike cannot tell a working gate from a broken one, which is why
        the two are kept apart.
      </p>

      <div className={styles.actions}>
        <Action
          label="Open this in the Playground"
          to="/playground"
          onClick={track(EVENTS.learnToPlayground, {lesson: 1})}
        />
        <Action
          label="Add it to my pipeline"
          to="/docs/tirith-usage/ci-integration/"
          onClick={track(EVENTS.learnToQuickstart, {lesson: 1})}
        />
      </div>
    </>
  );
}

export default function Learn() {
  usePageView(EVENTS.learnStart);

  return (
    <PageShell
      title="Learn Tirith IaC Governance — Interactive Terraform Policy Course"
      description="Learn how to evaluate Terraform and OpenTofu plans, write readable Tirith policies and add an enforceable check to any CI pipeline. No account required."
    >
      <Hero
        {...content.hero}
        actions={[
          {label: 'Start with the first verdict', href: '#lesson-1', primary: true},
          {label: 'Browse all lessons', href: '#curriculum'},
        ]}
      />

      <Section id="lesson-1" heading="Lesson 1: read a plan, then read a verdict">
        <LessonOne />
      </Section>

      <Section id="curriculum" heading="Where this one sits in the seven">
        <p>
          Seven short lessons, one concept and one thing to do in each. They run in the order the
          job happens: you cannot fix what you cannot explain, and you should not enforce
          what you have not watched fail once.
        </p>
        <ol className={styles.lessons}>
          {CURRICULUM.map((lesson) => (
            <li key={lesson.n}>
              <span className={styles.lessonNumber}>{lesson.n}</span>
              <span className={styles.lessonTitle}>
                {lesson.title}
                {lesson.ready ? null : <span className={styles.optionalTag}>not built yet</span>}
              </span>
              <span className={styles.optionalTag}>{lesson.ladder}</span>
              <span className={styles.lessonTask}>{lesson.task}</span>
            </li>
          ))}
        </ol>

        <Todo>
          Lesson 1 above covers the ground of lessons 1–3 in one page and is complete. Lessons 4–7
          are specified but not built. Building them needs a course shell that does not exist yet:
          a left rail with progress, a sticky Previous/Next footer, per-lesson completion driven by
          the intended interaction rather than by scrolling, and local progress storage with a
          working Reset. Until then this page is one worked lesson plus an outline, and says so.
        </Todo>
      </Section>

      <Section id="how" heading="Nothing on this page is a screenshot">
        <ul>
          <li>
            <strong>Real output, not screenshots.</strong> Every verdict on this page is generated
            by running the Tirith engine over a fixture that ships with the tool. If the engine's
            behaviour changes, so does this page.
          </li>
          <li>
            <strong>Reproducible on your machine.</strong> The fixtures are in the repository, so
            every result here can be re-run locally, and nothing depends on a service staying up.
          </li>
          <li>
            <strong>Never just a green tick.</strong> A result is only useful with the evidence and
            the enforcement consequence attached, so both are always shown.
          </li>
          <li>
            <strong>Nothing is uploaded and nothing is gated.</strong> No account, no sign-in, no
            progress sent anywhere.
          </li>
        </ul>
      </Section>

      <Section id="finish" heading="You governed the change — not just the code." tone="finale">
        <p>
          You read a concrete plan, evaluated a policy, explained the result and saw the exit code a
          pipeline would act on. Take that contract into a repository you own, or keep experimenting
          with another plan.
        </p>
        <div className={styles.actions}>
          <Action
            label="Add Tirith to my pipeline"
            to="/docs/tirith-usage/ci-integration/"
            primary
            onClick={track(EVENTS.learnToQuickstart, {source: 'course-end'})}
          />
          <Action label="Open Playground" to="/playground" onClick={track(EVENTS.learnToPlayground, {source: 'course-end'})} />
        </div>
        <ul className={styles.inlineLinks}>
          <li>
            <Link href={REPO} onClick={track(EVENTS.heroStar, {source: 'learn'})}>
              Star Tirith
            </Link>
          </li>
          <li>
            <Link href={issueUrl({template: 'general-issue.md', title: 'Lesson request: '})}>
              Request a lesson
            </Link>
          </li>
          <li>
            <Link to="/ai" onClick={track(EVENTS.aiView, {source: 'learn'})}>
              Do this with a coding agent
            </Link>
          </li>
          <li>
            <Link to="/fleet">Explore fleet governance</Link>
          </li>
        </ul>
      </Section>
    </PageShell>
  );
}
