/**
 * The pieces every non-docs page is built from.
 *
 * Extracted from the landing page when Learn, Playground, Policies, Traction
 * and Fleet arrived: six pages hand-rolling their own headings and cards is
 * how a site stops looking like one site. Anything used by more than one page
 * belongs here; anything used by exactly one belongs in that page.
 */

import Link from '@docusaurus/Link';
import Layout from '@theme/Layout';
import Heading from '@theme/Heading';
import CodeBlock from '@theme/CodeBlock';

import {EVENTS, capture} from '../analytics';
import styles from '../css/site.module.css';

export const REPO = 'https://github.com/StackGuardian/tirith';
export const ACTION_REPO = 'https://github.com/StackGuardian/tirith-iac-governance-action';
export const NEW_ISSUE = `${REPO}/issues/new/choose`;
export const BUILDER_URL = 'https://tirith-policy-builder.vercel.app/';

/**
 * A link to a specific issue template, rather than to the chooser.
 *
 * Every "ask a maintainer" link on this site used to land on
 * /issues/new/choose, which throws away the intent the visitor just expressed
 * and asks them to pick it again from a list. Deep-linking the template keeps
 * the context and gives maintainers a structured report instead of a blank box.
 *
 * `title` is appended to the template's own title prefix by GitHub, so pass the
 * whole line you want -- not a fragment meant to be concatenated.
 */
export function issueUrl({template = 'general-issue.md', title} = {}) {
  const params = new URLSearchParams({template});
  if (title) params.set('title', title);
  return `${REPO}/issues/new?${params.toString()}`;
}

/**
 * A placeholder that is impossible to miss.
 *
 * The alternative -- a quiet [X] in body text -- is how a page ships with [X]
 * on it. This renders as a warning chip in both themes and reads as obviously
 * unfinished to anyone who loads the page, including the person who was about
 * to approve it.
 */
export function Todo({children}) {
  return (
    <span className={styles.todo} role="note">
      <span className={styles.todoTag}>TODO</span>
      {children}
    </span>
  );
}

/**
 * A reserved space for an asset that does not exist yet.
 *
 * Renders the well at the aspect ratio the real thing will occupy, so the page
 * does not reflow when a GIF or screenshot lands, and so the amount of missing
 * material is obvious to anyone reviewing the page.
 *
 * `compact` is the in-card variant used by the demo pull-request cards, where
 * a full-width 16:9 frame would dwarf the copy beside it.
 */
export function VisualSlot({children, compact, label = 'ASSET'}) {
  return (
    <figure className={compact ? `${styles.visualSlot} ${styles.visualSlotCompact}` : styles.visualSlot}>
      <div className={styles.assetFrame}>
        <span className={styles.todoTag}>{label}</span>
      </div>
      <figcaption>{children}</figcaption>
    </figure>
  );
}

/** Several asset wells shown as a set. */
export function AssetGrid({children}) {
  return <div className={styles.assetGrid}>{children}</div>;
}

// Uses Docusaurus's own button classes rather than hand-rolled ones: they carry
// a readable foreground in both light and dark mode. The primary button
// additionally takes a CSS-module class that recolours it to the accent blue by
// overriding the --ifm-button-* custom properties (see site.module.css).
export function Action({label, to, href, primary, onClick}) {
  const className = primary
    ? `button button--lg button--primary ${styles.heroPrimary}`
    : 'button button--lg button--secondary';
  return to ? (
    <Link className={className} to={to} onClick={onClick}>
      {label}
    </Link>
  ) : (
    <Link className={className} href={href} onClick={onClick}>
      {label}
    </Link>
  );
}

/*
 * The id lands on the heading rather than on the <section>. Docusaurus's
 * broken-anchor check only registers heading anchors, and the navbar's
 * cross-page links have to resolve against something it knows about -- an id
 * on the wrapper builds clean but is reported broken on every page.
 */
