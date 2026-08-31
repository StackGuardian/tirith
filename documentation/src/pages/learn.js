import {useState} from 'react';
import Link from '@docusaurus/Link';
import Layout from '@theme/Layout';
import Heading from '@theme/Heading';

import Bench from '../components/learn/Bench';
import {INPUT_DOC, LESSONS, PLAYGROUND_START} from '../data/lessons';
import {CONDITION_NAMES} from '../data/tirithLite';
import styles from './learn.module.css';
import '../css/chrome.module.css';

/*
 * ---------------------------------------------------------------------------
 * LEARN — writing Tirith policies
 *
 * Same visual world as the landing page (Policy Specimen Sheet).
 *
 * Everything on this page evaluates for real, in the browser, through
 * src/data/tirithLite.js — a documented subset of Tirith's core. Its limits are
 * stated on the page itself, not buried in a comment, because a teaching tool
 * that quietly disagrees with the real evaluator is worse than no tool.
 * ---------------------------------------------------------------------------
 */

/*
 * The lesson copy is written with markdown-style `backticks` because that is how
 * anyone editing it will naturally write. JSX renders those literally, so they
 * are turned into real <code> here rather than being hand-tagged in the data —
 * the previous landing page shipped a bug of exactly this shape.
 */
function md(text) {
  return text.split(/(`[^`]+`|\*\*[^*]+\*\*)/g).map((part, i) => {
    if (part.startsWith('`') && part.endsWith('`') && part.length > 2) {
      return (
        <code key={i} className={styles.inlineCode}>
          {part.slice(1, -1)}
        </code>
      );
    }
    if (part.startsWith('**') && part.endsWith('**') && part.length > 4) {
      return <strong key={i}>{part.slice(2, -2)}</strong>;
    }
    return part;
  });
}

function Lesson({lesson, input}) {
  const [policy, setPolicy] = useState(lesson.policy);
  const [doc, setDoc] = useState(input);
  const dirty = policy !== lesson.policy || doc !== input;

  return (
    <section className={styles.lesson} id={lesson.id}>
      <div className={styles.lessonHead}>
        <div className={styles.lessonLabel}>
          <span className={styles.lessonNum}>{lesson.n}</span>
          <Heading as="h2" className={styles.lessonTitle}>
            {lesson.title}
          </Heading>
        </div>
        <span className={styles.teaches}>{lesson.teaches}</span>
      </div>

      <div className={styles.lessonBody}>
        <div className={styles.lessonProse}>
          <p className={styles.prose}>{md(lesson.body)}</p>
          <p className={styles.aside}>{md(lesson.aside)}</p>
          <p className={styles.tryIt}>
            <span className={styles.tryLabel}>Try it</span>
            {md(lesson.tryIt)}
          </p>
          {dirty ? (
            <button
              type="button"
              className={styles.reset}
              onClick={() => {
                setPolicy(lesson.policy);
                setDoc(input);
              }}>
              Reset this lesson
            </button>
          ) : null}
        </div>

        <div className={styles.lessonBench}>
          <Bench
            policy={policy}
            input={doc}
            onPolicy={setPolicy}
            onInput={setDoc}
            rows={16}
            idPrefix={lesson.id}
          />
        </div>
      </div>
    </section>
  );
}

function Playground() {
  const [policy, setPolicy] = useState(PLAYGROUND_START);
  const [input, setInput] = useState(INPUT_DOC);

  return (
    <section className={styles.playground} id="playground">
      <div className={styles.lessonHead}>
        <div className={styles.lessonLabel}>
          <span className={styles.lessonNum}>07</span>
          <Heading as="h2" className={styles.lessonTitle}>
            Playground
          </Heading>
        </div>
        <span className={styles.teaches}>both panes yours</span>
      </div>

      <p className={styles.prose}>
        Both panes are yours. Edit, run, and read the report — a half-written policy is
        reported in the output rather than as a crash, because while you are editing, the
        broken state is the normal state.
      </p>

      <div className={styles.conditionList}>
        <span className={styles.conditionLabel}>Conditions available here</span>
        <span className={styles.conditionNames}>{CONDITION_NAMES.join('  ·  ')}</span>
      </div>

      <Bench
        policy={policy}
        input={input}
        onPolicy={setPolicy}
        onInput={setInput}
        rows={26}
        idPrefix="playground"
      />

      <div className={styles.actions}>
        <button
          type="button"
          className={styles.reset}
          onClick={() => {
            setPolicy(PLAYGROUND_START);
            setInput(INPUT_DOC);
          }}>
          Reset
        </button>
        <Link className={styles.textLink} to="/docs/tirith-reference/evaluators/">
          Every condition, in full <span aria-hidden="true">→</span>
        </Link>
      </div>
    </section>
  );
}

export default function Learn() {
  return (
    <Layout
      title="Learn — writing Tirith policies"
      description="A guided introduction to Tirith policy syntax, with a playground that evaluates in the browser.">
      <main className={styles.page}>
        <header className={styles.hero}>
          <Heading as="h1" className={styles.h1}>
            Learn to write a Tirith policy.
          </Heading>

          <div className={styles.heroPlate}>
            <div className={styles.heroLede}>
              <p className={styles.lede}>
                Six steps, one document, one policy that grows a rule at a time. Each
                step is editable — change a value, run it, and watch the verdict, the
                messages and the exit code move with it.
              </p>
              <div className={styles.heroLinks}>
                <a className={styles.btnPrimary} href="#playground">
                  Skip to the playground <span aria-hidden="true">→</span>
                </a>
                <Link className={styles.btnGhost} to="/docs/tirith-policies/tirith-policy-structure/">
                  Policy reference <span aria-hidden="true">→</span>
                </Link>
              </div>
            </div>

            <div className={styles.heroNote}>
              <span className={styles.fieldLabel}>Browser playground</span>
              <p className={styles.caveat}>
                This runs a Tirith-compatible teaching subset in your browser, not the Python
                package. Edit either pane and press <strong>Run check</strong>. The examples
                cover <code>stackguardian/json</code>; install Tirith to evaluate OpenTofu,
                Terraform,
                Kubernetes, Infracost, and StackGuardian Workflow inputs.
              </p>
              <div className={styles.heroLinks}>
                <Link className={styles.btnGhost} to="/docs/tirith-reference/evaluators/">
                  Every condition <span aria-hidden="true">→</span>
                </Link>
                <Link className={styles.btnGhost} to="/docs/tirith-usage/interactive-interface/">
                  tirith ui <span aria-hidden="true">→</span>
                </Link>
              </div>
            </div>
          </div>
        </header>

        <nav className={styles.toc} aria-label="Lessons">
          {LESSONS.map((l) => (
            <a key={l.id} className={styles.tocItem} href={`#${l.id}`}>
              <span className={styles.tocNum}>{l.n}</span>
              <span>{l.title}</span>
            </a>
          ))}
          <a className={styles.tocItem} href="#playground">
            <span className={styles.tocNum}>07</span>
            <span>Playground</span>
          </a>
        </nav>

        {LESSONS.map((lesson) => (
          <Lesson key={lesson.id} lesson={lesson} input={INPUT_DOC} />
        ))}

        <Playground />

        <section className={styles.finale}>
          <div className={styles.finaleGrid}>
            <div>
              <Heading as="h2" className={styles.finaleTitle}>
                Now run it for real.
              </Heading>
              <p className={styles.finaleNote}>
                The same policy file, against a terraform plan, in your own pipeline.
              </p>
            </div>
            <div>
              <span className={styles.fieldLabel}>Install</span>
              <pre className={styles.installBlock}>
                <code>
                  pip install git+https://github.com/StackGuardian/tirith.git
                </code>
              </pre>
              <Link className={styles.textLink} to="/docs/getting-started-with-tirith/">
                Getting started <span aria-hidden="true">→</span>
              </Link>
              {/* The next problem after "it works in my repository" is "it has to work
                  in two hundred of them", which is the one page that answers it. */}
              <Link className={styles.textLink} to="/docs/tirith-usage/ci-integration/">
                Put it in your pipeline <span aria-hidden="true">→</span>
              </Link>
              <Link className={styles.textLink} to="/docs/tirith-usage/editor-and-local/">
                Run it as you write <span aria-hidden="true">→</span>
              </Link>
              <Link className={styles.textLink} to="/at-scale/">
                Governing many repositories <span aria-hidden="true">→</span>
              </Link>
            </div>
          </div>
        </section>
      </main>
    </Layout>
  );
}
