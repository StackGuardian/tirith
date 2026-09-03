# The interactive interface

Source: https://stackguardian.github.io/tirith/docs/tirith-usage/interactive-interface/
Summary: tirith ui — explore an evaluation down to the resource that caused it, build policies from a form, and experiment in a playground.

[NOTE] Beta — and we want your input

`tirith ui` is new. Everything described here works and is covered by tests, but the shape of the
interface is still open, and the rough edges are still being found.

Tell us what is confusing, what is missing, or what you would rather it did:
[open an issue](https://github.com/StackGuardian/tirith/issues/new/choose).

Nothing about the existing CLI changes: same flags, same `--json` output, same exit codes.

`tirith ui` opens a terminal interface with three tabs: an **Explorer** for reading results, a
**Builder** for assembling policies, and a **Playground** for experimenting.

## Installing it

It is an optional extra, so that using Tirith as a CI gate stays dependency-light — nobody gating a
pipeline should pay to install an interface they never open. It needs Python 3.9 or newer, while
Tirith itself still supports 3.8.

```bash
pip install 'py-tirith[tui] @ git+https://github.com/StackGuardian/tirith.git'
```

Tirith is not on PyPI — `pip install py-tirith` finds nothing and `pip install tirith` installs an
unrelated project of the same name — so the extra is requested against the git URL.

## Opening it

```bash
tirith ui                                          # playground, with worked examples
tirith ui --policy policy.json --input plan.json   # evaluate yours, open on the results
tirith ui --result result.json                     # an evaluation you already ran
tirith --json -policy-path p.json -input-path plan.json | tirith ui --result -
```

Naming both a policy and an input evaluates them and opens the **Explorer**, because that is what
you came to see. With only a policy, or nothing at all, it opens the Playground.

Keys: `1` Explorer, `2` Builder, `3` Playground, `r` re-run, `q` quit.

## Explorer

The output of `--json` and the pretty printer both tell you *that* a check failed. Neither tells you
*which resource* failed it — although the result document has carried the resource's address, its
planned action and its before/after values all along.

The Explorer shows them. Selecting a failing result names the resource (`aws_db_instance.primary`),
the action in Terraform's own vocabulary — **replace (destroy first)**, which is distinct from
create-first because only one of them means downtime — and the attributes that changed, including
the ones that are unknown until apply.

This matters most on a wildcard policy, where every message reads identically
(`` `"product-456"` is not empty ``) and only the address distinguishes one row from another.

## Builder

Pick a provider, an operation and a condition; the form's fields change to whatever that operation
actually accepts, and the policy JSON is generated as you go.

The argument names are not guessable: `stackguardian/json` reads `key_path` while
`stackguardian/kubernetes` reads `attribute_path`, and the Terraform provider alone has seven
operations taking different arguments. Get one wrong and the policy still parses, still runs, and
silently matches nothing.

Values keep their JSON types, so typing `true` gives a boolean, `["a","b"]` a list and `production`
the string — `Equals: true` and `Equals: "true"` are different questions.

**How the checks combine** is its own field, holding the policy's `eval_expression`:

| | |
| --- | --- |
| `a && b` | both must pass |
| `a \|\| b` | either may pass |
| `!a` | passes when the check *fails* — how you write a detector |
| `(a \|\| b) && c` | grouping |

It fills itself in with every check `&&`-ed together, and stops doing that the moment you edit it.
The expression is the one part of a policy that cannot be derived from the checks.

## Playground

Load one of the bundled examples, change something, watch the verdict move. Evaluation runs as you
type. Broken JSON, a half-written policy and a provider that raises are all reported in a findings
pane rather than as a traceback — while you are editing, the broken state is the normal state.

The examples are worked lessons rather than fixtures. Most of them fail on purpose, and each one's
notes explain the mechanism it demonstrates and what to try next:

| Example | Demonstrates |
| --- | --- |
| Required tags | One check, one condition, nested attributes. Why `error_tolerance` can turn a failure into a *skip* — and why a skip is not a pass. |
| No public buckets | Two checks joined with `&&`; two buckets, one at fault. |
| Cost ceiling | The Infracost provider, and why a misspelled resource type sums to `0` and fails open. |
| Block destroy | A database being replaced inside a routine plan, and the attribute that forced it. |
| Kubernetes probes | Wildcard paths, why `IsNotEmpty` is the wrong question over a list, and the `!` operator. |

Each editor has **Copy**, **Open** and **Clear** beside it. **Open** opens a file browser: arrow
keys to move, `→` into a directory, `←` back, Enter to choose.

## Serving it on a port

The same interface runs in a browser, which is useful for sharing a result with someone who does not
have Tirith installed:

```bash
tirith ui --serve --port 8000     # then open http://localhost:8000
```

It is the same interface relayed to the browser, not a second web-only implementation, so it behaves
identically and there is nothing extra to keep in sync.

The bind address and port are yours to choose, but note that the served interface can read any file
path the serving process can. Keep it on `localhost` unless you have a reason not to.
