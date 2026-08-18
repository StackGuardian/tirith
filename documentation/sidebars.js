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
      label: "Using Tirith",
      items: [
        "tirith-usage/cli-reference",
        "tirith-usage/interactive-interface",
        "tirith-usage/exit-codes",
        "tirith-usage/ci-integration",
        "tirith-usage/platform-check",
        "tirith-usage/evaluating-policy-files",
        "tirith-usage/output-contract",
      ]
    },
    {
      type: "category",
      collapsed: true,
      label: "Tirith Policies",
      items: [
        "tirith-policies/tirith-create-first-policy",
        "tirith-policies/tirith-policy-structure",
        "tirith-policies/tirith-policy-reference",
        "tirith-policies/tirith-policy-error-tolerance",
        "tirith-policies/tirith-policy-conditions",
        "tirith-policies/tirith-policy-variables",
        "tirith-policies/tirith-policy-cookbook",
        // "tirith-policies/tirith-policy-examples"
      ]
    },
    {
      type: "category",
      collapsed: true,
      label: "Providers",
      items: [
        "tirith-providers/providers-overview",
        "tirith-providers/terraform-plan-provider",
        "tirith-providers/infracost-provider",
        "tirith-providers/json-provider",
        "tirith-providers/kubernetes-provider",
        "tirith-providers/sg-workflow-provider",
      ]
    },
    {
      type: "category",
      collapsed: true,
      label: "Reference",
      items: [
        "tirith-reference/evaluators",
        "tirith-reference/eval-expressions",
      ]
    },
  ],
};
