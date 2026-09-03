import Link from '@docusaurus/Link';
import useBaseUrl from '@docusaurus/useBaseUrl';
import {useLocation} from '@docusaurus/router';

import TirithMark from '../brand/TirithMark';

/*
 * The end of the sheet, and the site's only footer navigation.
 *
 * One component rather than a copy per page. It was five copies, and they had already
 * drifted into four different link sets: the landing page listed At scale, Origins, Source
 * and Slack; At scale listed a Skills link to a hidden route; Origins and Roadmap each had
 * a different three; and Learn had no footer at all. A footer nav that differs per page is
 * worse than none, because a reader learns it and then it moves.
 *
 * Styles arrive as a prop rather than from a stylesheet of their own. Every page module
 * already carries `.colophon`, `.colophonBrand` and `.colophonMark`, and passing the
 * calling page's module in keeps those definitions where they are, so this change is
 * markup deduplication and not a CSS migration.
 *
 * ORDER
 *   Origins first, sitting directly against the mark and the name in the brand span beside
 *   it. It is the one item whose subject is that mark, so the colophon reads as the name,
 *   then where the name came from, before it becomes a menu.
 *
 *   Then the route through the product, matching the navbar: Home, Learn, Docs. Then
 *   Roadmap, which the navbar deliberately omits because it is not a step toward installing
 *   anything. Then the project: Source and Slack.
 *
 *   At scale is last, on its own. It is the commercial page, and the footer should not put
 *   a sales route in front of the open-source ones any more than the navbar does.
 */

const REPO = 'https://github.com/StackGuardian/tirith';
const SLACK =
  'https://join.slack.com/t/stackguardian-ol78820/shared_invite/' +
  'zt-2ksag36j9-OjmXqQmyXudgYrV6FmesIQ';

const LINKS = [
  {label: 'Origins', to: '/origins/'},
  {label: 'Home', to: '/'},
  {label: 'Learn', to: '/learn/'},
  {label: 'Skills', to: '/skills/'},
  {label: 'Docs', to: '/docs/getting-started-with-tirith/'},
  {label: 'Roadmap', to: '/roadmap/'},
  {label: 'Source', href: REPO},
  {label: 'Slack', href: SLACK},
  {label: 'Tirith at scale', to: '/at-scale/'},
];

/**
 * The link to the page you are already on is dropped, whichever page that is. It was a
 * `home` prop the caller had to remember to set, which only ever solved it for the landing
 * page and left Learn's footer offering Learn. Comparing against the current route solves
 * it for all of them and removes a prop that could be passed wrongly.
 *
 * @param styles  The calling page's CSS module. Must define colophon, colophonBrand and
 *                colophonMark.
 */
export default function Colophon({styles}) {
  const {pathname} = useLocation();
  // Hoisted: useBaseUrl is a hook and must not be called inside the map below.
  const base = useBaseUrl('/');
  /*
   * Both sides are stripped of a trailing slash before comparing. During the server render
   * `pathname` arrives without one (`/tirith/learn`) while the link builds with one
   * (`/tirith/learn/`), so a raw comparison matched only the site root, and every page
   * except the landing page shipped a footer link to itself.
   */
  const trim = (v) => (v.length > 1 ? v.replace(/\/+$/, '') : v);
  const here = (to) => trim(`${base}${to.replace(/^\//, '')}`) === trim(pathname);

  return (
    <footer className={styles.colophon}>
      <span className={styles.colophonBrand}>
        <TirithMark className={styles.colophonMark} size={16} />
        Tirith · StackGuardian
      </span>
      <span>Apache-2.0</span>
      {LINKS.filter((l) => !(l.to && here(l.to))).map((l) => (
        <span key={l.label}>
          {l.to ? (
            <Link to={l.to}>{l.label}</Link>
          ) : (
            <Link href={l.href}>{l.label}</Link>
          )}
        </span>
      ))}
    </footer>
  );
}
