import Link from '@docusaurus/Link';
import Layout from '@theme/Layout';
import Heading from '@theme/Heading';
import CodeBlock from '@theme/CodeBlock';

import styles from './index.module.css';

/*
 * ---------------------------------------------------------------------------
 * COPY
 *
 * All prose for the landing page lives in this one object, deliberately kept
 * apart from the markup below so it can be edited or lifted out without
 * reading any JSX.
 *
 * It is derived from the repository README, which is the source of truth. If
 * the two disagree, the README wins and this file is stale.
 * ---------------------------------------------------------------------------
 */
const content = {
  hero: {
    title: 'Tirith — IaC Governance plugin',
    tagline:
      'Plugin IaC Governance for any pipeline, running anywhere. Evaluate plans with Tirith, ' +
      'protect sensitive values, enforce centralised governance, and surface actionable results ' +
      'before infrastructure changes are applied.',
    body:
      'Tirith reads the plan your pipeline already produces, checks it against your policies, and ' +
      'exits non-zero so a violating change never reaches apply. Apache-2.0, and no account needed.',
    install: 'pip install git+https://github.com/StackGuardian/tirith.git',
    actions: [
      {label: 'Get started', to: '/docs/getting-started-with-tirith/', primary: true},
      {label: 'GitHub', href: 'https://github.com/StackGuardian/tirith'},
    ],
  },

  problem: {
    heading: 'The problem',
    body:
      'A pipeline that runs init, plan and apply deploys whatever the plan says. Nothing sits ' +
      'between the plan and the change.',
    points: [
      'Every repository does it its own way, so there is no one place to see what was deployed, or what was refused.',
      'Rules that do exist live in whichever pipeline someone wrote them into, and get copied into the next repository by hand.',
      'When a check does fail, the log says a job failed. It does not say which rule, on which resource, or what value broke it.',
    ],
  },

  add: {
    heading: 'What you add',
    body: 'Two lines, on GitHub Actions:',
    code:
      '- run: terraform show -json tfplan > plan.json\n' +
      '- uses: StackGuardian/tirith-iac-governance-action@v2',
    note:
      'With a plan.json in the working directory that is the whole integration — no with: block. ' +
      'Policies are JSON files committed under .tirith/policies.',
  },

  get: {
    heading: 'What you get',
    items: [
      {
        title: 'Policies as data, not code',
        body:
          'A rule is a JSON file describing what to look for, rather than a program you have to ' +
          'maintain. Terraform plans, terraform state, Kubernetes manifests, Infracost breakdowns ' +
          'and arbitrary JSON are all evaluated the same way.',
      },
      {
        title: 'Cost, before the change is applied',
        body:
          'Point Tirith at an infracost breakdown and gate on the monthly or hourly total of the ' +
          'resources the plan would create.',
      },
      {
        title: 'Sensitive values masked on your own runner',
        body:
          'Masking happens before anything leaves the machine, so a value marked sensitive stays ' +
          'out of the report and out of any upload.',
      },
      {
        title: 'An exit code your pipeline can act on',
        body:
          'Exit 3 means a policy said no; exit 1 means Tirith could not tell you either way. A job ' +
          'that treats every non-zero code alike cannot tell a working gate from a broken one.',
      },
      {
        title: 'The plan and the code, kept together',
        body:
          'In platform mode each run uploads the masked documents alongside the terraform source ' +
          'they describe, so a finding can still be read against the code that caused it later on.',
      },
      {
        title: 'One policy set, many pipelines',
        body:
          'Because Tirith is a CLI rather than an integration built into one CI system, the same ' +
          'policies gate a GitHub Actions job, a GitLab job and a laptop. In platform mode, Tirith ' +
          'rules and Checkov findings come back in a single verdict.',
      },
    ],
  },

  worksWith: {
    heading: 'Works with',
    items: [
      {
        title: 'GitHub Actions',
        body:
          'A native action that finds the plan, posts a sticky pull-request comment, creates a ' +
          'check run and sets the exit code.',
        link: {
          label: 'tirith-iac-governance-action',
          href: 'https://github.com/StackGuardian/tirith-iac-governance-action',
        },
      },
      {
        title: 'GitLab CI, and any container-based CI',
        body:
          'Install the CLI in the job and call it directly, which is all the action does ' +
          'underneath. There is no GitLab-native equivalent of the action.',
      },
      {
        title: 'Your machine',
        body: 'The same command, the same verdict, no account and no network.',
      },
    ],
  },

  platform: {
    heading: 'Keeping policy in one place',
    body:
      'Everything above works with policy files committed to your repository. If you would rather ' +
      'not copy those files into every repository that needs gating, tirith platform check ' +
      'evaluates against the policies a StackGuardian organization enforces instead — same ' +
      'document, same verdict, same exit codes, plus a central run history. That mode is optional, ' +
      'and is the only part that talks to a network.',
    link: {label: 'Read about platform mode', to: '/docs/tirith-usage/platform-check/'},
  },
};

/*
 * ---------------------------------------------------------------------------
 * MARKUP
 * ---------------------------------------------------------------------------
 */

function Action({label, to, href, primary}) {
  const className = primary ? styles.actionPrimary : styles.action;
  return to ? (
    <Link className={className} to={to}>
      {label}
    </Link>
  ) : (
    <Link className={className} href={href}>
      {label}
    </Link>
  );
}

function Hero() {
  const {title, tagline, body, install, actions} = content.hero;
  return (
    <header className={styles.hero}>
      <Heading as="h1" className={styles.heroTitle}>
        {title}
      </Heading>
      <p className={styles.tagline}>{tagline}</p>
      <p>{body}</p>
      <CodeBlock language="bash">{install}</CodeBlock>
      <div className={styles.actions}>
        {actions.map((action) => (
          <Action key={action.label} {...action} />
        ))}
      </div>
    </header>
  );
}

function Section({heading, children}) {
  return (
    <section className={styles.section}>
      <Heading as="h2" className={styles.sectionHeading}>
        {heading}
      </Heading>
      {children}
    </section>
  );
}

export default function Home() {
  return (
    <Layout title="Tirith — IaC Governance plugin" description={content.hero.tagline}>
      <main className={styles.page}>
        <Hero />

        <Section heading={content.problem.heading}>
          <p>{content.problem.body}</p>
          <ul>
            {content.problem.points.map((point) => (
              <li key={point}>{point}</li>
            ))}
          </ul>
        </Section>

        <Section heading={content.add.heading}>
          <p>{content.add.body}</p>
          <CodeBlock language="yaml">{content.add.code}</CodeBlock>
          <p className={styles.muted}>{content.add.note}</p>
        </Section>

        <Section heading={content.get.heading}>
          <ul className={styles.list}>
            {content.get.items.map((item) => (
              <li key={item.title}>
                <strong>{item.title}.</strong> {item.body}
              </li>
            ))}
          </ul>
        </Section>

        <Section heading={content.worksWith.heading}>
          <ul className={styles.list}>
            {content.worksWith.items.map((item) => (
              <li key={item.title}>
                <strong>{item.title}</strong> — {item.body}
                {item.link ? (
                  <>
                    {' '}
                    <Link href={item.link.href}>{item.link.label}</Link>.
                  </>
                ) : null}
              </li>
            ))}
          </ul>
        </Section>

        <Section heading={content.platform.heading}>
          <p>{content.platform.body}</p>
          <p>
            <Link to={content.platform.link.to}>{content.platform.link.label}</Link>
          </p>
        </Section>
      </main>
    </Layout>
  );
}
