# Getting started with Tirith

Source: https://stackguardian.github.io/tirith/docs/getting-started-with-tirith/
Summary: Learn how Tirith simplifies security, governance, and compliance for infrastructure-as-code platforms.

[NOTE] New — `tirith ui`, an interactive interface. In beta, and we want your input.

Explore a failing evaluation down to the resource that caused it, assemble policies from a form, and
experiment in a playground with worked examples. Install it with
`pip install 'py-tirith[tui] @ git+https://github.com/StackGuardian/tirith.git'` and run
`tirith ui` — see
[the interactive interface](tirith-usage/interactive-interface.md).

It is new, so the rough edges are still being found. Tell us what is confusing, what is missing, or
what you would rather it did:
[open an issue](https://github.com/StackGuardian/tirith/issues/new/choose).
Nothing about the existing CLI changes.

Tirith is a robust policy framework designed to automate and enforce security, governance, and compliance across infrastructure-as-code (IaC) platforms like Terraform, CloudFormation, and Kubernetes. It simplifies policy creation and management, ensuring infrastructure adheres to industry regulations and best practices.

## Key Benefits of Tirith

- **Centralized Policy Management :** Tirith offers a unified platform for centralized policy management, reducing duplication and streamlining governance across multiple infrastructures and environments. This ensures consistent application of policies, regardless of the platform being used.

- **Simplified Policy Creation :** Tirith’s [intuitive, no-code interface](https://tirith-policy-builder.vercel.app/) and declarative language simplify policy authoring, enabling users to define and manage policies effortlessly. This removes the need for deep technical expertise, allowing teams to quickly align with evolving regulatory requirements.

- **Proactive Compliance Enforcement :** With seamless CI/CD pipeline integration, Tirith proactively enforces compliance by running pre-deployment checks. This ensures non-compliant infrastructure configurations are detected and resolved before deployment, enhancing operational efficiency.

- **Integration with Popular Tools :** Tirith integrates with popular infrastructure-as-code (IaC) tools like Terraform, CloudFormation, and Kubernetes, making it easy to incorporate into your existing workflows.

- **Enhanced Security :** By enforcing consistent policies across your infrastructure, Tirith helps to reduce the risk of security vulnerabilities and compliance violations.
