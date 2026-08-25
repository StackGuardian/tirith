# Contributing to Tirith

Thank you for taking the time to contribute. Every bit helps, and credit is always given.

These are guidelines rather than rules. Use your judgement, and propose changes to this document in
a pull request if something here is wrong or unhelpful.

## Where the project lives

**Everything happens on GitHub, in public.** Bugs, feature requests, policy questions, design
disagreements and help getting a first pipeline gated all go through
[Issues](https://github.com/StackGuardian/tirith/issues/new/choose). There is no private channel
you need to be in to participate, and no account anywhere but GitHub.

Public by default is deliberate: a question answered in an issue is findable by the next person
with the same problem.

- **How decisions are made** — [GOVERNANCE.md](GOVERNANCE.md)
- **Who maintains what** — [MAINTAINERS.md](MAINTAINERS.md)
- **What is planned** — [ROADMAP.md](ROADMAP.md)
- **Where to ask for help** — [SUPPORT.md](SUPPORT.md)
- **Reporting a vulnerability** — [SECURITY.md](SECURITY.md), which is a private route. Not an
  issue.

The [Code of Conduct](CODE_OF_CONDUCT.md) applies everywhere in the project.

## Ways to contribute

### Report a bug

[Open a bug report](https://github.com/StackGuardian/tirith/issues/new/choose). A reproduction —
even a rough one — is the difference between a fix this week and a fix eventually.

**Do not include secrets, plan files or private source code.** Redact them, or reduce the case to
a minimal public example. This applies to every issue and every pull request.

### Request a policy you cannot express

Use the policy request template. Say the rule in plain words, show what you tried, and show what
happened instead. A rule that is awkward to write is usually a missing provider operation rather
than a missing language feature, and that is worth knowing.

### Fix bugs and implement features

Issues labelled `bug`, `enhancement` and `help wanted` are all fair game. Issues labelled
[good first issue](https://github.com/StackGuardian/tirith/labels/good%20first%20issue) carry
enough maintainer context and acceptance criteria to start on without asking.

### Improve the documentation

Docs count as contributions, and are frequently the highest-leverage ones. That includes
docstrings, the documentation site under `documentation/`, and worked policy examples.

### Propose a design change

Substantial changes should start as an RFC issue describing the problem, before a pull request
describing the solution — it is cheaper to disagree about an approach in a paragraph than in a
diff. Changes to the policy schema, the CLI contract, the action's behaviour, or what leaves the
machine need two maintainer approvals; see [GOVERNANCE.md](GOVERNANCE.md).

## Getting an issue assigned

Ask on the issue before you start, and a maintainer will assign it. Then:

- Work on one issue at a time.
- Limit yourself to four `good first issue` items in total; after that, please move on to other
  kinds of issue so the easy ones stay available to newcomers.
- If an issue assigned to you goes quiet for about a week, the assignee is removed so somebody else
  can pick it up. Say so on the issue if you are still on it — that is enough.

## Opening a pull request

1. Fork the repository and clone your fork.
2. Create a branch named for the change: `git switch -c fix-equals-evaluator`.
3. Make the change, and **add a test that fails without it**.
4. Run the test suite and the linters.
5. Push, and open a pull request against `main`.

What makes a pull request easy to merge:

- **Based on current `main`.** Rebase rather than merging `main` into your branch.
- **A clear title and description.** Say what changed and why; link the issue it closes.
- **Green CI.**
- **Openness to review.** Review comments are about the change, not about you.

### Commit messages

Use the imperative, present tense — «change», not «changed» or «changes» — so your messages read
the same way as the ones git generates itself. Describe what the change does, and why if it is not
obvious.

**Good:**

> `Add support for calculating total monthly cost of AWS resources`
>
> Implement a function that sums the monthly cost of the resources an Infracost breakdown would
> create, so a policy can gate on the total. Update the provider documentation.

Clear about the action, specific about what it affects, and consistent with the rest of the log.

**Bad:**

> `Fixed some stuff`
>
> Made changes to the code to fix issues. Updated a few things here and there.

Vague, no detail about what "stuff" was, and the wrong tense.

## If you have commit access

- Do **not** use `git push --force` on shared branches.
- Do **not** commit to another contributor's branch without their consent.
- Use a pull request when you are unsure, or when suggesting changes to another maintainer's work.

Thank you for taking the time to help improve Tirith.
