# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - Unreleased

### Fixed

- Terraform binary not required for using OPA provider

## [v1.0-beta.2] - 2021-01-12

### Added

- CHANGELOG, CODE_OF_CONDUCT, CONTRIBUTING
- Adopted Covenant Code of Conduct
- cli wrapper for calling tirith
- Summarized evaluation output and provides brief output formatting

### Fixed

- License content

## [v1.0-beta.1] - 2021-07-10

- Initial release of Tirith (SG Policy Framework).
- New schema for policy declaration in JSON - V1.BETA
- Tested for scanning terraform plans >= 0.14.6
- Added Support for for evaluations using Rego:
  > - str_equals_str
  > - str_contains_str
  > - str_contains_str
  > - equals_null
  > - str_matches_regex
  > - bool_equals_bool
  > - cidr_contains_cidr_or_ip

---

## Types of changes

**Added**: for new features.

**Changed**: for changes in existing functionality.

**Deprecated**: for soon-to-be removed features.

**Removed**: for now removed features.

**Fixed**: for any bug fixes.

**Security**: in case of vulnerabilities.

[unreleased]: https://github.com/StackGuardian/tirith/compare/v1.0-beta.2...HEAD
[v1.0-beta.1]: https://github.com/StackGuardian/tirith/compare/v1.0-beta.1
[v1.0-beta.2]: https://github.com/StackGuardian/tirith/compare/v1.0-beta.2
