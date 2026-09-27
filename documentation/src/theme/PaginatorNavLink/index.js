import React from 'react';
import Link from '@docusaurus/Link';
import clsx from 'clsx';

/**
 * Previous / next, with the arrow on the side it points to.
 *
 * Two things changed when the documentation was restyled. The arrows were filled `#666666`,
 * a literal grey that stayed grey on a dark page, so they are `currentColor` now and inherit
 * the label's colour in both themes. And the sizing that used to be inline on the label and
 * the sublabel now lives in `src/css/docs.css`, so the pagination can be restyled without
 * editing a component, which is the point of having a stylesheet.
 */

const ARROW = {
  prev: 'M8.53033 12.7803C8.23744 13.0732 7.76256 13.0732 7.46967 12.7803L3.2197 8.53033C2.9268 8.23744 2.9268 7.76256 3.2197 7.46967L7.46967 3.2197C7.76256 2.9268 8.23744 2.9268 8.53033 3.2197C8.82322 3.5126 8.82322 3.9874 8.53033 4.2803L5.5607 7.25L13 7.25C13.4142 7.25 13.75 7.58579 13.75 8C13.75 8.41421 13.4142 8.75 13 8.75H5.5607L8.53033 11.7197C8.82322 12.0126 8.82322 12.4874 8.53033 12.7803Z',
  next: 'M8.21967 3.21967C8.51256 2.92678 8.98744 2.92678 9.28033 3.21967L13.5303 7.46967C13.8232 7.76256 13.8232 8.23744 13.5303 8.53033L9.28033 12.7803C8.98744 13.0732 8.51256 13.0732 8.21967 12.7803C7.92678 12.4874 7.92678 12.0126 8.21967 11.7197L11.1893 8.75H3.75C3.33579 8.75 3 8.41421 3 8C3 7.58579 3.33579 7.25 3.75 7.25H11.1893L8.21967 4.28033C7.92678 3.98744 7.92678 3.51256 8.21967 3.21967Z',
};

function Arrow({dir}) {
  return (
    <svg width="14" height="14" viewBox="0 0 16 16" fill="none" aria-hidden="true">
      <path fillRule="evenodd" clipRule="evenodd" d={ARROW[dir]} fill="currentColor" />
    </svg>
  );
}

function PaginatorNavLink({permalink, title, isNext}) {
  return (
    <Link className="pagination-nav__link" to={permalink}>
      <div
        className={clsx('pagination-nav__item', {
          'pagination-nav__item--next': isNext,
          'pagination-nav__item--prev': !isNext,
        })}>
        <div className="pagination-nav__sublabel">
          {!isNext && <Arrow dir="prev" />}
          {isNext ? 'Next' : 'Previous'}
          {isNext && <Arrow dir="next" />}
        </div>
        <div className="pagination-nav__label">{title}</div>
      </div>
    </Link>
  );
}

export default PaginatorNavLink;
