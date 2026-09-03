import Link from '@docusaurus/Link';
import Layout from '@theme/Layout';
import {EVENTS, capture, track, usePageView} from '../analytics';
import Heading from '@theme/Heading';

import TirithMark from '../components/brand/TirithMark';
import CopyField from '../components/landing/CopyField';
import styles from './skills.module.css';
import '../css/chrome.module.css';

/*
 * SKILLS — Tirith in your coding agent.
 *
 * Organised around what someone does with it: install the skill, then write, check, run,
 * ship and debug policies. Every skill listed here is a real file in the repository under
 * .claude/skills/tirith-policies/, and every command is one that ships.
 */

const REPO = 'https://github.com/StackGuardian/tirith';
const SKILL_DIR = '.claude/skills/tirith-policies';
const RAW = 'https://raw.githubusercontent.com/StackGuardian/tirith/main';

const ROUTES = {
  playground: '/learn/#playground',
  policies: '/docs/tirith-policies/tirith-policy-cookbook/',
  atScale: '/at-scale/',
  ci: '/docs/tirith-usage/ci-integration/',
};

const hero = {
  eyebrow: 'Tirith in your coding agent',
  title: 'Your agent already writes policies.',
  dim: 'Give it the Tirith vocabulary.',
  lede:
    'Ask any agent for a guardrail and it writes plausible JSON against a schema it is ' +
    'guessing at. The Tirith skills give it the actual condition list, the argument key each ' +
    'provider reads, and the commands to check its own work before handing anything back.',
};

/*
 * One install command per client.
 *
 * The two that fetch the pack fetch every file in it. An earlier draft created the
 * reference/ directory and then downloaded only SKILL.md, which left the ten references
 * this page advertises as dangling paths inside the skill.
 */
const REFERENCES = [
  'schema',
  'validate',
  'verdicts',
  'terraform-plan',
  'other-providers',
  'variables',
  'install',
  'pipelines',
  'platform',
  'debug-ci',
];

const FETCH_PACK =
  `mkdir -p ${SKILL_DIR}/reference\n` +
  `BASE=${RAW}/${SKILL_DIR}\n` +
  `curl -sL $BASE/SKILL.md -o ${SKILL_DIR}/SKILL.md\n` +
  `for f in ${REFERENCES.join(' ')}; do\n` +
  `  curl -sL $BASE/reference/$f.md -o ${SKILL_DIR}/reference/$f.md\n` +
  `done`;

const CLIENTS = [
  {
    id: 'claude',
    name: 'Claude Code · Claude Desktop',
    detail:
      'Drop the folder into your repository. It is picked up automatically: no config file, ' +
      'no restart. Works in any project, not just this one.',
    command: FETCH_PACK,
    verify: 'Ask: "write a Tirith policy requiring an owner tag", and it should name real conditions.',
  },
  {
    id: 'cursor',
    name: 'Cursor',
    detail:
      'A single rule file scoped with globs, so it attaches by itself the moment a policy file ' +
      'is open and stays out of the way otherwise. Self-contained: it needs nothing else.',
    command:
      'mkdir -p .cursor/rules\n' +
      `curl -sL ${RAW}/.cursor/rules/tirith-policies.mdc \\\n` +
      '  -o .cursor/rules/tirith-policies.mdc',
    verify: 'Open a file under .tirith/policies, and the rule shows as attached in the chat panel.',
  },
  {
    id: 'agents',
    name: 'Codex · Zed · anything reading AGENTS.md',
    detail:
      'Fetch the pack, then point AGENTS.md at it. One file at the repository root is read by a ' +
      'growing number of clients, and the pack beside it keeps the references resolvable.',
    command:
      FETCH_PACK +
      '\n\nprintf \'\\n## Tirith policies\\nSee %s/SKILL.md\\n\' \\\n' +
      `  "${SKILL_DIR}" >> AGENTS.md`,
    verify: 'Ask your agent what condition types Tirith supports. It should say thirteen, not guess.',
  },
];

