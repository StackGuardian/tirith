# Security policy

## Supported versions

Tirith is released as git tags; there is no long-term support branch. Security
fixes land on `main` and are released as a new tag.

| Version | Supported |
|---|---|
| Latest tag | Yes |
| Anything older | No — upgrade to the latest tag |

CI examples in this repository pin a tag rather than tracking `main`, so
upgrading is a one-line change and a deliberate one. Check what you are pinned
to with `git ls-remote --tags https://github.com/StackGuardian/tirith.git`.

## Reporting a vulnerability

**Do not open a public issue for a suspected vulnerability.**

Use GitHub's private reporting:
[Report a vulnerability](https://github.com/StackGuardian/tirith/security/advisories/new).
It creates a private advisory visible only to you and the maintainers, and it
is the fastest route.

> [!NOTE]
> **Confirm before launch:** private vulnerability reporting must be enabled in
> the repository's Settings → Security before the link above works, and a
> monitored security contact address should be added here as a fallback for
> reporters who cannot use GitHub. Both are open items.

A useful report includes what you did, what happened, what you expected, the
Tirith version or commit, and — if you have one — a minimal reproduction.
Please do not include real secrets, plan files or private source in a report;
redact them, the same way the issue templates ask.

### What to expect

- **Acknowledgement within three working days.** If you have not heard back,
  assume the message was lost rather than ignored, and ping any maintainer in
  [MAINTAINERS.md](MAINTAINERS.md) — without disclosing details publicly.
- **An assessment within ten working days**, saying whether we consider it a
  vulnerability and, if so, roughly when a fix will land.
- **Credit in the advisory and release notes**, unless you would rather not be
  named.

We will not take legal action against anyone reporting in good faith, and we
ask the same courtesy in return: give us a reasonable window to ship a fix
before disclosing publicly.

## What counts

Things we want to hear about:

- Anything that causes Tirith to report a **pass for a policy that should have
  failed**, or to exit `0` when the verdict was never established. A gate that
  silently stops gating is the worst failure this project has.
- **A sensitive value surviving masking** in `tirith platform check` — a
  terraform-sensitive value, or a credential-shaped literal, reaching the
  network unredacted.
- Code execution, path traversal or file disclosure triggered by a crafted
  policy file, plan document or provider input.
- Credential leakage into logs, PR comments, check-run output or the result
  document.
- Dependency vulnerabilities that Tirith actually reaches.

## Known limits, already documented

These are stated behaviour rather than vulnerabilities. Reporting them is
welcome as a documentation or design issue, but they are not secret:

- **`json` and `kubernetes` documents are not masked.** There is no schema that
  says which fields are secret.
- **Committed source ships as written** in platform mode. Masking applies to
  the documents, not to your repository — a secret hardcoded in a `.tf` file
  reaches the platform even though the plan was masked. `--no-source` is the
  opt-out.
- **Terraform's sensitivity markers are not exhaustive.** A value that flows
  through `locals`, or comes from a provider that did not mark its schema, is
  not caught by marker-driven masking.
- **A misconfigured policy fails closed but reads as a violation** — an
  unsupported `condition.type` or unknown `required_provider` comes back as an
  ordinary failed check and exits `3`, pointing at your infrastructure when the
  fault is in the policy.

The full detail is in the
[platform-check documentation](https://stackguardian.github.io/tirith/docs/tirith-usage/platform-check/)
and the [exit-code contract](https://stackguardian.github.io/tirith/docs/tirith-usage/exit-codes/).

Local mode makes no network call at all, which bounds a great deal of this: if
you never pass credentials, nothing leaves your runner.
