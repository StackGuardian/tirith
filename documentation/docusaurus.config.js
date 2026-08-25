import {themes as prismThemes} from 'prism-react-renderer';

/*
 * PostHog is configured entirely from the environment, and nothing is
 * committed. An unset key means the client module never loads the script and
 * src/lib/analytics.js no-ops -- which is the correct behaviour for a local
 * `docusaurus start`, a fork's build and a contributor's checkout.
 */
const posthogKey = process.env.POSTHOG_KEY || '';
const posthogHost = process.env.POSTHOG_HOST || 'https://eu.i.posthog.com';

/*
 * The Fleet enquiry form posts straight to HubSpot from the browser, which is
 * what that endpoint is for -- a static site needs no backend. Both values are
 * environment-supplied: unset, the form disables itself and says why, rather
 * than posting into the void.
 */
const hubspotPortalId = process.env.HUBSPOT_PORTAL_ID || '';
const hubspotFormGuid = process.env.HUBSPOT_FORM_GUID || '';

const repo = 'https://github.com/StackGuardian/tirith';

/** @type {import('@docusaurus/types').Config} */
const config = {
  // Named `Tirith IaC Governance` rather than `Tirith` so that search results
  // and social cards distinguish this project from the unrelated Tirith
  // terminal-security tool and the unrelated `tirith` package on PyPI. The
  // navbar still reads `Tirith`, which is what the project is called.
  title: 'Tirith IaC Governance',
  tagline: 'Put governance in front of every Terraform or OpenTofu plan.',
  favicon: 'img/tirith.png',
  // Set the production url of your site here
  url: 'https://stackguardian.github.io',
  // Set the /<baseUrl>/ pathname under which your site is served.
  // This is a GitHub Pages project site, so it is served under /<projectName>/.
  baseUrl: '/tirith/',

  // GitHub pages deployment config.
  // If you aren't using GitHub pages, you don't need these.
  organizationName: 'StackGuardian', // Usually your GitHub org/user name.
  projectName: 'tirith', // Usually your repo name.
  onBrokenLinks: 'throw',
  onBrokenMarkdownLinks: 'warn',

  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  customFields: {
    posthogKey,
    posthogHost,
    hubspotPortalId,
    hubspotFormGuid,
  },

  clientModules: ['./src/clientModules/posthog.js'],

  presets: [
    [
      'classic',
      /** @type {import('@docusaurus/preset-classic').Options} */
      ({
        docs: {
          sidebarPath: './sidebars.js',
        },
        theme: {
          customCss: './src/css/custom.css',
        },
      }),
    ],
  ],

  themeConfig:
    /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
    ({
      image: 'img/tirith.png',
      navbar: {
        title: 'Tirith',
        hideOnScroll: true,
        // No href: the logo and title link to the site home, which is what a
        // reader clicking a site's own logo expects.
        //
        // The mark is Tirith's own, not StackGuardian's. This is an Apache-2.0
        // project that works with no account and no vendor relationship, and
        // flying the sponsor's logo as the page logo argues the opposite
        // before a word is read. StackGuardian is credited in the footer, and
        // its blue survives as the single accent colour.
        logo: {
          alt: 'Tirith',
          src: 'img/tirith.png',
        },
        items: [
          {
            type: 'docSidebar',
            sidebarId: 'TirithSidebar',
            position: 'left',
            label: 'Docs',
          },
          {to: '/learn', label: 'Learn', position: 'left'},
          {to: '/playground', label: 'Playground', position: 'left'},
          {to: '/policies', label: 'Policies', position: 'left'},
          {to: '/ai', label: 'AI', position: 'left'},
          {to: '/traction', label: 'Traction', position: 'left'},
          // Last in the left group, after Docs: the commercial route is
          // reachable but sits at the end of the OSS surfaces rather than
          // beside the primary action. `Star on GitHub` stays alone on the
          // right, so nothing competes with it.
          {to: '/fleet', label: 'Fleet governance', position: 'left'},
          {
            href: repo,
            label: 'Star on GitHub',
            position: 'right',
          },
        ],
      },
      footer: {
        style: 'light',
        links: [
          {
            title: 'Use it',
            items: [
              {label: 'Documentation', to: '/docs/getting-started-with-tirith/'},
              {label: 'CI integration', to: '/docs/tirith-usage/ci-integration/'},
              {label: 'Exit codes', to: '/docs/tirith-usage/exit-codes/'},
              {label: 'Platform mode (optional)', to: '/docs/tirith-usage/platform-check/'},
            ],
          },
          {
            title: 'Explore',
            items: [
              {label: 'Learn', to: '/learn'},
              {label: 'Playground', to: '/playground'},
              {label: 'Policies', to: '/policies'},
              {label: 'AI and MCP', to: '/ai'},
              {label: 'Traction', to: '/traction'},
              {label: 'Fleet governance', to: '/fleet'},
            ],
          },
          {
            title: 'Policies',
            items: [
              {label: 'Policy reference', to: '/docs/tirith-policies/tirith-policy-reference/'},
              {label: 'Worked examples', to: '/docs/tirith-policies/tirith-policy-examples/'},
              {label: 'Providers', to: '/docs/tirith-providers/providers-overview/'},
              // The builder is now a tab inside the Playground rather than a
              // separate destination, so this points there instead of leaving
              // the site. People search the footer for the word "builder".
              {label: 'Policy builder', to: '/playground'},
            ],
          },
          {
            title: 'Project',
            items: [
              {label: 'GitHub', href: repo},
              {label: 'Issues', href: `${repo}/issues`},
              {label: 'Contributing', href: `${repo}/blob/main/CONTRIBUTING.md`},
              {label: 'Governance', href: `${repo}/blob/main/GOVERNANCE.md`},
              {label: 'Maintainers', href: `${repo}/blob/main/MAINTAINERS.md`},
              {label: 'Security', href: `${repo}/blob/main/SECURITY.md`},
              {label: 'Roadmap', href: `${repo}/blob/main/ROADMAP.md`},
              {label: 'License', href: `${repo}/blob/main/LICENSE`},
            ],
          },
        ],
        copyright:
          'Tirith is Apache-2.0, maintained by community contributors with engineering support ' +
          'from StackGuardian.',
      },
      prism: {
        theme: prismThemes.github,
        darkTheme: prismThemes.dracula,
      },
    }),
};

export default config;
