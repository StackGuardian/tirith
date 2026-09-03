/*
 * Geometry for the logo story page, lifted verbatim from the canvas in
 * docs/Tirith Logo.html. Do not hand-edit the path data.
 *
 * Two shapes of glyph live here and they are not interchangeable:
 *
 *   `strokes` -- the three derivation diagrams. Open arcs, drawn with `fill: none` and a
 *     stroke whose width is part of the drawing. Any bulk rewrite of `width="..."` over
 *     this file will also hit `stroke-width` and turn every one of them into a solid
 *     black disc, which is exactly what happened once while extracting them.
 *
 *   `fills` -- the three candidate marks. Closed shapes, no stroke.
 *
 * viewBox travels with each glyph rather than being assumed, because the canvas does not
 * draw them all on the same box.
 *
 * Only the shipped mark and the three derivation diagrams live here. The canvas also holds
 * two forms that were drawn and not chosen; they were removed from this file when the page
 * stopped showing them. Re-extract from the canvas if they are ever wanted again.
 */

export const SEVEN_WALLS = {
  "viewBox": "0 0 48 48",
  "strokes": [
    {
      "d": "M40.99 36.34A21 21 0 0 1 3.62 18.92",
      "w": 1.7
    },
    {
      "d": "M7.01 11.66A21 21 0 0 1 44.38 29.08",
      "w": 1.7
    },
    {
      "d": "M14.36 37.27A16.4 16.4 0 0 1 27.97 8.09",
      "w": 1.7
    },
    {
      "d": "M33.64 10.73A16.4 16.4 0 0 1 20.03 39.91",
      "w": 1.7
    },
    {
      "d": "M33.22 30.70A11.4 11.4 0 0 1 12.94 21.24",
      "w": 1.7
    },
    {
      "d": "M14.78 17.30A11.4 11.4 0 0 1 35.06 26.76",
      "w": 1.7
    },
    {
      "d": "M20.24 29.18A6.4 6.4 0 0 1 25.55 17.79",
      "w": 1.7
    },
    {
      "d": "M27.76 18.82A6.4 6.4 0 0 1 22.45 30.21",
      "w": 1.7
    }
  ]
};

export const TWO_WALLS = {
  "viewBox": "0 0 48 48",
  "strokes": [
    {
      "d": "M40.31 31.61A18 18 0 0 1 7.69 31.61",
      "w": 5.2
    },
    {
      "d": "M7.69 16.39A18 18 0 0 1 40.31 16.39",
      "w": 5.2
    }
  ]
};

export const THE_CLIMB = {
  "viewBox": "0 0 48 48",
  "strokes": [
    {
      "d": "M41.76 32.28A19.6 19.6 0 0 1 24.00 43.60L24.00 39.40A15.4 15.4 0 0 1 10.04 30.51",
      "w": 5.2
    },
    {
      "d": "M6.24 15.72A19.6 19.6 0 0 1 24.00 4.40L24.00 8.60A15.4 15.4 0 0 1 37.96 17.49",
      "w": 5.2
    }
  ]
};

export const KEEP = {
  "viewBox": "0 0 48 48",
  "fills": [
    "M45.1211 18.6412C46.2318 18.2149 47.4741 18.8466 47.6704 20.02C47.8869 21.3145 48 22.644 48 24C48 37.2548 37.2548 48 24 48C15.4856 48 8.00685 43.5661 3.74648 36.8814C3.10701 35.8781 3.60721 34.577 4.71797 34.1506L13.106 30.9303C14.2965 30.4732 15.6335 30.6112 16.7056 31.3017L22.917 35.3024C23.5765 35.7272 24.4235 35.7272 25.083 35.3024L32.083 30.7938C32.6546 30.4256 33 29.7923 33 29.1124V25.3558C33 24.1138 33.7654 23.0002 34.9249 22.5551L45.1211 18.6412Z",
    "M24 0C32.9579 0 40.7687 4.90815 44.8919 12.1816C45.46 13.1838 44.9485 14.4227 43.8729 14.8355L36.138 17.8044C34.625 18.3851 33 17.2682 33 15.6476C33 14.8832 32.4392 14.2344 31.6828 14.1237L26.8945 13.4234C24.9751 13.1426 23.0249 13.1426 21.1055 13.4234L16.7105 14.0662C15.7282 14.2099 15 15.0524 15 16.0452V23.1699C15 24.8259 13.9795 26.3107 12.4335 26.9042L3.09798 30.4879C2.02273 30.9007 0.813867 30.323 0.565312 29.1984C0.195368 27.5245 0 25.7851 0 24C0 10.7452 10.7452 0 24 0Z"
  ]
};

