# Contributing to Tirith (StackGuardian Policy Framework)

Thank you for taking the time to contribute! 🎉
Contributions are welcome, and they are greatly appreciated! Every
little bit helps, and credit will always be given.

The following is a set of guidelines for contributing to Tirith on GitHub. These are mostly guidelines, not rules. Use your best judgment, and feel free to propose changes to this document in a pull request.

## Join the StackGuardian Community
We'd love for you to join our community! Join our [Slack](https://join.slack.com/t/stackguardian-ol78820/shared_invite/zt-2ksag36j9-OjmXqQmyXudgYrV6FmesIQ) to ask questions, share ideas, and connect with other contributors. Follow us on [LinkedIn](https://www.linkedin.com/company/stackguardian/posts/?feedView=all) to stay updated on the latest news and announcements.

## Contribution types

### Report Bugs

We use GitHub issues to track bugs at [https://github.com/stackguardian/tirith/issues](https://github.com/stackguardian/tirith/issues). Please use Bug report issue template.

### Fix Bugs and implement features

All contributions to solve GitHub issues tagged with "bug", "enhancement" and "help wanted" are most welcome and greatly appreciated.

### Documentation

Trith could always use more documentation, whether as part of the
official Tirith docs, in docstrings, or even on the web in blog posts,
articles, and such.

### Submit Feedback

Please use GitHub Discussions to submit feedback and engage with community [https://github.com/StackGuardian/feedback/discussions/8](https://github.com/StackGuardian/feedback/discussions/8).

## Basic guidelines

### Commits

-  Use the imperative, present tense («change», not «changed» or «changes») to be consistent with generated messages from commands like git merge.
- Describe the changes you have made

#### Examples
**Good example**: 
 - Commit Message:\
  `Add feature to calculate total monthly cost for AWS resources`

- Description:\
`Implement a function that calculates the total monthly cost for AWS resources. Update the documentation to reflect this new feature.`

  Why it’s Good:
    > **Clarity**: Clearly states the action and the feature.\
    >**Specificity**: Specifies what the feature is and what it affects (AWS resources).\
    >**Consistency**: Uses imperative, present tense, aligning with best practices.


**Bad Example**:  
- Commit Message:\
  `Fixed some stuff`
- Description:\
`Made changes to the code to fix issues. Updated a few things here and there.`
  Why it’s Bad:
    > **Vague**: Does not explain what was fixed.\
    > **Lacks Detail**: Provides no insight into what "stuff" refers to or how it was changed.\
    > Does not use imperitve present tense.

### Pull Requests

- **Stay Updated**: Make sure your PR is based on the latest code from the `main` branch.
- **Clear Title and Description**: Try to include a clear, descriptive title and a detailed explanation of your changes.
- **Reference Issues**: If applicable, link to related issues and PRs.
- **Pass Tests**: Ensure all tests pass before submitting your PR.
- **Be Open to Feedback**: We're all here to help each other improve, so please be open to feedback and ready to make adjustments.

### Creating Issues

- **Search First**: It helps to check if your problem or feature request has already been discussed before opening a new issue.
- **Be Detailed**: When you open a new issue, providing as much detail as possible really helps. Feel free to use our templates for bugs and feature requests.
- **Be Respectful**: Let's all be kind and considerate in our communication.

### Solving Issues

- Limit yourself to solving a maximum of four `good first issues`. Once you've reached this limit, consider tackling other types of issues.
- Please work on only one issue at a time.
- Please ask for assignee before working, and if there's no update for about a week on a particular issue, we'll remove the assignee.

## AI use policy

This policy covers every contribution to Tirith: code, docs, issues, reviews and discussion. AI tools are welcome; unreviewed AI output is not. You own every line you submit, and "the AI wrote it" is never an answer to "why is this change correct?"

> [!WARNING]
> **PRs that look AI-generated and untested are closed without review.** Maintainer time is the scarcest thing in this project; send us your best work.

### Writing code with an assistant

1. Read the code you are changing first (the evaluator, provider or test the issue names), so you can judge what the assistant gives you.
2. Check every claim an assistant makes about Tirith against the source or the docs. Assistants often invent condition types, provider operations and CLI flags that do not exist.
3. Start from an open issue and get it assigned to you before writing code. Don't ask an assistant to scan the repo for things to fix.
4. Run `pytest tests/` yourself, and for policy changes run the policy against a real plan; paste the output in the PR.
5. Keep the diff to what the issue asks: no reformatting, no unrelated files, and coherent commits even if the assistant produced everything at once.
6. Don't have an assistant add comments across the code. Add a comment only where the code cannot say it, and keep it short.

### Writing PRs, reviews and messages

1. A PR description explains *why*. Leave out what the diff already shows (files touched, functions renamed).
2. Answer review comments in your own words. Never paste an assistant's reply into a review thread.
3. Everything you write must be accurate, including what the change does and how you tested it. Misreporting your testing gets the PR closed.
4. Fill in every field of the PR template; don't overwrite it with generated text.
5. Short and clear beats polished. Spelling, grammar and translation tools are fine; if an assistant edits your text, it must not get longer.
6. Link primary sources (a line of Tirith code, the Terraform provider docs, a CIS control) instead of quoting an assistant. If you must quote one, put it in a quote block so it is clearly not your own words.
7. Write your own messages in Slack and GitHub discussions. We want to hear from you, not a model.

Rule of thumb: if you wouldn't carefully read the output yourself, don't ask a maintainer to.

### When a PR is closed as `invalid`

- It touches files unrelated to its issue, or reformats code it did not change.
- It uses functions, flags, condition types or policy fields that do not exist in Tirith.
- It claims test results that were not run.
- Its author cannot answer a reviewer's follow-up question about their own change.

Adapted from [Zulip's AI use policy](https://github.com/zulip/zulip/blob/main/docs/contributing/contributing.md).

Thank you for taking the time to help improve our project!



### If you have commit access:

- Do NOT use git push --force.
- Do NOT commit to other contributor's branches without their consent.
- Use Pull Requests if you are unsure and to suggest changes to other maintainers.