/* Every entry is a real file under .claude/skills/tirith-policies/. */
const SKILLS = [
  {
    group: 'Write and check',
    items: [
      ['Author a policy', 'SKILL.md', 'Turn an intent, “every resource needs an owner tag”, into valid policy JSON: the provider, the operation, the condition and the expression that ties them together.'],
      ['The schema', 'reference/schema.md', 'The closed vocabulary. Thirteen condition types, each provider’s operations, and the argument key that differs per provider, which is the one an agent otherwise invents.'],
      ['Validate it', 'reference/validate.md', 'The trap classes that produce a policy which looks right and gates nothing, and why a clean shape is not a working rule. tirith lint is in development; tirith ui validates against the live registries today.'],
      ['Run it and read the verdict', 'reference/verdicts.md', 'Exit 0, 1 and 3 and what each should do to a job, why final_result: null is not a pass, and how to find the resource behind a failure.'],
    ],
  },
  {
    group: 'Per document',
    items: [
      ['OpenTofu and Terraform plans', 'reference/terraform-plan.md', 'The seven operations, why attribute cannot see a destroy, replacement ordering, and why count measures the module rather than the change.'],
      ['Kubernetes, Infracost, JSON', 'reference/other-providers.md', 'attribute_path with kubernetes_kind, cost ceilings and the misspelled type that sums to zero and passes, and get_value wildcards for any other document.'],
      ['One policy, many environments', 'reference/variables.md', 'Parameterise with -var and -var-path, and the var. prefix that is silently required.'],
    ],
  },
  {
    group: 'While you write',
    items: [
      ['Run it in a pipeline', 'reference/pipelines.md', 'GitHub Actions, GitLab, Bitbucket, Jenkins, Azure DevOps and CircleCI: the plan step, the install, and making each exit code do the right thing to the job. The editor and pre-commit loop is in development and marked as such.'],
    ],
  },
  {
    group: 'Set up and ship',
    items: [
      ['Install Tirith', 'reference/install.md', 'Install from git, because it is not on PyPI, and the name there belongs to something else. Pinning a tag, the optional interface, and the Python floors.'],
      ['Add it to a pipeline', 'reference/pipelines.md', 'GitHub Actions, GitLab, Bitbucket, Jenkins, any container CI, and a pre-commit hook, plus making each exit code do the right thing to the job.'],
      ['Debug a red build', 'reference/debug-ci.md', 'Start from a failed job and end at the rule and the resource, ordered by what is most often the answer.'],
      ['Organization policies', 'reference/platform.md', 'tirith platform check: central policy across many repositories, what is masked on your runner before anything is uploaded, and which flags are required.'],
    ],
  },
];

const WORKFLOW = [
  ['Ask', 'Describe the guardrail in a sentence. The skill supplies the schema, so the agent picks a real provider, operation and condition instead of guessing.'],
  ['Check the shape', 'Check the condition type and every argument key against the closed vocabulary. An invented one is ignored rather than rejected, so the check reads nothing and passes.'],
  ['Check the meaning', 'Only evaluation proves a policy matches anything. Run it against a document that should fail it.'],
  ['Ship it', 'Commit the policy, add the gate to the pipeline, and let the exit code decide.'],
];

const BOUNDARIES = [
  ['Nothing here changes your infrastructure.', 'The commands read documents and return verdicts. An agent may propose a code change; a human reviews and merges it, as before.'],
  ['A drafted policy is a draft.', 'Generated JSON is worth no more than the evaluation that follows it.'],
  ['The engine decides, not the model.', 'Every verdict comes from the same evaluator your pipeline runs.'],
  ['Evaluation stays on your machine.', 'Your agent may be a hosted model, which is between you and your agent. Tirith itself makes no network call unless you use organization mode.'],
];

/* --------------------------------------------------------------------------- */

function SectionHead({num, title, lede}) {
  return (
    <div className={styles.sectionHead}>
      <div className={styles.sectionLabel}>
        <span className={styles.sectionNum}>{num}</span>
        <Heading as="h2" className={styles.sectionTitle}>{title}</Heading>
      </div>
      {lede ? <p className={styles.sectionLede}>{lede}</p> : null}
    </div>
  );
}

