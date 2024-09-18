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
      label: "Installation",
      items: [
        "install-tirith-on-linux",
        "install-tirith-on-windows",
        "install-tirith-on-mac"
      ]
    },
    {
      type: "category",
      collapsed: true,
      label: "Tirith Policies",
      items: [
        "tirith-policy-structure",
        "tirith-policy-error-tolerance",
        "tirith-policy-conditions",
        "tirith-policy-variables",
        "tirith-policy-examples"
      ]
    },
  ],
};