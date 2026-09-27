import React from 'react';
import DocBreadcrumbs from '@theme-original/DocBreadcrumbs';
import CopyPageMenu from '@site/src/components/docs/CopyPageMenu';
import styles from './styles.module.css';

/**
 * The breadcrumb row, with the copy-page control on the other end of it.
 *
 * WHY HERE. The control has to sit at the top of the article column, level with something,
 * and the breadcrumbs are the only element already in that position. Wrapping this component
 * is a two-line swizzle; reaching the same place through DocItem/Layout would mean ejecting
 * the whole layout and owning Docusaurus's TOC and pagination logic forever.
 *
 * The original renders `null` on a page with breadcrumbs turned off. The row survives that:
 * `justify-content: space-between` with one child leaves the control on the right, which is
 * where it belongs anyway.
 */
export default function DocBreadcrumbsWrapper(props) {
  return (
    <div className={styles.row}>
      <DocBreadcrumbs {...props} />
      <CopyPageMenu />
    </div>
  );
}
