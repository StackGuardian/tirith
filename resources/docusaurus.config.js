module.exports = {
  title: "StackGuardian Guardry",
  favicon: "img/favicon.ico",
  url: "https://beta.stackguardian.io",
  baseUrl: "/resources/guardry",
  onBrokenLinks: "throw",
  onBrokenMarkdownLinks: "warn",
  tagline: "Easy to use policy framework for Configuration as Code.",
  organizationName: "tandlabs",
  projectName: "guardry",
  themeConfig: {
    hideableSidebar: false,
    colorMode: {
      defaultMode: 'light',
      disableSwitch: true,
      respectPrefersColorScheme: true,
      switchConfig: {
        darkIcon: '🌙',
        lightIcon: '\u2600',
        // React inline style object
        // see https://reactjs.org/docs/dom-elements.html#style
        darkIconStyle: {
          marginLeft: '2px',
        },
        lightIconStyle: {
          marginLeft: '1px',
        },
      },
    },
    navbar: {
      title: "StackGuardian Guardry",
      logo: {
        alt: "stackguardian guardry logo",
        src: "img/logo.svg",
      },
      items: [
        {
          type: "doc",
          // to: "docs",
          label: "Docs",
          docId: "core/introduction",
          position: "left",
        },
        {
          type: "doc",
          // to: "apis",
          label: "CLI",
          docId: "cli/overview",
          position: "left",
        },
        {
          // to: "community",
          type: "doc",
          label: "Community",
          docId: "community/overview",
          position: "left",
        },
        {
          href: 'https://stackguardian-users.slack.com/',
          label: "Slack",
          position: "right",
        },
        {
          // to: 'blog',
          href: 'https://stackguardian.io/blog/',
          label: 'Blog',
          position: 'right'
        },
        {
          href: "https://github.com/stackguardian/",
          label: "GitHub",
          position: "right",
        },
      ],
    },
    footer: {
      style: "dark",
      links: [
        {
          title: "Resources",
          items: [
            {
              label: "Docs",
              to: "docs/introduction",
            },
            {
              label: "CLI",
              to: "docs/cli/overview/",
            },
          ],
        },
        {
          title: "Community",
          items: [
            {
              label: "Stack Overflow",
              href: "https://stackoverflow.com/questions/tagged/stackguardian",
            },
            {
              label: "Slack",
              href: "https://stackguardian-users.slack.com/",
            },
            {
              label: "Twitter",
              href: "https://twitter.com/stackguardian",
            },
          ],
        },
        {
          title: "More",
          items: [
            {
              label: "Landing",
              href: 'https://stackguardian.io/'
            },
            {
              label: "Blog",
              href: 'https://stackguardian.io/blog/'
            },
            {
              label: "GitHub",
              href: "https://github.com/tandlabs/",
            },
          ],
        },
      ],
      copyright: `Made with ❤️ + 💦 + ☕️ + Docusaurus`,
    },
  },
  presets: [
    [
      "@docusaurus/preset-classic",
      {
        docs: {
          sidebarPath: require.resolve("./sidebars.js"),
        },
        blog: {
          showReadingTime: true,
        },
        theme: {
          customCss: require.resolve("./src/css/custom.css"),
        },
      },
    ],
  ],
};