export default function Skills() {
  usePageView(EVENTS.aiView);

  return (
    <Layout
      title="Tirith skills for coding agents"
      description={
        'Give your coding agent the real Tirith schema and a way to check its own work: ' +
        'skills for Claude, Cursor and Codex covering policy authoring, validation, providers, ' +
        'installation and CI.'
      }>
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
                  href="#install">
                  Install the skills <span aria-hidden="true">→</span>
                </a>
                <a className={styles.btnGhost} href="#skills">
                  What it covers <span aria-hidden="true">→</span>
                </a>
              </div>
            </div>
          </div>
        </header>

        {/* ================= 01 INSTALL ================= */}
        <section className={styles.section} id="install">
          <SectionHead
            num="01"
            title="Install them in your client"
            lede="One command, and the file is self-contained: copy it into any repository and your agent picks it up."
          />
          <ul className={styles.clients}>
            {CLIENTS.map((c) => (
              <li key={c.id}>
                <span className={styles.clientName}>{c.name}</span>
                <p className={styles.clientDetail}>{c.detail}</p>
                <CopyField
                  onCopy={() => capture(EVENTS.skillCopy, {client: c.id})}
                  command={c.command}
                  label={`skill-${c.id}`}
                  prompt={false}
                />
                <p className={styles.clientVerify}>
                  <span className={styles.verifyLabel}>Check it worked</span>
                  {c.verify}
                </p>
              </li>
            ))}
          </ul>
          <p className={styles.caveat}>
            Working in VS Code? The{' '}
            <Link to="/docs/tirith-usage/editor-and-local/">editor setup</Link> wires lint and
            evaluate to one keystroke, so the policy your agent just wrote is proved before you
            read it. The skills teach your agent the vocabulary. To let it <em>run</em> a policy
            as well,
            install Tirith so the command is on PATH.{' '}
            <Link to="/docs/tirith-installation/quick-installation/">one pip command</Link>, and
            the skill's own install reference covers pinning a version.
          </p>
        </section>

        {/* ================= 02 WHAT IT COVERS ================= */}
        <section className={styles.section} id="skills">
          <SectionHead
            num="02"
            title="What it covers"
            lede="Twelve references, each a file in the skills folder. Your agent loads the entry skill and pulls the rest in as the task needs them."
          />
          {SKILLS.map((group) => (
            <div className={styles.skillGroup} key={group.group}>
              <span className={styles.skillGroupName}>{group.group}</span>
              <ul className={styles.skillList}>
                {group.items.map(([name, file, what]) => (
                  <li key={file}>
                    <span className={styles.skillName}>{name}</span>
                    <Link
                      className={styles.skillFile}
                      href={`${REPO}/blob/main/${SKILL_DIR}/${file}`}>
                      <code>{file}</code>
                    </Link>
                    <span className={styles.skillWhat}>{what}</span>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </section>

        {/* ================= 03 THE LOOP ================= */}
        <section className={styles.section} id="loop">
          <SectionHead
            num="03"
            title="How a policy gets written"
            lede="Their one standing instruction is never to hand back a policy it has not run. A policy that matches nothing looks identical to one that works."
          />
          <ol className={styles.loop}>
            {WORKFLOW.map(([k, v], i) => (
              <li key={k}>
                <span className={styles.loopNum}>{String(i + 1).padStart(2, '0')}</span>
                <h3>{k}</h3>
                <p>{v}</p>
              </li>
            ))}
          </ol>
          <div className={styles.actions}>
            <Link className={styles.btnPrimary} to={ROUTES.playground}>
              Try it in the playground <span aria-hidden="true">→</span>
            </Link>
            <Link className={styles.btnGhost} to={ROUTES.policies}>
              Browse worked policies <span aria-hidden="true">→</span>
            </Link>
          </div>
        </section>

        {/* ================= 04 BOUNDARIES ================= */}
        <section className={styles.section} id="boundaries">
          <SectionHead num="04" title="What it does not do" />
          <dl className={styles.defs}>
            {BOUNDARIES.map(([k, v]) => (
              <div className={styles.def} key={k}>
                <dt>{k}</dt>
                <dd>{v}</dd>
              </div>
            ))}
          </dl>
        </section>

        {/* ================= FINALE ================= */}
        <section className={styles.finale} id="next">
          <div className={styles.finaleGrid}>
            <div>
              <Heading as="h2" className={styles.finaleTitle}>
                Across every repository, not just this one.
              </Heading>
              <p className={styles.finaleNote}>
                An agent with the skill can write and prove a policy in the repository in front of
                it. What it cannot see is which of your two hundred repositories have no gate at
                all.
              </p>
            </div>
            <div className={styles.finaleLinks}>
              <Link
                className={styles.btnPrimary}
                to={ROUTES.atScale}>
                Tirith at scale <span aria-hidden="true">→</span>
              </Link>
              <Link className={styles.btnGhost} to={ROUTES.ci}>
                Keep it local <span aria-hidden="true">→</span>
              </Link>
            </div>
          </div>
        </section>

        <footer className={styles.colophon}>
          <span className={styles.colophonBrand}>
            <TirithMark className={styles.colophonMark} size={16} />
            Tirith · StackGuardian
          </span>
          <span><Link to="/">Landing page</Link></span>
          <span><Link to="/learn/">Learn</Link></span>
          <span><Link to="/at-scale/">Tirith at scale</Link></span>
          <span><Link href={REPO}>Source</Link></span>
        </footer>
      </main>
    </Layout>
  );
}
