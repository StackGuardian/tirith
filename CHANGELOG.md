# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).




## [Unreleased]

### Changed — verdicts

Read this section before upgrading: it changes what some policies report, on inputs where the
previous answer was wrong.

- `core`: a tolerated provider miss no longer erases a failure recorded by an earlier resource.
  A check whose provider returned several results — one that violated the policy and one it could
  not read, tolerated by `error_tolerance` — reported the *skip* if the tolerated one came last,
  because the skip marker overwrote the verdict unconditionally. The verdict therefore depended on
  the order the provider happened to emit resources. It now reports the failure regardless of
  order. Under `--fail-on-error` the affected runs move from exit `1` to exit `3`: previously a
  real violation could be reported as "nothing was checked". Pass-and-skip is unchanged and still
  reports skipped, in both orders.

### Added

- Running many policies in one invocation. `-policy-path` accepts a **directory**, walked
  recursively for `*.json`, and `--pack NAME` runs a policy pack bundled with Tirith
  (`--list-packs` lists them). Both are repeatable and combine, so bundled and local rules produce
  one summary and one exit code. A single policy *file* is untouched — same result document, same
  exit codes.
- The first bundled pack: **`terraform-baseline`**, 104 baseline security and configuration checks
  for Terraform plans across AWS, Azure, GCP, Kubernetes and several smaller providers. Every one
  is verified end to end in CI against a compliant and a violating document, so an engine change
  cannot silently turn a check into a no-op.
- A set run reports `passed / failed / skipped / errored` and prints failures in full. **Skipped is
  not a failure**: a policy only applies to plans that touch the resource it names, so most of a
  large pack skips on any given plan, and counting that as an error would make every pack run red.
  With `--fail-on-error`, a set exits `3` if any policy failed, `0` if none failed and at least one
  reached a verdict, and `1` if nothing reached one.
- `tirith ui`: an interactive interface with three tabs.
  - **Explorer** — read an evaluation's results down to the resource behind each one. The result
    document has always carried the resource address, the planned action and the before/after
    values; the pretty printer prints only the message, so this detail was reachable only by
    piping `--json` into another tool. Opens on the first failure, names replacements by their
    ordering (destroy-first and create-first mean different things), and shows the attributes
    that changed, flagging the ones that are unknown until apply.
  - **Builder** — assemble a policy from a form whose fields follow the chosen provider and
    operation. Values keep their JSON types, so `Equals: true` and `Equals: "true"` stay
    distinguishable.
  - **Playground** — edit a policy and an input side by side and watch the verdict move, with
    five worked examples that mostly fail on purpose and explain why.
  - `--serve` runs the same interface over HTTP for a browser.
- Optional extra: `pip install 'py-tirith[tui]'`. Not a hard dependency — the interface needs
  Python 3.9 while tirith supports 3.8, and using tirith as a CI gate should stay
  dependency-light. Without it, `tirith ui` prints how to install it and exits 1.
- A policy validator behind the interface, reporting the mistakes that are otherwise silent:
  a provider argument the operation does not read, an id referenced in `eval_expression` but
  never defined, a single `&` where `&&` was meant, an evaluator that does not exist.
- `core`: Provider results can now carry a `context` object saying where the evaluated value came
  from. It is rendered into the front of the result `message` and kept as structured fields in the
  result document.
