/*
 * The Tirith mark -- candidate B, "Keep", from the logo canvas in docs/Tirith Logo.html.
 *
 * Inline rather than an <img> to the same file in static/img, for one reason: `fill` is
 * `currentColor`, so the mark inherits whatever ink its context is set in. On this page
 * that means it tracks `--tp-ink` through the light/dark token swap in index.module.css
 * without a second asset and without a theme hook. The static SVGs exist for the places
 * that can only take a URL -- the navbar logo, the favicon, the social card.
 *
 * Two paths, not one, and that is the shape's known weakness: the canvas notes Keep "can
 * read as two marks instead of one" at very small sizes. Nothing below renders it under
 * 16px for that reason.
 *
 * aria-hidden everywhere it is used: the wordmark or the page title always names Tirith
 * beside it, so announcing the mark again is noise for a screen reader.
 *
 * Do not hand-edit the path data. It is copied verbatim from the canvas; regenerate from
 * there if the mark changes.
 */

const PATHS = [
  'M45.1211 18.6412C46.2318 18.2149 47.4741 18.8466 47.6704 20.02C47.8869 21.3145 48 22.644 48 24C48 37.2548 37.2548 48 24 48C15.4856 48 8.00685 43.5661 3.74648 36.8814C3.10701 35.8781 3.60721 34.577 4.71797 34.1506L13.106 30.9303C14.2965 30.4732 15.6335 30.6112 16.7056 31.3017L22.917 35.3024C23.5765 35.7272 24.4235 35.7272 25.083 35.3024L32.083 30.7938C32.6546 30.4256 33 29.7923 33 29.1124V25.3558C33 24.1138 33.7654 23.0002 34.9249 22.5551L45.1211 18.6412Z',
  'M24 0C32.9579 0 40.7687 4.90815 44.8919 12.1816C45.46 13.1838 44.9485 14.4227 43.8729 14.8355L36.138 17.8044C34.625 18.3851 33 17.2682 33 15.6476C33 14.8832 32.4392 14.2344 31.6828 14.1237L26.8945 13.4234C24.9751 13.1426 23.0249 13.1426 21.1055 13.4234L16.7105 14.0662C15.7282 14.2099 15 15.0524 15 16.0452V23.1699C15 24.8259 13.9795 26.3107 12.4335 26.9042L3.09798 30.4879C2.02273 30.9007 0.813867 30.323 0.565312 29.1984C0.195368 27.5245 0 25.7851 0 24C0 10.7452 10.7452 0 24 0Z',
];

export default function TirithMark({size = 48, className}) {
  return (
    <svg
      className={className}
      width={size}
      height={size}
      viewBox="0 0 48 48"
      fill="currentColor"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
      focusable="false">
      {PATHS.map((d) => (
        <path key={d.slice(0, 24)} d={d} />
      ))}
    </svg>
  );
}
