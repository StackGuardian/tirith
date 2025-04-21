module.exports = {
  TirithSidebar: [
    {
      type: "doc",
      label: "Getting Started",
      id: "getting-started-with-tirith",
    },
    {
      type: "category",
      collapsed: true,
      label: "Setup Tirith",
      items: [
        'tirith-installation/quick-installation',
        'tirith-installation/developer-mode-installation',
        'tirith-installation/manual-installation'
      ]
    },
    {
      type: "category",
      collapsed: true,
      label: "Tirith Policies",
      items: [
        "tirith-policies/tirith-create-first-policy",
        "tirith-policies/tirith-policy-structure",
        "tirith-policies/tirith-policy-error-tolerance",
        "tirith-policies/tirith-policy-conditions",
        "tirith-policies/tirith-policy-variables",
        // "tirith-policies/tirith-policy-examples"
      ]
    },
  ],
};