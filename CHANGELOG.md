# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0-alpha.1] - 2022-Sep-08

- Alpha release of SG Policy Framework
- Introduce v1 of schema for policy declaration in JSON
- Supported Providers:
  - Terraform Plan
  - Infracost
- Add support for evaluators:
  - ContainedIn
  - Equals
  - GreaterThanEqualTo
  - GreaterThan
  - IsEmpty
  - IsNotEmpty
  - LessThanEqualTo
  - LessThan
  - RegexMatch

---

## Types of changes

**Added**: for new features.

**Changed**: for changes in existing functionality.

**Deprecated**: for soon-to-be removed features.

**Removed**: for now removed features.

**Fixed**: for any bug fixes.

**Security**: in case of vulnerabilities.

[unreleased]: https://github.com/StackGuardian/policy-framework/compare/v1.0-beta.2...HEAD
[v1.0-beta.1]: https://github.com/StackGuardian/policy-framework/compare/v1.0-beta.1
[v1.0-beta.2]: https://github.com/StackGuardian/policy-framework/compare/v1.0-beta.2
