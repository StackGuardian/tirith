# require-private-registry-modules: not expressible

**What it enforces.** Every `module` call's `source` starts with `app.terraform.io/acme/`.

**What Tirith cannot see.** Module calls are configuration, read by Sentinel through `tfconfig/v2`.
A Terraform plan's `resource_changes` records resources, not the modules that declared them, and
Tirith's plan provider reads only `resource_changes` and `configuration.provider_config`. There is
no attribute, on any resource, that carries the module source.

**What would change that.** Issue #348 proposes a `terraform_code` provider that reads HCL. Until
it exists, keep this policy in Sentinel or enforce it where modules are resolved.

No `policy.json` is shipped for this example, on purpose. A policy that checked something adjacent,
say that every resource address contains `module.`, would pass CI and enforce nothing.
