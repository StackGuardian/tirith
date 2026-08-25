# Getting help

**GitHub Issues is the support channel for Tirith.**
[Open one](https://github.com/StackGuardian/tirith/issues/new/choose).

Public by default is deliberate. A question answered in an issue is findable by
the next person with the same problem; the same question answered in a private
channel is answered once.

## Before you open one

- Check the [documentation](https://stackguardian.github.io/tirith/) — the
  [exit-code contract](https://stackguardian.github.io/tirith/docs/tirith-usage/exit-codes/)
  in particular, if a job is red and you are not sure why.
- Search [existing issues](https://github.com/StackGuardian/tirith/issues?q=is%3Aissue).
- Try `tirith ui` if you are debugging a policy: the explorer walks a failing
  evaluation down to the resource that caused it, which is usually faster than
  reading raw JSON.

## Which template

| You have | Use |
|---|---|
| Something is broken | Bug report |
| A rule you cannot express | Policy request |
| Tirith will not slot into your CI | Integration help |
| A first pipeline to set up | Help me govern my first IaC pipeline |
| A design change to propose | Proposal / RFC |

Whatever you open: **no secrets, no plan files, no private source code.**
Redact, or reduce it to a minimal public example.

## What you can expect

Maintainers are volunteers and StackGuardian engineers, not a support rota.
Issues are usually acknowledged within a few working days. An issue with a
reproduction gets looked at sooner than one without, which is not a rule so
much as an inevitability.

## Community versus commercial support

Everything in this repository — the CLI, the providers, the policy schema, the
GitHub Action's local mode, the example policies — is Apache-2.0 and supported
here, by the maintainers, for free.

[StackGuardian](https://www.stackguardian.io/) sells a platform that Tirith can
optionally talk to (`tirith platform check`), and sells commercial support for
it. That is a separate relationship with a separate contract. You never need it
to use Tirith: local mode needs no account, and questions about local mode
belong here, in issues, regardless of whether you are a StackGuardian customer.

If your question is specifically about a StackGuardian organisation, its
policies, or a platform-mode run, StackGuardian's own support is the faster
route.

## Security

Not here — see [SECURITY.md](SECURITY.md), which is a private route.