- `terraform_plan`: Result messages now name the resource address, its planned action and the
  attribute being evaluated, e.g. ``[aws_s3_bucket.example (create)] acl: `"public-read"` is not
  equal to `"private"` `` instead of just ``` `"public-read"` is not equal to `"private"` ``. The
  Explorer above reads the same detail out of the result document; this puts it in the message, so
  a CI log is legible without it.

### Changed
- `terraform_plan`: A wildcard attribute now reports the index it resolved to
  (`ebs_block_device.0.tags.application_acronym`), so results coming from the same resource can be
  told apart.
- `terraform_plan`: An "attribute is not found" error now names the resource it is about, instead
  of repeating the same text once per resource — with `terraform_resource_type: "*"` it was emitted
  once per resource with identical text.
- `core`: "Could not find input value" now names the provider arguments that produced no value.

### Notes
- The local evaluation surface is untouched. `ui` is dispatched before the flat parser, like
  `platform`, so `--json` output remains byte-identical to the golden file.
- No new runtime dependencies for anyone who does not install the extra.
- Only `terraform_plan` attaches a result `context`. The other providers return results without
  it, so their messages and result documents are unchanged.

## [1.2.0] - 2026-08-03

### Added
- `tirith platform check`: run an organization's policies against a plan, state or arbitrary JSON
  document from CI or a laptop. Masks the document locally, packs it with the terraform source into
  an archive, uploads it, creates a StackGuardian run, polls it and reports the verdict as JSON
  and/or markdown. The uploaded bundle carries the source under `code/` and a `metadata.json`
  describing the repository, the commit and where in the repository `code/` belongs.
- `--fail-on-error` on the local surface too, so evaluating policy files without an account can gate
  a merge. Off by default: the local form has always exited 0 either way, and changing that silently
  would turn existing green pipelines red.
- `ExitStatus.ERROR_POLICY_FAILED` (3), so a caller can tell "a policy said no" from "tirith could
  not tell you". Both surfaces use the same code for the same meaning. Note this applies **only**
  with `--fail-on-error`; without it the local form still exits 0 for everything, including a policy
  it could not evaluate.

### Changed
- `cli.main(args=...)` is now honoured. It previously called `parse_args()` with no argument, so
  the parameter was ignored and the CLI could only ever read `sys.argv`.

### Notes
- The local evaluation surface is unchanged, including its single-dash long options. Subcommands
  are dispatched before the flat parser sees anything, so `--json` output stays byte-identical.
- No new runtime dependencies: the platform integration is stdlib-only.

## [1.1.0] - 2026-08-01

### Added
- `core`: Policy metadata passthrough — `meta.id`, `meta.name`, `meta.description`,
  `meta.severity`, `meta.enforcement`, `meta.tags` and `meta.remediation` now reach the result
  document when a policy declares them. Keys that are absent are omitted, so the output of a
  policy declaring none of them is unchanged. `{{ var.x }}` substitution works in all of them.

### Fixed
- `core`: Variable substitution no longer mutates the caller's policy dictionary. Evaluating the
  same parsed policy more than once (a policy set, or a retry) previously leaked substituted
  values from one evaluation into the next.
- `core`: An unsupported `condition.type` now populates `result` instead of returning without it,
  which raised `KeyError` in the pretty printer far from the real cause.
- `core`: Provider errors reported without a `ProviderError` severity are now surfaced instead of
  being discarded and `None` evaluated against the condition — a typo'd `operation_type` read as
  a genuine policy violation. These are treated as malformed provider calls and are deliberately
  not subject to `error_tolerance`.

## [1.0.5] - 2025-11-19

### Fixed
- `json/get_value`: Fixed cases when the key is `*.something`
- `core`:  Fixed support for YAML files through JSON provider

## [1.0.4] - 2025-11-15

### Fixed
- `terraform_plan`: Fixed cases when using `*` as the resource_type and the attribute is not found, the provider outputs `null` insetad of `ProviderError`

## [1.0.3] - 2025-09-26

### Fixed
- `evaluators/contains`: Fixed message when the evaluator is failing when input and data are both strings

## [1.0.2] - 2025-05-27

### Added
- `terraform_plan`: Added `exclude_types` parameter to filter specific resource types when using wildcard (*) resource type
- `terraform_plan`: Support for excluding resource types in `attribute`, `action`, and `count` operations

## [1.0.0] - 2025-05-15

### Fixed
- `terraform_plan/attribute`: Fixed bug where the attribute was not being properly evaluated when using the `*` in the middle of the attribute name
- `core/evaluators`: Enhance result message to use JSON encoded string instead of Python string


## [1.0.0-beta.14] - 2025-02-25

### Added
- `terraform_plan/attribute`: Support "*" resource type

## [1.0.0-beta.13] - 2025-02-07

### Added
- New condition type: `NotContains`
- New feature to use variables within Tirith policies


## [1.0.0-beta.12] - 2024-04-02

### Fixed
- `terraform_plan/referenced_by`: Fixed bug where `referenced_by` was not accounting references in another modules
- `terraform_plan/referenced_by`: Now outputs the result per resource instead of a single boolean


## [1.0.0-beta.11] - 2024-02-22

### Fixed
- `terraform_plan/provider_config`: Properly handle the case where the region is not defined in the provider config
- `json/get_value`: Properly handle the case where the keypath is not found


## [1.0.0-beta.10] - 2023-11-16

### Added
- Bump pydash from 5.1.0 to 6.0.0


## [1.0.0-beta.9] - 2023-11-16

### Added
- `terraform_plan`: Add `terraform_version` operation type to get the terraform version from the plan file
- `terraform_plan`: Add `provider_config` operation type to get the provider config from the plan file, like checking for the `region` in the `aws` provider, and the version of the provider

### Fixed
- `evaluator/RegexMatch`: Change the method to check regex match to `re.search` instead of `re.match` to make sure the regex is matched anywhere in the string

## [1.0.0-beta.8] - 2023-11-13

### Fixed
- `terraform_plan/direct_references`: Fixed bug where `references_to` and `referenced_by` were not accounting the no-op resources
- `json/get_value`: Fixed bug where `get_value` always return list of values even if the value is not a list

## [1.0.0-beta.7] - 2023-11-08

### Fixed
- `terraform_plan`: Fixed bug where values are not typecasted for regex comparisons.

## [1.0.0-beta.6] - 2023-11-08

### Fixed
- `terraform_plan/direct_dependencies`: Fixed bug where `references_to` and `referenced_by` were still accounting the destroyed resources

## [1.0.0-beta.5] - 2023-10-26

### Added
- terraform_plan provider - bugfixes

## [1.0.0-beta.4] - 2023-10-26

### Added
- `terraform_plan/direct_dependencies`: Added option `references_to` and `referenced_by` to make sure whether the resource is referenced by or references to the given resource (e.g. `references_to: "aws_security_group"`)

## [1.0.0-beta.3] - 2023-07-20

### Fixed
- Hard set PyYAML requirement to 6.0.1 due to Cython incompatibilities, see https://stackoverflow.com/q/76708329/6156700

## [1.0.0-beta.2] - 2023-05-18

### Added
- Kubernetes provider


## [1.0.0-beta.1] - 2023-05-04

### Added
- `terraform_plan` provider: `direct_references` and `direct_dependencies` operators (891d9b7)


## [1.0.0-beta] - 2023-05-01

### Added
- NotEquals and NotContainedIn evaluators (a7c3a)

### Fixed
- Improve `terraform_plan` provider for operator `action`: return error=1 when the resource isn't found (a7c3a3)
- Improve `terraform_plan` provider: skip if no `after` key is found
- Improve error messages in `terraform_plan` provider


## [1.0.0-alpha.1] - 2022-10-04

- Initial realease of Tirith (StackGuardian Policy Framework)
- Adopted Covenant Code of Conduct
- cli wrapper for calling tirith


## Types of changes

**Added**: for new features.

**Changed**: for changes in existing functionality.

**Deprecated**: for soon-to-be removed features.

**Removed**: for now removed features.

**Fixed**: for any bug fixes.

**Security**: in case of vulnerabilities.

[unreleased]: https://github.com/StackGuardian/tirith/compare/1.0.0-alpha.1...HEAD
[1.0.0-alpha.1]: https://github.com/StackGuardian/tirith/compare/1.0.0-alpha.1