export function Section({id, heading, kicker, children, tone}) {
  return (
    <section className={tone ? `${styles.section} ${styles[tone]}` : styles.section}>
      {kicker ? <p className={styles.kicker}>{kicker}</p> : null}
      {heading ? (
        <Heading as="h2" id={id} className={styles.sectionHeading}>
          {heading}
        </Heading>
      ) : null}
      {children}
    </section>
  );
}

export function PageShell({title, description, children}) {
  return (
    <Layout title={title} description={description}>
      <main className={styles.page}>{children}</main>
    </Layout>
  );
}

export function Hero({eyebrow, title, body, trust, actions, children}) {
  return (
    <header className={styles.hero}>
      {eyebrow ? <p className={styles.eyebrow}>{eyebrow}</p> : null}
      <Heading as="h1" className={styles.heroTitle}>
        {title}
      </Heading>
      {body ? <p className={styles.tagline}>{body}</p> : null}
      {actions?.length ? (
        <div className={styles.actions}>
          {actions.map((action) => (
            <Action key={action.label} {...action} />
          ))}
        </div>
      ) : null}
      {trust?.length ? (
        <ul className={styles.trustLine}>
          {trust.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      ) : null}
      {children}
    </header>
  );
}

export function Cards({items}) {
  return (
    <div className={styles.cards}>
      {items.map((item) => (
        <div key={item.title} className={styles.card}>
          <h3>{item.title}</h3>
          <p>{item.body}</p>
        </div>
      ))}
    </div>
  );
}

/**
 * A full-width invitation to a companion page.
 *
 * `subdued` is for the commercial route. The brief requires the commercial CTA
 * never to outrank `Use Tirith OSS`, so that variant loses its fill and its
 * button and becomes a plain link.
 */
export function Doorway({title, body, cta, subdued, onClick}) {
  return (
    <div className={subdued ? `${styles.doorway} ${styles.doorwaySubdued}` : styles.doorway}>
      <div className={styles.doorwayBody}>
        <h3>{title}</h3>
        <p>{body}</p>
      </div>
      {subdued ? (
        <Link to={cta.to} href={cta.href} onClick={onClick}>
          {cta.label} →
        </Link>
      ) : (
        <Link
          className="button button--secondary"
          to={cta.to}
          href={cta.href}
          onClick={onClick}
        >
          {cta.label}
        </Link>
      )}
    </div>
  );
}

export function DataTable({columns, rows, rowHeader = true}) {
  return (
    <table className={styles.table}>
      <thead>
        <tr>
          {columns.map((column, index) => (
            <th key={index}>{column}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((row) => (
          <tr key={row[0]}>
            {row.map((cell, index) =>
              index === 0 && rowHeader ? (
                <th key={index} scope="row">
                  {cell}
                </th>
              ) : (
                <td key={index}>{cell}</td>
              ),
            )}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

/*
 * CodeBlock owns its copy button and exposes no callback, so the click is
 * caught on the way up instead. Coarse by design: any button inside a code
 * block is the copy button.
 */
export function TrackedCode({ciSystem, mode = 'local', ...props}) {
  const onClick = (event) => {
    if (event.target.closest('button')) {
      capture(EVENTS.installCopy, {ci_system: ciSystem, mode});
    }
  };
  return (
    <div onClick={onClick}>
      <CodeBlock {...props} />
    </div>
  );
}

/* ------------------------------------------------------------ verdict --- */

/**
 * The four outcomes Tirith can return, and what each one means.
 *
 * `unevaluated` is the one that matters most and the one a scanner UI usually
 * gets wrong. A policy whose every check was skipped evaluated nothing, and
 * showing that as green is exactly the failure the exit-code contract exists
 * to prevent -- so it gets its own badge, its own glyph and its own wording,
 * never a quiet pass.
 */
export function outcomeOf(result) {
  if (!result || !('final_result' in result)) {
    return {
      key: 'error',
      label: 'Tool error',
      glyph: '!',
      className: styles.badgeUnknown,
      sr: 'Tool error: the evaluation did not complete',
      note: 'The evaluation did not complete. Your policy did not fail; fix the execution error and run it again.',
    };
  }
  if (result.final_result === true) {
    return {
      key: 'passed',
      label: 'Passed',
      glyph: '✓',
      className: styles.badgePass,
      sr: 'Passed: every check that ran passed',
      note: 'This plan satisfies the policy. Inspect the resources evaluated before exporting the rule.',
    };
  }
  if (result.final_result === false) {
    return {
      key: 'failed',
      label: 'Failed',
      glyph: '✕',
      className: styles.badgeFail,
      sr: 'Failed: a check ran and failed',
      note: 'This change would be blocked.',
    };
  }
  return {
    key: 'unevaluated',
    label: 'Unevaluated',
    glyph: '?',
    className: styles.badgeUnknown,
    sr: 'Unevaluated: no policy answer was reached, which is not a pass',
    note: 'Tirith could not reach a policy answer. This is not a pass. Review the provider input, match count and policy diagnostics.',
  };
}

function Evidence({item}) {
  const passed = item.passed === true;
  const address = item.meta?.address;
  const actions = item.meta?.change?.actions;
  return (
    <li>
      <span
        className={`${styles.evidenceGlyph} ${passed ? styles.evidencePass : styles.evidenceFail}`}
        aria-hidden="true"
      >
        {passed ? '✓' : '✕'}
      </span>
      <span>
        <span className={styles.srOnly}>{passed ? 'Passed: ' : 'Failed: '}</span>
        {address ? (
          <>
            <code className={styles.resourceAddress}>{address}</code>
            {actions?.length ? (
              <span className={styles.actionTag}>{actions.join(', ')}</span>
            ) : null}
            <br />
          </>
        ) : null}
        {item.message}
      </span>
    </li>
  );
}

/**
 * Renders one real engine result.
 *
 * Every field read here comes out of
 * documentation/scripts/generate-fixtures.py, which runs the actual engine --
 * so this follows the engine's shape rather than an idealised version of it,
 * including the fact that a skipped check carries a message but no resource
 * metadata.
 */
export function Verdict({example, showExit = true}) {
  const {result, exitCode, exitMeaning} = example;
  const outcome = outcomeOf(result);
  const failing = (result.evaluators || []).reduce(
    (total, evaluator) => total + (evaluator.result || []).filter((r) => r.passed === false).length,
    0,
  );

  return (
    <div className={styles.verdict}>
      <div className={styles.verdictHead}>
        <span className={`${styles.badge} ${outcome.className}`}>
          <span aria-hidden="true">{outcome.glyph}</span>
          {outcome.label}
        </span>
        <span className={styles.srOnly}>{outcome.sr}</span>
        <strong>{result.meta?.name}</strong>
        {showExit ? (
          <span className={styles.verdictExit}>
            exit <code>{exitCode}</code> — {exitMeaning}
          </span>
        ) : null}
      </div>
      <div className={styles.verdictBody}>
        {outcome.key === 'failed' && failing ? (
          <p className={styles.muted}>
            Tirith found {failing} failing resource{failing === 1 ? '' : 's'}; each one below shows
            the planned action and the value behind the result.
          </p>
        ) : (
          <p className={styles.muted}>{outcome.note}</p>
        )}

        {(result.evaluators || []).map((evaluator) => (
          <div key={evaluator.id} className={styles.evaluator}>
            <div>
              <strong>{evaluator.description || evaluator.id}</strong>
            </div>
            <div className={styles.evaluatorId}>
              <code>{evaluator.id}</code> — {evaluator.passed ? 'passed' : 'failed'}
            </div>
            <ul className={styles.evidence}>
              {(evaluator.result || []).map((item, index) => (
                <Evidence key={index} item={item} />
              ))}
            </ul>
          </div>
        ))}

        {result.errors?.length ? (
          <div className={styles.evaluator}>
            <strong>Errors</strong>
            <ul className={styles.evidence}>
              {result.errors.map((error, index) => (
                <li key={index}>
                  <span className={styles.evidenceGlyph} aria-hidden="true">
                    !
                  </span>
                  <span>{typeof error === 'string' ? error : JSON.stringify(error)}</span>
                </li>
              ))}
            </ul>
          </div>
        ) : null}
      </div>
    </div>
  );
}

export {styles};
