# Roadmap

Themes, not dates. This file says what the maintainers intend to work on and in
roughly what order; it is not a commitment, and anything here can be argued
with in an [issue](https://github.com/StackGuardian/tirith/issues).

Everything under **Now** and **Next** is open source and works without an
account. Where an item involves the optional StackGuardian platform, it is
labelled — and labelled *planned*, not shipped.

> [!NOTE]
> **Draft.** These themes were assembled from the launch messaging brief and
> the current state of the repository. Maintainers should confirm, reorder and
> cut before this is treated as the project's position.

## Now

Work in progress or next up.

- **Remove first-run friction.** An unambiguous installation story is the
  biggest one: Tirith is not on PyPI, `pip install tirith` installs an
  unrelated project, and the git-URL install is a stumbling block for anyone
  evaluating quickly. Publish and own a package name, or make the git route
  impossible to get wrong.
- **A credential-free demo path.** The existing four-PR demo requires a
  StackGuardian organisation and token, so it demonstrates platform mode. Add a
  local-mode quick start that reaches the same first verdict with nothing but a
  repository.
- **`tirith ui` out of beta.** The explorer, builder and playground shipped
  recently and the rough edges are still being found. Feedback is wanted.
- **Community foundations.** Governance, maintainers, support and security
  documented; issue templates for the paths people actually arrive on; a set of
  genuinely scoped good-first issues.

## Next

Intended, not started.

- **A policy test harness.** Today a policy that silently matches nothing is
  hard to distinguish from a policy that passed. Authors need a way to assert
  that a rule matched what they meant it to match — this is the gap most likely
  to cost someone real trust in a green check.
- **GitLab CI support that is as good as the GitHub Action.** Right now GitLab
  users invoke the CLI directly and get no native reporting. Either a catalog
  component or an honest statement that the CLI is the supported route.
- **A published, tested policy library.** Community-contributed policies with
  clear ownership, licensing and tests, rather than examples pasted from docs.
- **Better provider coverage and clearer provider errors**, driven by what
  people actually report.
- **A fair, reproducible comparison** with Checkov, OPA/Rego and Sentinel —
  identical policies in a benchmark repository, published including the cases
  where another tool is the better fit.

## Later

Directional. No design work has been done, and any of it may be dropped.

- **Richer remediation output** — showing the smallest compliant change, not
  just the failing value.
- **Policy versioning and deprecation** as policy sets grow past what one
  person holds in their head.
- **Governed execution via the StackGuardian workflow API** *(planned; platform
  mode)* — moving from a policy decision into controlled execution. This does
  not exist today and should not be described as if it does.

## Not planned

Stated so nobody spends effort proposing them:

- **Replacing scanners.** Tirith is the governance step between plan and apply,
  not a catalogue of built-in security checks. Checkov's breadth is real and we
  are not trying to reproduce it.
- **A second policy language.** Policies are JSON data. If a rule needs a
  program, that is a signal the provider is missing an operation, not that
  Tirith needs an expression language.
- **Network calls in local mode.** See [GOVERNANCE.md](GOVERNANCE.md).
