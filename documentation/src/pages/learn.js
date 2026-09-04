import {useCallback, useEffect, useState} from 'react';
import Link from '@docusaurus/Link';
import Layout from '@theme/Layout';
import Heading from '@theme/Heading';

import TirithMark from '../components/brand/TirithMark';
import Colophon from '../components/site/Colophon';
import Bench from '../components/learn/Bench';
import {TRACKS} from '../data/lessons';
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

/*
 * The blank bench, seeded from whichever track is open.
 *
 * `start` and `doc` are only the *initial* state, so the parent gives this a key of the
 * track id: changing tracks remounts it rather than trying to reconcile a policy the
 * reader may have edited with a document it no longer matches.
 */
function Playground({start, doc, num}) {
  const [policy, setPolicy] = useState(start);
  const [input, setInput] = useState(doc);

  return (
    <section className={styles.playground} id="playground">
      <div className={styles.lessonHead}>
        <div className={styles.lessonLabel}>
          <span className={styles.lessonNum}>{num}</span>
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
            setPolicy(start);
            setInput(doc);
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

/*
 * The chooser.
 *
 * Three providers stacked on one page meant a reader wanting Kubernetes scrolled past nine
 * lessons about something else to reach two about their own problem. So the page asks first
 * and shows one track.
 *
 * WHY THE HASH IS THE STATE. `/learn/#kubernetes` has to open on Kubernetes, because that is
 * the link someone sends a colleague, and `#playground` is already linked from the Skills
 * page and must keep working. Reading it on mount rather than tracking a separate piece of
 * state means a deep link and a click end up in exactly the same place.
 *
 * The initial render is always the first track, deliberately: this page is prerendered at
 * build time, where there is no location, and a component that renders one thing on the
 * server and another on the client is a hydration mismatch. The effect below corrects it
 * after mount, which is one frame on a page whose content is several screens tall.
 */
function useTrack() {
  const [id, setId] = useState(TRACKS[0].id);

  useEffect(() => {
    const fromHash = () => {
      const hash = window.location.hash.replace('#', '');
      if (!hash) return;
      // A track id, or any lesson inside one: both mean "open that track".
      const track =
        TRACKS.find((t) => t.id === hash) ||
        TRACKS.find((t) => t.lessons.some((l) => l.id === hash));
      if (track) setId(track.id);
    };
    fromHash();
    window.addEventListener('hashchange', fromHash);
    return () => window.removeEventListener('hashchange', fromHash);
  }, []);

  return [id, setId];
}

export default function Learn() {
  const [trackId, setTrackId] = useTrack();
  const track = TRACKS.find((t) => t.id === trackId) || TRACKS[0];

  /*
   * Choosing a track rewrites the hash without a navigation, so the back button walks the
   * reader's choices instead of leaving the page, and a copied URL carries the track. No
   * scroll, because the selector is what they just clicked and it should stay put.
   */
  const choose = useCallback((id) => {
    setTrackId(id);
    if (typeof window !== 'undefined') {
      window.history.replaceState(null, '', `#${id}`);
    }
  }, [setTrackId]);

  return (
    <Layout
      title="Learn — writing Tirith policies"
      description="A guided introduction to Tirith policy syntax, with a playground that evaluates in the browser.">
      <main className={styles.page}>
        <header className={styles.hero}>
          {/*
           * The letterhead, as on every other page in this set. Learn was the one
           * route that opened straight onto its headline, so it read as a page from
           * a different site -- the navbar above it is shared, which made the missing
           * row look like a rendering fault rather than a design choice.
           */}
          <div className={styles.letterhead}>
            <TirithMark className={styles.letterheadMark} size={40} />
            <span className={styles.letterheadName}>Tirith</span>
            <span className={styles.letterheadRule} aria-hidden="true" />
            <span className={styles.letterheadNote}>Three providers, eleven lessons</span>
          </div>

          <Heading as="h1" className={styles.h1}>
            Learn to write a Tirith policy.
          </Heading>

          <div className={styles.heroPlate}>
            <div className={styles.heroLede}>
              <p className={styles.lede}>
                Pick the thing you actually need to gate and learn on that. The syntax is
                the same for all three, so the JSON track teaches it fastest and the other
                two teach what changes. Every step is editable: change a value, run it, and
                watch the verdict, the messages and the exit code move with it.
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
                package. Edit either pane and press <strong>Run check</strong>. It implements
                <code>stackguardian/json</code>, <code>stackguardian/terraform_plan</code> and
                <code>stackguardian/kubernetes</code>, and its verdicts are checked against the
                real engine. Install Tirith for Infracost and StackGuardian Workflow inputs,
                and for anything you intend to trust.
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

        {/*
          * The chooser. Radio semantics rather than buttons, because these are three
          * states of one setting and a screen reader should be told they are exclusive.
          */}
        <section className={styles.chooser} aria-labelledby="choose-provider">
          <span className={styles.chooserLabel} id="choose-provider">
            Choose what you want to gate
          </span>
          <div className={styles.chooserTabs} role="radiogroup" aria-labelledby="choose-provider">
            {TRACKS.map((t) => {
              const active = t.id === track.id;
              return (
                <button
                  key={t.id}
                  type="button"
                  role="radio"
                  aria-checked={active}
                  className={active ? styles.tabOn : styles.tab}
                  onClick={() => choose(t.id)}>
                  <span className={styles.tabName}>{t.tab}</span>
                  <span className={styles.tabProvider}>{t.provider}</span>
                  <span className={styles.tabCount}>
                    {t.lessons.length} {t.lessons.length === 1 ? 'lesson' : 'lessons'}
                  </span>
                </button>
              );
            })}
          </div>
        </section>

        {/*
          * The open track. Keyed on the track id so switching remounts every lesson:
          * each one holds the reader's edits in its own state, and reconciling those
          * against a different document would leave a policy and an input that do not
          * belong together.
          */}
        <div key={track.id}>
          <section className={styles.track} id={track.id}>
            <span className={styles.trackProvider}>{track.provider}</span>
            <Heading as="h2" className={styles.trackTitle}>
              {track.title}
            </Heading>
            <p className={styles.trackLede}>{track.lede}</p>
            <p className={styles.trackForYou}>{track.forYou}</p>
          </section>

          <nav className={styles.toc} aria-label={`Lessons: ${track.title}`}>
            {track.lessons.map((l) => (
              <a key={l.id} className={styles.tocItem} href={`#${l.id}`}>
                <span className={styles.tocNum}>{l.n}</span>
                <span>{l.title}</span>
              </a>
            ))}
            <a className={styles.tocItem} href="#playground">
              <span className={styles.tocNum}>
                {String(track.lessons.length + 1).padStart(2, '0')}
              </span>
              <span>Playground</span>
            </a>
          </nav>

          {track.lessons.map((lesson) => (
            <Lesson key={lesson.id} lesson={lesson} input={track.input} />
          ))}

          <Playground
            start={track.playground}
            doc={track.input}
            num={String(track.lessons.length + 1).padStart(2, '0')}
          />
        </div>

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
                  pip install "git+https://github.com/StackGuardian/tirith.git@1.2.0"
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

        <Colophon styles={styles} />
      </main>
    </Layout>
  );
}
