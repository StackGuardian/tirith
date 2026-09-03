import Link from '@docusaurus/Link';
import Layout from '@theme/Layout';
import Heading from '@theme/Heading';

import TirithMark from '../components/brand/TirithMark';
import Colophon from '../components/site/Colophon';
import {RELEASES} from '../data/roadmap';
import {NEW_ISSUE, issueUrl} from '../data/repo';
import styles from './roadmap.module.css';
import '../css/chrome.module.css';

/*
 * ---------------------------------------------------------------------------
 * ROADMAP
 *
 * Job: say what is being built, in what order, without any of it reading as available.
 *
 * The whole page is unshipped material, which is the opposite of every other page on this
 * site, so the status tag is not decoration here: it is the only thing keeping the page
 * honest. Two consequences shape the design.
 *
 *   1. The word "planned" or "in dev" appears against every single item. There is no
 *      unlabelled item, because an unlabelled item in a list of labelled ones reads as
 *      shipped.
 *   2. No item is written in the present tense. "Counting destroys becomes a single
 *      policy", not "count destroys with one policy". The tense is the second line of
 *      defence when someone skims past the tags.
 *
 * Ordered by release, and each release carries a coarse relative date rather than a
 * calendar one. An order plus a rough distance is what a roadmap can honestly promise.
 * ---------------------------------------------------------------------------
 */

const hero = {
  eyebrow: 'What is being built',
  title: 'Not shipped yet.',
  dim: 'Here is the order, and roughly when.',
  lede:
    'Everything on this page is in development or planned. None of it is available, and ' +
    'anything already working lives in the documentation instead. It is ordered by ' +
    'release, and each item says which of the two it is.',
};

const STATUS = {
  inDev: {label: 'In dev', className: 'tagDev'},
  planned: {label: 'Planned', className: 'tagPlanned'},
};

function StatusTag({status}) {
  const s = STATUS[status];
  return <span className={styles[s.className]}>{s.label}</span>;
}

export default function Roadmap() {
  return (
    <Layout
      title="Roadmap: what is being built in Tirith"
      description={
        'Tirith’s roadmap: severity gating, blast radius, policy on the change, plan ' +
        'attestation and Checkov rule import. Everything here is in development or ' +
        'planned, and none of it has shipped.'
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
            <p className={styles.lede}>{hero.lede}</p>
            <div className={styles.heroLinks}>
              <Link className={styles.btnPrimary} to="/docs/getting-started-with-tirith/">
                What works today <span aria-hidden="true">→</span>
              </Link>
              {/* Deliberately the picker: "ask for something" is not one template. */}
              <Link className={styles.btnGhost} href={NEW_ISSUE}>
                Ask for something <span aria-hidden="true">→</span>
              </Link>
            </div>
          </div>
        </header>

        {RELEASES.map((release) => (
          <section className={styles.section} id={release.id} key={release.id}>
            <div className={styles.sectionHead}>
              <div className={styles.sectionLabel}>
                <span className={styles.sectionNum}>{release.n}</span>
                <Heading as="h2" className={styles.sectionTitle}>
                  {release.name}
                </Heading>
                <span className={styles.when}>{release.when}</span>
              </div>
              <p className={styles.sectionLede}>{release.lede}</p>
            </div>

            <ul className={styles.items}>
              {release.items.map((item) => (
                <li key={item.title}>
                  <div className={styles.itemHead}>
                    <span className={styles.itemTitle}>{item.title}</span>
                    <StatusTag status={item.status} />
                  </div>
                  <p className={styles.itemBody}>{item.body}</p>
                </li>
              ))}
            </ul>
          </section>
        ))}

        <section className={styles.finale}>
          <Heading as="h2" className={styles.finaleTitle}>
            The list is not fixed.
          </Heading>
          <p className={styles.finaleNote}>
            Order changes when evidence changes. Several items above moved because a
            translation corpus measured how many real policies they actually unblock, and one
            was dropped when the measurement came back at a single policy. If something you
            need is missing, saying so is the most useful thing you can do.
          </p>
          <div className={styles.heroLinks}>
            {/*
             * Straight to the feature-request template, not the picker. A button that names
             * one action should not open a menu of three, and the template carries the
             * `enhancement` label and the title prefix, which a blank form does not.
             */}
            <Link className={styles.btnPrimary} href={issueUrl({template: 'feature_request.md'})}>
              Request a feature <span aria-hidden="true">→</span>
            </Link>
            <Link className={styles.btnGhost} to="/learn/">
              Learn what ships today <span aria-hidden="true">→</span>
            </Link>
          </div>
        </section>

        <Colophon styles={styles} />
      </main>
    </Layout>
  );
}
