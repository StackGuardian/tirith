import {useMemo, useState} from 'react';
import Link from '@docusaurus/Link';
import {
  AXIS_SLOT,
  READING_STEPS,
  REGION_BY_KEY,
  SPECIMENS,
  commandLine,
  evaluate,
  resultLines,
  verdict,
} from '../../data/specimens';
import styles from '../../pages/index.module.css';

/*
 * THE SPECIMEN — the first viewport.
 *
 * One policy at display scale, one axis, and a grid of resources that re-reads itself
 * every time the axis moves. The evaluation is real (see src/data/specimens.js); the
 * document being evaluated is synthetic and labelled as such in the UI.
 *
 * The chosen visual world names a technique -- bind a range input to
 * font-variation-settings through a custom property, so one control remaps the whole
 * page's type. That is built here rather than imitated: --spec-wdth drives Martian
 * Mono's real width axis on the verdict readout, so dragging the threshold physically
 * narrows and widens the word.
 */

/*
 * Which of the three regions each line of the document belongs to.
 *
 * Resolved by brace depth rather than by hardcoded line numbers, so editing a policy
 * string in specimens.js cannot silently mis-label the annotation. A key listed in
 * REGION_BY_KEY claims its line; if that line opens a block, it claims the block and
 * the closing brace too, and the region ends when the depth comes back.
 */
function regionsFor(policy) {
  const lines = policy.split('\n');
  let region = null;
  let openedAt = 0;
  let depth = 0;

  return lines.map((line) => {
    const key = (line.match(/"([a-z_]+)"\s*:/) || [])[1];
    if (!region && key && REGION_BY_KEY[key]) {
      region = REGION_BY_KEY[key];
      openedAt = depth;
    }
    const mine = region;
    depth += (line.match(/[{[]/g) || []).length - (line.match(/[}\]]/g) || []).length;
    if (region && depth <= openedAt) region = null;
    return mine;
  });
}

