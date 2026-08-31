import {useState} from 'react';
import Link from '@docusaurus/Link';

import {PIPELINE_TARGETS} from '../../data/demoPhases';
import styles from '../../pages/index.module.css';

/**
 * The same gate, wired up five ways.
 *
 * The point of the switcher is that almost nothing changes between them: the policies, the
 * verdicts and the exit codes are identical, and only the invocation differs. GitHub has a
 * wrapper Action; everything else calls the CLI, which is what the Action does underneath.
 *
 * Each target links either to a public demo repository (`url`) or to the documentation that
 * covers it (`to`) -- never both, and never a link that does not exist.
 */
export default function PlatformSetup() {
  const [activeId, setActiveId] = useState(PIPELINE_TARGETS[0].id);
  const active = PIPELINE_TARGETS.find((t) => t.id === activeId);

  return (
    <div className={styles.platformSetup}>
      <div className={styles.platformTabs} aria-label="Choose where Tirith runs">
        {PIPELINE_TARGETS.map((target) => (
          <button
            type="button"
            key={target.id}
            className={styles.platformTab}
            data-active={target.id === activeId ? 'true' : undefined}
            aria-pressed={target.id === activeId}
            onClick={() => setActiveId(target.id)}>
            {target.name}
          </button>
        ))}
      </div>

      <div className={styles.platformBody}>
        <span className={styles.fieldLabel}>{active.file}</span>
        <pre className={styles.block} aria-label={`${active.name} configuration`}>
          <code>{active.code}</code>
        </pre>
        <p className={styles.platformNote}>{active.note}</p>
        {active.url ? (
          <Link className={styles.platformLink} href={active.url}>
            {active.linkLabel} <span aria-hidden="true">→</span>
          </Link>
        ) : (
          <Link className={styles.platformLink} to={active.to}>
            {active.linkLabel} <span aria-hidden="true">→</span>
          </Link>
        )}
      </div>
    </div>
  );
}
