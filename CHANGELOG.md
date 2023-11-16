# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
