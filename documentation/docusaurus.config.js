import {themes as prismThemes} from 'prism-react-renderer';

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: 'Tirith',
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
      // Replace with your project's social card
      image: 'img/docusaurus-social-card.jpg',
      navbar: {
        title: 'Tirith',
        hideOnScroll: true,    
        // No href: the logo and title link to the site home, which is what a
        // reader clicking a site's own logo expects. It used to open the policy
        // builder in a new tab, which left no way back to the docs home.
        logo: {
          alt: 'StackGuardian logo',
          src: 'img/sg-icon.png',
        },
        items: [
          {
            type: 'docSidebar',
            sidebarId: 'TirithSidebar',
            position: 'left',
            label: 'Docs',
          },
          {
            href: 'https://tirith-policy-builder.vercel.app/',
            label: 'Policy Builder',
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




