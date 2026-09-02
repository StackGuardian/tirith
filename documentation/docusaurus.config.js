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
    /*
     * Structured data, on every route.
     *
     * Two graph nodes and no more. SoftwareApplication is the one an answer engine reads to
     * decide what this is, what it costs and what it runs on, and every field below is
     * checkable against the repository: the licence, the price, the language floor from
     * setup.py's python_requires, and the version from setup.py. SoftwareSourceCode carries
     * the repository so a citation can point at the code rather than only the docs.
     *
     * `offers` at price 0 is not marketing. Without it a crawler has no statement either
     * way, and "is Tirith free" is a question people actually ask an assistant.
     *
     * Deliberately absent: aggregateRating and any review markup. There are no ratings, and
     * inventing them is both a policy violation and the fastest way to lose a rich result.
     */
    {
      tagName: 'script',
      attributes: {type: 'application/ld+json'},
      innerHTML: JSON.stringify({
        '@context': 'https://schema.org',
        '@graph': [
          {
            '@type': 'SoftwareApplication',
            '@id': 'https://stackguardian.github.io/tirith/#software',
            name: 'Tirith',
            alternateName: 'Tirith IaC Governance',
            applicationCategory: 'DeveloperApplication',
            applicationSubCategory: 'Infrastructure as Code policy engine',
            operatingSystem: 'Linux, macOS, Windows',
            softwareVersion: '1.2.0',
            softwareRequirements: 'Python 3.8 or newer',
            license: 'https://www.apache.org/licenses/LICENSE-2.0',
            url: 'https://stackguardian.github.io/tirith/',
            downloadUrl: 'https://github.com/StackGuardian/tirith',
            codeRepository: 'https://github.com/StackGuardian/tirith',
            description:
              'An Apache-2.0 policy gate for infrastructure as code. Tirith evaluates the ' +
              'OpenTofu or Terraform plan a pipeline already produces against declarative ' +
              'JSON policies and returns an exit code the pipeline can gate on. Runs ' +
              'locally or in any CI, on your own runner, with no account.',
            featureList: [
              'Evaluates OpenTofu and Terraform plan JSON',
              'Policies are JSON documents, not code',
              'Thirteen condition types',
              'Reads Kubernetes manifests, Infracost breakdowns and any JSON or YAML document',
              'Exit-code contract that separates a policy failure from an engine error',
              'Reports a check that could not run as unevaluated rather than as a pass',
              'No account and no network call in local mode',
            ],
            offers: {
              '@type': 'Offer',
              price: '0',
              priceCurrency: 'USD',
            },
            author: {'@id': 'https://www.stackguardian.io/#org'},
          },
          {
            '@type': 'SoftwareSourceCode',
            '@id': 'https://github.com/StackGuardian/tirith#code',
            name: 'Tirith',
            codeRepository: 'https://github.com/StackGuardian/tirith',
            programmingLanguage: 'Python',
            license: 'https://www.apache.org/licenses/LICENSE-2.0',
            about: {'@id': 'https://stackguardian.github.io/tirith/#software'},
          },
          {
            '@type': 'Organization',
            '@id': 'https://www.stackguardian.io/#org',
            name: 'StackGuardian',
            url: 'https://www.stackguardian.io/',
          },
        ],
      }),
    },
    /*
     * A machine-discoverable pointer to llms.txt. There is no registered rel value for it
     * yet, so this is a convention rather than a standard, and it costs one line. It matters
     * more here than on most sites: a project subpath means /llms.txt at the host root is
     * not ours to publish, so a crawler that only probes the root will never find it.
     */
    {
      tagName: 'link',
      attributes: {
        rel: 'alternate',
        type: 'text/plain',
        title: 'llms.txt',
        href: 'https://stackguardian.github.io/tirith/llms.txt',
      },
    },
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
        /*
         * Skills is hidden for now, not deleted. src/pages/skills.js and its stylesheet
         * are untouched; this line is the only thing keeping the route out of the build,
         * so restoring the page is deleting the 'skills.js' entry below and putting the
         * navbar item back.
         *
         * Excluding here rather than renaming the file to _skills.js -- the other way to
         * hide a page -- keeps the filename matching the route it will return to, and puts
         * the decision somewhere a reader of the config can see it.
         *
         * GlobExcludeDefault is repeated because supplying `exclude` replaces the plugin's
         * defaults rather than adding to them, and dropping them would start building
         * _partials and test files as pages.
         */
        pages: {
          exclude: [
            '**/_*.{js,jsx,ts,tsx,md,mdx}',
            '**/_*/**',
            '**/*.test.{js,jsx,ts,tsx}',
            '**/__tests__/**',
            'skills.js',
          ],
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
          // Names the destination, not the picture. The anchor takes its accessible name
          // from this, so a screen reader announced "Tirith, link" and said nothing about
          // where the link goes, which is the same gap the hover state had visually.
          alt: 'Tirith, home',
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
          // Hidden with the page itself -- see the `pages.exclude` note above. Kept
          // here so restoring the route is uncommenting rather than rewriting.
          // {
          //   to: '/skills/',
          //   label: 'Skills',
          //   position: 'left',
          // },
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
