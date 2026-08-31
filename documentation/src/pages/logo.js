import Link from '@docusaurus/Link';
import Layout from '@theme/Layout';
import Heading from '@theme/Heading';

import Glyph from '../components/brand/Glyph';
import TirithMark from '../components/brand/TirithMark';
import {KEEP, SEVEN_WALLS, THE_CLIMB, TWO_WALLS} from '../data/logoStory';
import styles from './logo.module.css';
import '../css/chrome.module.css';

/*
 * ---------------------------------------------------------------------------
 * THE MARK — why the logo is what it is
 *
 * Same visual world as the landing page (Policy Specimen Sheet). Reached only from
 * the colophon: this is background for someone who has already read the product page,
 * not a step towards installing anything, so it stays out of the navbar.
 *
 * WHAT THIS PAGE IS FOR, AND WHAT IT IS NOT
 *   It explains the idea behind the mark that shipped. It is not a design record.
 *   Production detail was deliberately removed: no size ladder, no pixel thresholds,
 *   no box dimensions, and no account of the forms that were drawn and rejected. If
 *   any of that is ever needed again it belongs in brand/README.md, or in the canvas
 *   at docs/Tirith Logo.html, which remains the source of truth for the geometry.
 *
 * COPY RULES FOR THIS FILE
 *   - The city, the four moves and the opposed-gates argument are the canvas's own
 *     writing, quoted or lightly trimmed.
 *   - Two passages are written for this page rather than lifted: the second paragraph
 *     of §01 and the middle of §03. Both extend an argument the canvas already makes
 *     -- that the defence is the sequence, not the wall -- rather than introducing a
 *     claim about the mark that nobody drew.
 *   - Claims about what Tirith does are checked against the repository README, which
 *     wins where the two disagree.
 * ---------------------------------------------------------------------------
 */

const hero = {
  title: 'Nothing reaches the summit',
  dim: 'unexamined.',
  lede:
    'Tirith stands between a plan and the change it would make, so a plan that breaks a ' +
    'rule you have written does not reach apply. The mark says that before a word does. ' +
    'It is not a castle and not a tower — it is a city seen from above, reduced until ' +
    'only the rule is left.',
  caption: 'Keep · the shipped mark',
};

const city = {
  num: '01',
  title: 'The city the name comes from',
  body: [
    'Minas Tirith held because of how it was laid out. Seven walls, a single gate in ' +
      'each, and every gate set on the far side of the one below it, so anyone who broke ' +
      'the first was walking sideways by the time he met the second.',
    'None of which is a wall being strong. A single wall, however thick, is one problem ' +
      'and it is solved once. Seven walls with their gates deliberately out of line is a ' +
      'different problem: it cannot be solved once and it cannot be solved quickly, ' +
      'because the work of getting through one is spent again at the next, and again ' +
      'after that.',
  ],
  pull: 'The defence was never the stone. It was the order the gates were in.',
};

const derivation = {
  num: '02',
  title: 'A city in plan, opened up',
  lede:
    'The city is the argument, not the decoration. No castle and no tower appear in the ' +
    'mark. What carries over is the plan, in four moves.',
  moves: [
    {
      n: '01',
      k: 'Seven walls',
      glyph: SEVEN_WALLS,
      v:
        'Seven walls climbing a spur of rock, one gate in each, and no gate on the same ' +
        'side as the one below it. Anyone climbing spent the whole ascent turning. Seen ' +
        'from above, that is a set of broken rings.',
    },
    {
      n: '02',
      k: 'Down to two',
      glyph: TWO_WALLS,
      v:
        'Seven walls is a drawing. Two is a mark. One band, broken twice, gates set ' +
        'opposite, which is the fewest breaks that still make a sequence rather than a hole.',
    },
    {
      n: '03',
      k: 'The climb',
      glyph: THE_CLIMB,
      v:
        'The inner edge steps in behind each gate, so the band is never a constant ring. ' +
        'That is the climb in plan, and it is also what keeps the shape from settling ' +
        'into a target.',
    },
    {
      n: '04',
      k: 'Close the ring',
      glyph: KEEP,
      v:
        'The wall comes back to full thickness and the ring closes, cut through on both ' +
        'diagonals. What survives of the corridor is the step on the inner edge — the ' +
        'climb, still legible in a shape that no longer has a way in.',
    },
  ],
};

