/*
 * Renders one glyph from src/data/logoStory.js.
 *
 * Both kinds paint in `currentColor` rather than the canvas's `#111318`, so a glyph
 * follows whatever ink its section is set in and the whole page inverts with the theme
 * from the token block alone.
 *
 * Sized through CSS (a `className` and a `--glyph` size), never through width/height
 * attributes: `stroke-width` is part of the derivation drawings, and attribute rewriting
 * is how it gets destroyed.
 */

export default function Glyph({glyph, className}) {
  const {viewBox, strokes, fills} = glyph;

  return (
    <svg
      className={className}
      viewBox={viewBox}
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
      focusable="false">
      {fills
        ? fills.map((d) => <path key={d.slice(0, 24)} d={d} fill="currentColor" />)
        : strokes.map(({d, w}) => (
            <path
              key={d.slice(0, 24)}
              d={d}
              fill="none"
              stroke="currentColor"
              strokeWidth={w}
              strokeLinecap="round"
            />
          ))}
    </svg>
  );
}