// Minimal JSON tokenizer. Prism is already in the bundle, but it cannot mark up the one
// number the slider owns, and that mark is the whole point of the composition.
const TOKEN =
  /("(?:\\.|[^"\\])*")(\s*:)|("(?:\\.|[^"\\])*")|(-?\d+(?:\.\d+)?)|(true|false|null)/g;

function highlight(text, keyPrefix) {
  const out = [];
  let last = 0;
  let match;
  TOKEN.lastIndex = 0;
  while ((match = TOKEN.exec(text)) !== null) {
    if (match.index > last) {
      out.push(text.slice(last, match.index));
    }
    const [full, key, colon, str, num, lit] = match;
    if (key) {
      out.push(
        <span key={`${keyPrefix}-${match.index}`} className={styles.jsonKey}>
          {key}
        </span>,
        colon,
      );
    } else if (str) {
      out.push(
        <span key={`${keyPrefix}-${match.index}`} className={styles.jsonStr}>
          {str}
        </span>,
      );
    } else if (num) {
      out.push(
        <span key={`${keyPrefix}-${match.index}`} className={styles.jsonNum}>
          {num}
        </span>,
      );
    } else if (lit) {
      out.push(
        <span key={`${keyPrefix}-${match.index}`} className={styles.jsonLit}>
          {lit}
        </span>,
      );
    }
    last = match.index + full.length;
  }
  if (last < text.length) out.push(text.slice(last));
  return out;
}

function PolicyCode({specimen, axisValue, active, onRegion}) {
  const lines = specimen.policy.split('\n');
  const regions = useMemo(() => regionsFor(specimen.policy), [specimen.policy]);
  const stepFor = (r) => READING_STEPS.find((step) => step.region === r);

  return (
    <pre
      className={styles.policyCode}
      data-active={active || undefined}
      aria-label="The policy being evaluated">
      <code>
        {lines.map((line, i) => {
          const slot = line.indexOf(AXIS_SLOT);
          const region = regions[i];
          // The numeral sits on the first line of each region only, so the code
          // carries three marks rather than a margin full of them.
          const opensRegion = region && regions[i - 1] !== region;
          return (
            <span
              className={styles.codeLine}
              key={i}
              data-region={region || undefined}
              onMouseEnter={region ? () => onRegion(region) : undefined}
              onMouseLeave={region ? () => onRegion(null) : undefined}>
              {/* Own slot, always rendered: putting the numeral *inside* the line
                  number made the gutter read 1, 2, 3, 1, 5 — two different
                  numbering systems in one column. Fixed width keeps the code
                  aligned whether or not a line opens a region. */}
              <span className={styles.codeMark} aria-hidden="true">
                {opensRegion ? stepFor(region).n : ''}
              </span>
              <span className={styles.lineNo} aria-hidden="true">
                {i + 1}
              </span>
              {slot === -1 ? (
                highlight(line, i)
              ) : (
                <>
                  {highlight(line.slice(0, slot), `${i}a`)}
                  <mark className={styles.axisMark}>{axisValue}</mark>
                  {highlight(line.slice(slot + AXIS_SLOT.length), `${i}b`)}
                </>
              )}
            </span>
          );
        })}
      </code>
    </pre>
  );
}

export default function Specimen() {
  const [specimenId, setSpecimenId] = useState(SPECIMENS[0].id);
  // Which of the three regions is lit. Hover or focus sets it, click pins it, so the
  // annotation works on a touch screen and from the keyboard, not only under a mouse.
  const [active, setActive] = useState(null);
  const [pinned, setPinned] = useState(null);
  const specimen = useMemo(
    () => SPECIMENS.find((s) => s.id === specimenId),
    [specimenId],
  );
  const [axisByfId, setAxisById] = useState(() =>
    Object.fromEntries(SPECIMENS.map((s) => [s.id, s.axis.initial])),
  );
  const axisValue = axisByfId[specimen.id];

  const evaluation = useMemo(
    () => evaluate(specimen, axisValue),
    [specimen, axisValue],
  );
  const v = verdict(evaluation);

  // Axis position 0..1, used to drive the variable font's width axis.
  const t = (axisValue - specimen.axis.min) / (specimen.axis.max - specimen.axis.min);
  const wdth = 75 + t * 37.5; // Martian Mono's real wdth range

  const setAxis = (value) =>
    setAxisById((prev) => ({...prev, [specimen.id]: Number(value)}));

  const lit = pinned || active;
  const reading = specimen.reading;
  const axisText = specimen.axis.format(axisValue);

  return (
    <div
      className={styles.specimen}
      style={{'--spec-wdth': wdth.toFixed(1)}}
      data-verdict={v.word.toLowerCase()}>
      {/* ---------- across the top: what this policy says ---------- */}
      <div className={styles.readingRow}>
        <div className={styles.stageHead}>
          <span className={styles.tag}>SPECIMEN</span>
          <span className={styles.stageMeta}>{specimen.provider}</span>
        </div>
        {/* The policy, said once in English. Three parts, numbered to the three
            marked regions of the document below. */}
        <ul className={styles.reading}>
          {READING_STEPS.map((step) => {
            const value = reading[step.region];
            return (
              <li key={step.region}>
                <button
                  type="button"
                  className={styles.readingPart}
                  data-region={step.region}
                  data-lit={lit === step.region ? 'true' : undefined}
                  aria-pressed={pinned === step.region}
                  onMouseEnter={() => setActive(step.region)}
                  onMouseLeave={() => setActive(null)}
                  onFocus={() => setActive(step.region)}
                  onBlur={() => setActive(null)}
                  onClick={() =>
                    setPinned((p) => (p === step.region ? null : step.region))
                  }>
                  <span className={styles.readingLabel}>
                    <span className={styles.readingNum}>{step.n}</span>
                    {step.label}
                  </span>
                  <span className={styles.readingText}>
                    {typeof value === 'function' ? value(axisText) : value}
                  </span>
                </button>
              </li>
            );
          })}
        </ul>
      </div>

      {/* ---------- left: the dials, then the document they rewrite ----------
          The controls used to be a column down the right-hand side, which put
          the slider a full page-height away from the output it changes. Input on
          the left, output on the right, and the whole loop fits one screen. */}
      <div className={styles.specimenStage}>
        <div className={styles.controls}>
          <div className={styles.controlBlock}>
            <div className={styles.controlsHead}>CHANGE THE RULE</div>
            <div className={styles.control}>
              <div className={styles.controlTop}>
                <span className={styles.controlName}>{specimen.axis.label}</span>
                <span className={styles.controlValue}>
                  {specimen.axis.format(axisValue)}
                </span>
                <span className={styles.controlHint}>{specimen.axis.hint}</span>
              </div>
              <input
                className={styles.slider}
                type="range"
                min={specimen.axis.min}
                max={specimen.axis.max}
                step={specimen.axis.step}
                value={axisValue}
                onChange={(e) => setAxis(e.target.value)}
                aria-label={`${specimen.axis.hint} threshold, ${specimen.axis.format(
                  axisValue,
                )}`}
                style={{'--fill': `${t * 100}%`}}
              />
              <div className={styles.sliderEnds}>
                <span>{specimen.axis.min}</span>
                <span>{specimen.axis.max}</span>
              </div>
            </div>
          </div>

          <div className={styles.controlBlock}>
            <div className={styles.controlsHead}>CHANGE THE DOCUMENT</div>
            <div className={styles.presets} role="tablist" aria-label="Provider">
              {SPECIMENS.map((sp) => (
                <button
                  key={sp.id}
                  type="button"
                  role="tab"
                  aria-selected={sp.id === specimen.id}
                  className={
                    sp.id === specimen.id
                      ? `${styles.preset} ${styles.presetOn}`
                      : styles.preset
                  }
                  onClick={() => setSpecimenId(sp.id)}>
                  <span className={styles.presetName}>{sp.chip}</span>
                  <span className={styles.presetSub}>{sp.chipSub}</span>
                </button>
              ))}
            </div>
          </div>
        </div>

        <PolicyCode
          specimen={specimen}
          axisValue={axisValue}
          active={lit}
          onRegion={setActive}
        />
        <div className={styles.stageFoot}>
          <span>
            provider returns <em>{specimen.returns}</em>
          </span>
          <Link className={styles.stageLink} to={specimen.docPath}>
            Reference →
          </Link>
        </div>
      </div>

      {/* ---------- right: what the command actually prints ----------
          `WHAT COMES BACK` used to sit here as three rows — values extracted,
          final_result, exit. Every one of them is already in the output below
          (the numbered result lines, the Passed/Failed tally, `echo $?`), so it
          was a summary of a thing that was on the same screen. Removed; the
          resource list took the space, because that is what visibly moves. */}
      <div className={styles.resultBlock}>
        <div className={styles.term} data-verdict={v.word.toLowerCase()}>
          <div className={styles.termBar}>
            <span className={styles.termTitle}>stdout</span>
            <span className={styles.termVerdict}>
              exit <strong>{v.exit}</strong>
            </span>
          </div>
          <pre className={styles.termBody} aria-label="Tirith output">
            <code>
              <span className={styles.termCmd}>
                <span className={styles.termPrompt}>$</span> {commandLine(specimen)}
              </span>
              {resultLines(specimen, axisValue, evaluation).map((line, i) => (
                <span key={i} className={styles.termLine} data-kind={line.kind}>
                  {line.text || '\u00a0'}
                </span>
              ))}
              <span className={styles.termCmd}>
                <span className={styles.termPrompt}>$</span> echo $?
              </span>
              <span className={styles.termLine} data-kind="plain">
                {v.exit}
              </span>
            </code>
          </pre>
        </div>

        <div className={styles.addresses}>
          <div className={styles.addressesHead}>
            <h3 className={styles.addressesTitle}>
              Which resource failed?
            </h3>
            <p className={styles.addressesNote}>
              {evaluation.aggregate ? (
                <>
                  Tirith compares one total, {specimen.axis.format(evaluation.total)}. The
                  resources that contribute to that total are listed below.
                </>
              ) : (
                <>
                  The CLI output lists the tested values, but not their resource addresses.{' '}
                  <Link to="/docs/tirith-usage/interactive-interface/">tirith ui</Link>{' '}
                  maps the values back to the resources below.
                </>
              )}
            </p>
          </div>

          <ul className={styles.cells}>
            {evaluation.results.map((r, i) => (
              <li
                key={r.address}
                className={styles.cell}
                data-state={r.passed === null ? 'na' : r.passed ? 'pass' : 'fail'}>
                {/* Numbered to match the report's own result lines, so "6. FAILED"
                    on the left and this row are visibly the same finding. */}
                <span className={styles.cellNum} aria-hidden="true">
                  {i + 1}
                </span>
                <span className={styles.cellAddr}>
                  <span className={styles.cellMark} aria-hidden="true" />
                  {r.address}
                </span>
                <span className={styles.cellVal}>
                  {specimen.aggregate
                    ? `$${r.value}`
                    : `${r.value}${specimen.itemUnit ? ` ${specimen.itemUnit}` : ''}`}
                </span>
              </li>
            ))}
          </ul>

          <p className={styles.syntheticNote}>
            This browser demo uses sample {specimen.input} data and a Tirith-compatible
            evaluator. The policy syntax, messages, and exit codes mirror Tirith; install
            Tirith to evaluate real input documents.
          </p>
        </div>
      </div>
    </div>
  );
}
