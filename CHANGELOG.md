# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


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
