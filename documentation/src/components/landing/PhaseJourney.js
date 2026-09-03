import {useState} from 'react';
import Link from '@docusaurus/Link';

import {DEMO_PHASES, DEMO_REPOS} from '../../data/demoPhases';
import styles from '../../pages/index.module.css';

// The PRs are stacked chronologically, but a first-time reader needs to see the
// core loop before the optional platform migration: set up, fail, fix, scale, publish.
const PHASES = [0, 2, 3, 1, 4].map((sourceIndex, index) => ({
  ...DEMO_PHASES[sourceIndex],
  number: String(index + 1).padStart(2, '0'),
}));

export default function PhaseJourney() {
  const [activeIndex, setActiveIndex] = useState(0);
  const phase = PHASES[activeIndex];

  return (
    <div className={styles.phaseJourney}>
      <ol className={styles.phaseRail} aria-label="Tirith adoption walkthrough">
        {PHASES.map((item, index) => {
          const active = index === activeIndex;
          return (
            <li key={item.number}>
              <button
                type="button"
                className={styles.phaseSelect}
                data-active={active ? 'true' : undefined}
                aria-current={active ? 'step' : undefined}
                aria-controls="phase-detail"
                onClick={() => setActiveIndex(index)}>
                <span className={styles.phaseSelectNum}>{item.number}</span>
                <span className={styles.phaseSelectCopy}>
                  <span className={styles.phaseSelectGroup}>{item.group}</span>
                  <span className={styles.phaseSelectTitle}>{item.title}</span>
                  <span className={styles.phaseSelectSummary}>{item.summary}</span>
                </span>
              </button>
            </li>
          );
        })}
      </ol>

      <article
        className={styles.phaseDetail}
        id="phase-detail"
        aria-labelledby={`phase-title-${phase.number}`}>
        <div className={styles.phaseDetailHead}>
          <div>
            <span className={styles.phaseEyebrow}>
              Phase {phase.number} · {phase.group}
            </span>
            <h3 className={styles.phaseTitle} id={`phase-title-${phase.number}`}>
              {phase.title}
            </h3>
          </div>
          <span className={styles.phaseTag}>{phase.tag}</span>
        </div>

        <p className={styles.phaseBody}>{phase.body}</p>

        <div className={styles.phaseDelta}>
          <span>CHANGE</span>
          <strong>{phase.delta}</strong>
        </div>

        <pre className={styles.phaseCode} aria-label={`Phase ${phase.number} change`}>
          <code>{phase.code}</code>
        </pre>

        <div className={styles.phaseOutcome} data-tone={phase.outcome.tone}>
          <div className={styles.phaseOutcomeHead}>
            <span className={styles.phaseOutcomeLabel}>{phase.outcome.label}</span>
            <strong>{phase.outcome.title}</strong>
          </div>
          <ul>
            {phase.outcome.items.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
          <p>{phase.outcome.note}</p>
        </div>

        {/*
          * Repository roots, not deep links. The three demos are maintained independently
          * and get rebased; a link to pull/6 or to a branch is stale the moment that
          * happens, and a dead link on the landing page is worse than one less click.
          */}
        <div className={styles.phaseLinks}>
          {DEMO_REPOS.map((repo) => (
            <Link href={repo.url} key={repo.id}>
              {repo.name} <span aria-hidden="true">→</span>
            </Link>
          ))}
        </div>
      </article>
    </div>
  );
}
