import {useEffect, useMemo, useState} from 'react';
import {evaluatePolicy, exitCodeFor, prettyPrint} from '../../data/tirithLite';
import styles from '../../pages/learn.module.css';

/**
 * The bench: a policy, a document, and what the command would print.
 *
 * Editable or not, it is the same component and the same evaluation — a lesson
 * is just a bench whose panes happen to start with a worked example in them.
 * Nothing is transcribed, so a lesson cannot describe output it does not produce.
 */

function Editor({label, value, onChange, rows, readOnly, name}) {
  return (
    <div className={styles.pane}>
      <div className={styles.paneHead}>
        <span className={styles.paneName}>{label}</span>
        {readOnly ? <span className={styles.paneRo}>read-only</span> : null}
      </div>
      <textarea
        className={styles.editor}
        value={value}
        onChange={onChange ? (e) => onChange(e.target.value) : undefined}
        readOnly={readOnly}
        rows={rows}
        spellCheck="false"
        autoComplete="off"
        autoCorrect="off"
        autoCapitalize="off"
        aria-label={`${label}${readOnly ? ', read only' : ', editable'}`}
        name={name}
      />
    </div>
  );
}

export default function Bench({
  policy,
  input,
  onPolicy,
  onInput,
  rows = 18,
  readOnly = false,
  idPrefix = 'bench',
}) {
  // What was last run, as opposed to what is currently typed. Evaluation is
  // explicit: you press Run, the same way you would press return on a command.
  const [ran, setRan] = useState({policy, input});
  const stale = ran.policy !== policy || ran.input !== input;

  // Editing a lesson back to its starting text should not leave a stale banner.
  useEffect(() => {
    setRan({policy, input});
  }, [idPrefix]); // eslint-disable-line react-hooks/exhaustive-deps

  const {document: doc, fatal} = useMemo(
    () => evaluatePolicy(ran.policy, ran.input),
    [ran],
  );
  const exit = exitCodeFor(doc);
  const lines = doc ? prettyPrint(doc) : [];

  const verdict = !doc
    ? 'error'
    : doc.final_result === true
      ? 'passed'
      : doc.final_result === false
        ? 'failed'
        : 'skipped';

  return (
    <div className={styles.bench}>
      <div className={styles.benchPanes}>
        <Editor
          label="policy.json"
          value={policy}
          onChange={onPolicy}
          readOnly={readOnly || !onPolicy}
          rows={rows}
          name={`${idPrefix}-policy`}
        />
        <Editor
          label="input.json"
          value={input}
          onChange={onInput}
          readOnly={readOnly || !onInput}
          rows={rows}
          name={`${idPrefix}-input`}
        />
      </div>

      <div className={styles.runBar}>
        <button
          type="button"
          className={styles.runButton}
          onClick={() => setRan({policy, input})}
          disabled={!stale}>
          {stale ? 'Run check' : 'Up to date'}
        </button>
        <span className={styles.runHint}>
          {stale ? 'edited since the last run' : 'showing the current policy'}
        </span>
      </div>

      <div className={styles.term} data-verdict={verdict} data-stale={stale ? 'true' : undefined}>
        <div className={styles.termBar}>
          <span className={styles.termTitle}>stdout</span>
          <span className={styles.termVerdict}>
            {doc ? (
              <>
                final_result <strong>{String(doc.final_result)}</strong> · exit{' '}
                <strong>{exit}</strong>
              </>
            ) : (
              <>
                exit <strong>1</strong>
              </>
            )}
          </span>
        </div>

        <pre className={styles.termBody} aria-live="polite" aria-label="Evaluation output">
          <code>
            <span className={styles.termCmd}>
              <span className={styles.termPrompt}>$</span> tirith --fail-on-error
              -policy-path policy.json -input-path input.json
            </span>
            {fatal ? (
              <>
                <span className={styles.termLine} data-kind="fail">
                  [ERROR] {fatal}
                </span>
                <span className={styles.termLine} data-kind="blank">
                  &nbsp;
                </span>
                <span className={styles.termLine} data-kind="dim">
                  {/* Exit 1 is "could not evaluate", which is a different thing
                      from a policy saying no. The distinction is the product. */}
                  nothing was evaluated, so this is exit 1 — not a verdict
                </span>
              </>
            ) : (
              lines.map((line, i) => (
                <span key={i} className={styles.termLine} data-kind={line.kind}>
                  {line.text || ' '}
                </span>
              ))
            )}
            <span className={styles.termCmd}>
              <span className={styles.termPrompt}>$</span> echo $?
            </span>
            <span className={styles.termLine} data-kind="plain">
              {exit}
            </span>
          </code>
        </pre>
      </div>
    </div>
  );
}