const product = {
  num: '03',
  title: 'Opposed gates are the product',
  body: [
    'A change arrives at the first wall, gets checked, and comes out facing the wrong ' +
      'way for the second. It cannot run the walls in a straight line and it cannot skip ' +
      'one.',
    'That is Tirith, drawn as a floor plan. A plan arrives at the gate before anything ' +
      'is applied, every rule you have written gets its say on it in turn, and the change ' +
      'either comes out the far side or it does not move at all. A rule that passes does ' +
      'not excuse the one behind it. A rule that fails is not outvoted by the rest.',
    'Which is the refusal the city was built on. No single move gets you to the top, and ' +
      'nothing reaches production without walking the whole route.',
  ],
  notes: [
    {
      k: 'Why it is not the parent mark',
      v:
        'StackGuardian watches what reaches production. Tirith is the part that decides ' +
        'whether it should, so the mark inherits the family’s geometry and none of the ' +
        'parent’s shapes.',
    },
    {
      k: 'Why it has no up',
      v:
        'Rotational rather than mirror symmetry, which is why it holds at any angle and ' +
        'reads the same in an avatar as in a favicon.',
    },
  ],
};

/* --------------------------------------------------------------------------- */

function SectionHead({num, title, lede}) {
  return (
    <div className={styles.sectionHead}>
      <div className={styles.sectionLabel}>
        <span className={styles.sectionNum}>{num}</span>
        <Heading as="h2" className={styles.sectionTitle}>
          {title}
        </Heading>
      </div>
      {lede ? <p className={styles.sectionLede}>{lede}</p> : null}
    </div>
  );
}

export default function Logo() {
  return (
    <Layout
      title="The mark — the idea behind the Tirith logo"
      description={
        'Why the Tirith mark is a city seen in plan: seven walls reduced to two, gates ' +
        'set opposite, and a change that cannot reach the summit without passing all of them.'
      }>
      <main className={styles.page}>
        {/* ================= HERO ================= */}
        <header className={styles.hero}>
          <div className={styles.letterhead}>
            <TirithMark className={styles.letterheadMark} size={40} />
            <span className={styles.letterheadName}>Tirith</span>
            <span className={styles.letterheadRule} aria-hidden="true" />
            <span className={styles.letterheadNote}>The mark</span>
          </div>

          <Heading as="h1" className={styles.h1}>
            {hero.title}
            <span className={styles.h1Dim}>{hero.dim}</span>
          </Heading>

          <div className={styles.heroPlate}>
            <p className={styles.lede}>{hero.lede}</p>
            <div className={styles.heroMark}>
              <TirithMark className={styles.heroMarkGlyph} size={140} />
              <span className={styles.fieldLabel}>{hero.caption}</span>
            </div>
          </div>
        </header>

        {/* ================= 01 THE CITY ================= */}
        <section className={styles.section}>
          <SectionHead {...city} />
          {city.body.map((para) => (
            <p className={styles.prose} key={para.slice(0, 32)}>
              {para}
            </p>
          ))}
          <p className={styles.pull}>{city.pull}</p>
        </section>

        {/* ================= 02 DERIVATION ================= */}
        <section className={styles.section}>
          <SectionHead {...derivation} />
          <ol className={styles.moves}>
            {derivation.moves.map((move) => (
              <li key={move.n}>
                <div className={styles.moveGlyphBox}>
                  <Glyph glyph={move.glyph} className={styles.moveGlyph} />
                </div>
                <span className={styles.moveNum}>{move.n}</span>
                <h3>{move.k}</h3>
                <p>{move.v}</p>
              </li>
            ))}
          </ol>
        </section>

        {/* ================= 03 THE PRODUCT ================= */}
        <section className={styles.section}>
          <SectionHead {...product} />
          {product.body.map((para) => (
            <p className={styles.prose} key={para.slice(0, 32)}>
              {para}
            </p>
          ))}
          <dl className={styles.defs}>
            {product.notes.map((n) => (
              <div className={styles.def} key={n.k}>
                <dt>{n.k}</dt>
                <dd>{n.v}</dd>
              </div>
            ))}
          </dl>
        </section>

        <footer className={styles.colophon}>
          <span className={styles.colophonBrand}>
            <TirithMark className={styles.colophonMark} size={16} />
            Tirith · StackGuardian
          </span>
          <span>
            <Link to="/">Landing page</Link>
          </span>
          <span>
            <Link to="/learn/">Learn</Link>
          </span>
          <span>
            <Link to="/at-scale/">Tirith at scale</Link>
          </span>
          <span>
            <Link href="https://github.com/StackGuardian/tirith">Source</Link>
          </span>
        </footer>
      </main>
    </Layout>
  );
}
