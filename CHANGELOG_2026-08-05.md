# What changed on 2026-08-05

Everything below was built, deployed to QA and exercised against **freshly created private
repositories** — not fixtures. Every claim links to the run that proves it.

Test repos: [tirith-e2e-08050726](https://github.com/refeed/tirith-e2e-08050726) ·
[tirith-e2e-08051009](https://github.com/refeed/tirith-e2e-08051009) (priced fixture: a
`t3.medium`, an unencrypted S3 bucket, a `null_resource`, and a `local_sensitive_file` fed from a
`sensitive` variable).

---

## 1 · The masker was silently disarming Infracost and Checkov

**The single most consequential finding of the day.** Both tools read `planned_values` and nothing
else. The masker dropped it — correctly, because terraform's copy mirrors every value with **no**
sensitivity markers, so masking `resource_changes` leaves the same secret in plaintext there. A real
plan had leaked a `local_sensitive_file` body through exactly that path.

The consequence was that both tools returned a clean, empty, entirely wrong answer. Measured
against infracost 0.10.27, same binary, same key, same plan, differing only by this section:

| plan | totalMonthlyCost | priced resources |
|---|---|---|
| with `planned_values` | **$39.80** | 1 |
| without — what we shipped | 0 | 0 |

`redact_plan` now **rebuilds** `planned_values` from the *already-masked* `resource_changes`, after
`_mask_by_marker` has run. Same data, same shape, no unmarked copy. Only `after`, and only for
resources that will exist — a destroy has no planned value. Module resources group under
`child_modules`; flat and nested forms were verified to price identically.

**Evidence** — [run 30978181140](https://github.com/refeed/tirith-e2e-08051009/actions/runs/30978181140):

```
planned_values present : True
planned resources      : aws_instance.app, aws_s3_bucket.data, null_resource.untagged
secret leaked?         : False
best-practices         : FAIL      ← was WARN "Policy produced no evaluator outcomes"
```

That `WARN → FAIL` is Checkov genuinely evaluating the unencrypted bucket for the first time.

`tirith@041d5f9` · 17 new tests, including that the rebuilt section carries `__SG_REDACTED__` and
that terraform's original copy is replaced rather than merged.

## 2 · Checkov policies were never running

A QA run showed an org's enforced `best-practices` policy coming back
`Unsupported sourceConfigKind "SG_INTERNAL_P2"`. **`SG_INTERNAL_P2` is Checkov** — the plan/apply
path has handled it all along. So this was not a missing feature; it was an **enforced policy that
silently never ran**.

`checkov()` and `extract_result_from_checkov_output()` moved verbatim out of `main.py` into a shared
`checkov_support.py` — `main.py` imports the step module, so the dependency cannot run the other
way, and two copies of the output mapping is exactly the drift that produces two different verdicts
for the same plan. `main.py`'s call sites are unchanged.

On top of that, a **built-in Checkov pass** for orgs that have configured nothing. Deliberately
narrow, because nobody opted into it: only in the `default` workflow group, only when no Checkov
policy is already enforced, and always `WARN` — which maps to a `neutral` check and so can never
block a merge.

> Not yet observed firing: `demo-org` enforces `best-practices` org-wide, so the defer-to-configured
> rule correctly suppresses it every time. Needs an org or group without a Checkov policy.

`workflow-step-templates@cf3745e`

## 3 · Infracost now prices every run

`main.py` has always priced unconditionally. The tirith-check path only ran it when a policy
declared the infracost provider. That gate is gone: the binary is in the image, the key is already
injected for any TERRAFORM workflow, and it costs one subprocess.

It runs **ahead of** the `applyPolicy` check on purpose — a caller who turned policy evaluation off
still gets a cost estimate, and that is precisely the caller who is not costing today.

Published under `InfracostBreakdown` **and** `InfracostBreakdownPreApply`. The bare key renders
nowhere: the run modal gates its cost tab on the Pre/Post keys, and both the workflow overview and
the PR comment read `PreApply`. Not `PostApply` — nothing was applied, and that key feeds
`incurred_cost` in the org rollup, where a speculative number would be reported as money spent.

## 4 · Cost appears in the pull-request comment

A line under the findings with the monthly total, plus the delta from the change when Infracost
supplies one. Rendered **even at zero or on failure**, because silence is indistinguishable from
"this change costs nothing" — very different things to tell a reviewer. Placed outside the
truncation path, so a wall of findings cannot push it out. Also surfaced as `monthly_cost` in
`--output-json` for a caller aggregating several units.

## 5 · `policy-only` → `tirith-check`

The old name described what the action does *not* do. The new one names the thing that runs, and
matches the CLI subcommand and the action users add, so the same word appears at every layer.
Renamed across core, api, workflow-step-templates and tirith, including the module
(`policy_only.py` → `tirith_check.py`).

Nothing had shipped under the old name, so there is no alias and no migration — the action is a
per-run RuntimeParameter, not stored on the workflow.

**Evidence** — [run 30973554638](https://github.com/refeed/tirith-e2e-08051009/actions/runs/30973554638):

```
POST wfruns/ {"action":"policy-only"}  ->  "policy-only" is not a valid choice
RuntimeParameters.terraformAction      ->  {'action': 'tirith-check'}
```

`git grep` across all four repos returns zero residual references.

## 6 · Artifacts no longer accumulate

Measured on the older QA workflow: **27 permanent directories** — 10 project archives and 17
`tirith-results.json` files, every one downloaded into every later run's working directory. There is
no retention anywhere: no lifecycle rule, no TTL, no `--delete` on either sync direction.

The results artifact is gone entirely — it duplicated `PolicyEvalResults`, which the run facts
already carry. The project archive is now deleted after the run.

That required **flattening** the archive name to `__sg.<sha7>-<tag>.tar.gz`. Not cosmetic: verified
against auth's own matcher, a nested `DELETE .../artifacts/<sha7>/<name>/` resolves to
`DELETE .../wfgrps/<wfGrp>/` — the *workflow-group delete* — via the greedy `<path:wfGrp>`
converter, so it would be checked against entirely the wrong permission.

**Evidence** — artifact prefix after a run: `sub-prefixes: (none)  objects: (none)`.

## 7 · The workflow now links back to its repo

Set via `GIT_OTHER` (singular — the wire value behind the UI's "Git Others"), the connector-less
provider, which with `isPrivate: false` needs no auth. Metadata only: core pops `iacVCSConfig`
whenever `terraformProjectZip` is set, and the runner takes the archive branch regardless.

**Evidence**: `GIT_OTHER | https://github.com/refeed/tirith-e2e-08050726 | ref = add-storage`.

> Caveat, measured rather than predicted: on a **private** repo the async repo-insights scan that
> fires on workflow creation settles at `scan_status: "error"`. It cannot fail the create, but it is
> user-visible. Worth deciding whether to suppress it for archive-based workflows.

## 8 · Two bugs the E2E caught that unit tests did not

**`None/` folder.** The first run uploaded to `artifacts/`**`None`**`/__sg.d1ecf60-default.tar.gz` —
`urlencode` stringifies `None` to the literal string, and the endpoint treats any non-empty folder
as a subfolder. So a bogus directory appeared *and* the archive sat at a nested key the delete could
not address, so cleanup silently no-opped on a 404. `tirith@cbc397c`, with a parametrized regression
test over `None` and `""`.

**A broken facts reader.** `get_policy_results` read `body.get("signedUrl")` while the endpoint
returns `signed_url`, so the facts path **always** returned `{}`. It went unnoticed for exactly as
long as the results artifact was covering for it — which is why removing that artifact had to be
sequenced behind fixing this.

---

## Removed from this batch

The two wfrunfacts platform fixes are **closed**, with the full diagnosis preserved on each PR:
[core#1238](https://github.com/StackGuardian/core/pull/1238) ·
[sg-run-controller#295](https://github.com/StackGuardian/sg-run-controller/pull/295).

One correction to how I described that bug earlier: it is **shared-ec2 only**. `external.py` passes
`resource_ksuid` explicitly and was never affected. The 08051009 workflow landed on
`shared-external`, where `wfrunfacts` returns 200 — which is why the E2E kept working after the
revert. Worth carrying into whatever ticket picks it up.

## Open — one thing not finished

**Infracost still reports `$0` on QA**, and it is now down to a single variable.

The plan is correct: I took the exact `TfPlan` that QA shipped and priced it locally with your key —
**$35.99, 2 resources**. The same plan on QA returns 0.

An *invalid* key reproduces QA's behaviour precisely — valid JSON, no error, `monthly: 0`,
`priced: 0`. A *missing* key errors out loudly instead. So the image has a key baked in; it just is
not a working one.

`INFRACOST_API_KEY` is now set as a repo secret and the image was rebuilt
([run 30978470905](https://github.com/StackGuardian/workflow-step-templates/actions/runs/30978470905)) —
the build log confirms `--build-arg infracost_api_key=***`, masked, so non-empty. The rebuild pushed
`:dde24b0` and `:latest`, `dde24b0` **is** the current branch head, and the Checkov `FAIL` proves the
run used that image. Yet the cost stayed 0.

What I have not been able to settle: whether the runner resolves `/stackguardian/terraform:11` to a
different, older ECR tag. I could not read the `WORKFLOW_STEP` template (`Unauthorized` on
`orgs/stackguardian`), and could not rebuild locally — `aws sts get-caller-identity --profile
sg-nonprod-1-readwrite` fails with *"The source profile sg-saml must have credentials"*, which needs
an interactive SSO login.

Next step, needing someone who can read the template: confirm which image tag revision 11 points at,
and whether it is `:latest`. If it pins an older tag, the `WORKFLOW_STEP` revision bump — already on
the roadmap as a manual step — is the fix.

Worth noting the key is baked into the image as an `ENV`, readable by anyone who can pull it. That
is the pre-existing design, not something introduced here, but it is why the org secret is the right
home for it rather than anything hardcoded.

---

## Test counts

| repo | |
|---|---|
| tirith | 196 |
| workflow-step-templates | 115 |
| core | 30 |
| sg-cli-gh-action | 26 |
