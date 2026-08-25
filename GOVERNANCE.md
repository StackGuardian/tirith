# Tirith governance

Tirith is an Apache-2.0 open-source project governed by its maintainers.
StackGuardian contributes engineering time, infrastructure and production
experience, but using, forking or contributing to Tirith does not require a
StackGuardian account or a commercial relationship. Project decisions are made
in public, through GitHub Issues and pull requests, under the process below.

## What this project promises

These commitments hold for every release. If one of them has to change, it
changes in public, in a pull request against this file, with the reasoning
stated.

- **Local policy evaluation stays usable without a StackGuardian account.**
  Running `tirith` against a plan on your own machine or runner will not start
  requiring credentials.
- **The open parts stay open.** The policy schema, the providers, the CLI
  contract, the action's local mode and the example policy library are
  Apache-2.0 and remain so.
- **Local mode sends nothing.** No telemetry, no plans, no source, no results —
  unless a future opt-in is added, and then only as an opt-in that is off by
  default and documented before it ships.
- **Commercial capabilities are labelled.** Anything that needs a StackGuardian
  organisation is called out as such in the docs, on the landing page, in demos
  and in release notes. `tirith platform check` is the only such surface today.
- **Breaking changes are versioned and documented**, and CI examples pin a
  released tag rather than a moving branch.
- **Community policies get a real home.** Accepted policy contributions live in
  a public, tested policy library with clear ownership and licensing.

## Roles

**Contributor** — anyone who opens an issue or a pull request. No prior
involvement is expected, and no account anywhere but GitHub is needed.

**Maintainer** — has commit access and review authority over some area of the
project. Maintainers are listed in [MAINTAINERS.md](MAINTAINERS.md), which also
records what each one looks after.

There is no third tier. If the project grows enough to need one, it will be
added here first.

## How decisions get made

Most changes need one maintainer approval and green CI. That covers bug fixes,
documentation, new policy examples, new conditions and new provider operations.

Changes that alter a contract need **two** maintainer approvals, from
maintainers who did not author the change:

- the policy schema, or the meaning of an existing field;
- the CLI's flags, output shape or exit codes;
- the action's inputs, outputs or default behaviour;
- what leaves the machine in either mode;
- anything in this file.

Where a change is contested, the maintainers seek consensus in the pull request
or issue thread. Consensus means no maintainer sustains an objection — not that
everybody is enthusiastic. If consensus is not reached within two weeks, a
simple majority of maintainers decides, and the reasoning is recorded in the
thread. A maintainer may block a change on the grounds that it breaks one of
the promises above; that objection is resolved by changing the promise first,
in its own pull request, or not at all.

Substantial changes should start as an issue describing the problem before a
pull request describing the solution. This is a courtesy to the contributor as
much as to the project: it is cheaper to disagree about an approach in a
paragraph than in a diff.

## Releases

Any maintainer may cut a release. Releases are tagged, and the tag is what CI
examples and installation instructions point at. A release that changes a
documented contract says so in [CHANGELOG.md](CHANGELOG.md) and in the release
notes, in the plain terms a reader upgrading their pipeline needs.

## Adding and removing maintainers

A contributor with a sustained record of good judgement in the project — review
comments as much as commits — may be nominated by any maintainer. The
nomination is an issue; it carries if a majority of maintainers agree and none
sustain an objection.

Maintainers who have been inactive for six months move to emeritus in
[MAINTAINERS.md](MAINTAINERS.md) and lose commit access, with no implication of
fault; the door back is another nomination. A maintainer may step down at any
time by opening a pull request against that file. Removal for cause — repeated
violation of the [Code of Conduct](CODE_OF_CONDUCT.md), or acting against the
promises above — requires a majority of the remaining maintainers.

## Relationship to StackGuardian

StackGuardian employs several of the maintainers, funds the project's
development and operates the optional platform mode that `tirith platform
check` talks to. That relationship is why the project exists and is worth being
plain about.

What it does not confer: StackGuardian has no reserved seats, no casting vote
and no veto. A StackGuardian-employed maintainer's approval counts the same as
anyone else's, and the two-approval rule above deliberately makes it awkward
for a single employer's engineers to change a contract quietly. Where a change
would benefit the platform at the expense of the local, accountless path, the
promises at the top of this file are the tiebreaker.

## Conduct

The [Code of Conduct](CODE_OF_CONDUCT.md) applies to every project space.
Reports go to the maintainers listed in [MAINTAINERS.md](MAINTAINERS.md);
security reports follow [SECURITY.md](SECURITY.md) instead, which is a private
route.
