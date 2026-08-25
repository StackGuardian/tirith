# Working on Tirith with a coding agent

Tirith is an open-source IaC governance tool: it evaluates the Terraform or OpenTofu plan a
pipeline already produces against declarative JSON policies and returns a pass, warning, failure
or unevaluated verdict.

This file is for an agent working **on this repository**. If you are writing policies in someone
else's repository, the skill at `.claude/skills/tirith-policies/SKILL.md` is the one you want —
it is self-contained and can be copied into any project.

## Layout

| Path | What lives there |
|---|---|
| `src/tirith/core/` | The evaluation engine and the condition registry (`EVALUATORS_DICT`) |
| `src/tirith/providers/` | One directory per provider; each turns an input document into values |
| `src/tirith/platform/` | `tirith platform check` — the only surface that talks to a network |
| `src/tirith/tui/` | `tirith ui`, optional `[tui]` extra |
| `src/tirith/mcp/` | `tirith mcp`, optional `[mcp]` extra |
| `src/tirith/tui/examples/` | Worked policy/input pairs, used by the UI, the docs site and the tests |
| `documentation/` | The Docusaurus site |
| `tests/` | pytest |

## Running things

```bash
pip install -e .                  # the CLI
pip install -e '.[tui]'           # plus the interactive interface (needs Python 3.9+)
pip install -e '.[mcp]'           # plus the MCP server (needs Python 3.10+)

pytest                            # the suite
tirith -policy-path .tirith/policies -input-path plan.json --fail-on-error
```

The documentation site needs Node 18 or newer:

```bash
cd documentation && npm ci && npm run build
```

## Things that will bite you

**Exit codes are a contract, not a convention.** `0` passed, `3` a policy failed, `1` Tirith
could not reach a verdict, `2` platform timeout. `3` is deliberately not `1`: a caller has to be
able to page the platform team on one and the change author on the other. Both surfaces fail
closed. `tests/core/test_output_compatibility.py` asserts the `--json` output is byte-identical
to a golden file — if you change the result shape, that test is the conversation.

**`final_result: null` is not a pass.** It means every check was skipped, so the policy evaluated
nothing. It exits `1`, not `0` and not `3`.

**Optional extras must degrade, not crash.** `tui` needs Python 3.9 and `mcp` needs 3.10, while
Tirith itself supports 3.8. Both are dispatched before the flat argument parser and both report a
missing extra as an actionable message rather than an ImportError traceback. Keep the SDK imports
inside the subcommand's `cli.py`, never at package import time — the tests rely on importing the
package without the extra installed.

**Local mode makes no network call.** That is a published governance commitment, not just current
behaviour. Nothing outside `src/tirith/platform/` may open a connection.

**Adding a condition type** means adding it to `EVALUATORS_DICT`; the MCP server, the docs page
and the skill's list all read from or mirror that registry. Adding a provider `operation_type` to
`terraform_plan` means updating `_TERRAFORM_PLAN_OPS` in `src/tirith/mcp/tools.py` — there is a
drift test that will tell you.

## Style

- Comments explain **why**, not what. The existing code is comment-rich in that specific way;
  match it rather than stripping it.
- British spelling in prose; American in code identifiers where the ecosystem uses it.
- Commit messages: imperative present tense (`Add …`, not `Added …`), with a body saying why.
- Every behavioural change needs a test that fails without it.

See [CONTRIBUTING.md](CONTRIBUTING.md) for the pull-request process and
[GOVERNANCE.md](GOVERNANCE.md) for which changes need two approvals.
