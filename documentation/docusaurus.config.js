import {themes as prismThemes} from 'prism-react-renderer';

/*
 * PostHog is configured entirely from the environment, and nothing is committed. An
 * unset key never loads the script and src/analytics.js no-ops -- which is the correct
 * behaviour for a local `docusaurus start`, a fork's build and a contributor's checkout.
 * Only .github/workflows/deploy_docs.yml supplies a key, so the published site is the
 * one place anything is reported.
 */
const posthogKey = process.env.POSTHOG_KEY || '';
const posthogHost = process.env.POSTHOG_HOST || 'https://eu.i.posthog.com';

/*
 * The At scale enquiry form posts straight to HubSpot from the browser, which is what that
 * endpoint is for -- a static site needs no backend. Neither value is a secret: a portal
 * id and form guid are public by design, since the browser sends them. They are supplied
 * from the environment rather than committed so a fork's build does not point at
 * StackGuardian's CRM. Unset, the form disables itself and says why.
 */
const hubspotPortalId = process.env.HUBSPOT_PORTAL_ID || '';
const hubspotFormGuid = process.env.HUBSPOT_FORM_GUID || '';

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: 'Tirith',
  favicon: 'img/tirith-mark.svg',
  url: 'https://stackguardian.github.io',
  baseUrl: '/tirith/',
  organizationName: 'StackGuardian',
  projectName: 'tirith',
  onBrokenLinks: 'throw',
  onBrokenMarkdownLinks: 'warn',
  /*
   * The three faces the design is built on, loaded for every route.
   *
   * They used to be a <Head> block repeated inside each landing page, which meant the one
   * route nobody could add a <Head> to -- the docs -- never got them. The shared navbar was
   * the visible symptom: identical CSS on every page, but Martian Mono never arrived on
   * /docs, so the bar fell back to the system mono and rendered about 7% narrower there
   * ("Learn" at 60.8px against 65.7px everywhere else). It read as a smaller font size,
   * and it was not one.
   *
   * Loading them here rather than per page does not change which family anything uses --
   * the docs body and headings still take Infima's system stack. It only makes the fonts
   * the navbar already asks for actually available on every route.
   */
  headTags: [
    {
      tagName: 'link',
      attributes: {rel: 'preconnect', href: 'https://fonts.googleapis.com'},
    },
    {
      tagName: 'link',
      attributes: {
        rel: 'preconnect',
        href: 'https://fonts.gstatic.com',
        crossorigin: 'anonymous',
      },
    },
  ],

  stylesheets: [
    'https://fonts.googleapis.com/css2?family=Martian+Mono:wdth,wght@75..112.5,100..800&family=IBM+Plex+Sans:ital,wght@0,400;0,500;0,600;0,700;1,400;1,500;1,600;1,700&family=JetBrains+Mono:ital,wght@0,100..800;1,100..800&display=swap',
  ],

  customFields: {
    posthogKey,
    posthogHost,
    hubspotPortalId,
    hubspotFormGuid,
  },

  clientModules: ['./src/clientModules/posthog.js'],

  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  presets: [
    [
      'classic',
      /** @type {import('@docusaurus/preset-classic').Options} */
      ({
        docs: {
          sidebarPath: './sidebars.js',
        },
        blog: false,
        theme: {
          customCss: './src/css/custom.css',
        },
      }),
    ],
  ],

  themeConfig:
    /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
    ({
      image: 'img/tirith-social-card.png',
      navbar: {
        // No `title`. The logo below is the full lockup -- mark plus the "Tirith"
        // wordmark drawn as outlines -- so a text title beside it sets the name twice,
        // once in the drawn face and once in the theme's.
        hideOnScroll: true,
        logo: {
          alt: 'Tirith',
          // Two files rather than one theme-reactive SVG: the swap is driven by the
          // site's own theme toggle, which a `prefers-color-scheme` query inside the
          // file cannot observe. `src` carries the dark ink for the light theme,
          // `srcDark` the reversed cut.
          src: 'img/tirith-lockup.svg',
          srcDark: 'img/tirith-lockup-dark.svg',
          height: 28,
        },
        // Left is the route through the product: Learn, Skill, then Docs last. Install,
        // Providers and Tirith UI used to sit here as individual deep links into the
        // sidebar; they are reachable from Docs itself, and six left-hand items made the
        // bar read as a sitemap rather than a route.
        //
        // At scale sits on the right, away from that route: it is the commercial page, and
        // the left group should not be selling anything.
        items: [
          {
            to: '/learn/',
            label: 'Learn',
            position: 'left',
          },
          {
            to: '/skills/',
            label: 'Skills',
            position: 'left',
          },
          {
            type: 'docSidebar',
            sidebarId: 'TirithSidebar',
            position: 'left',
            label: 'Docs',
          },
          {
            to: '/at-scale/',
            label: 'Tirith at scale',
            position: 'right',
          },
          {
            href: 'https://github.com/StackGuardian/tirith',
            label: 'GitHub',
            position: 'right',
          },
        ],
      },
      prism: {
        theme: prismThemes.github,
        darkTheme: prismThemes.dracula,
      },
    }),
};

export default config;
