Catch a database replacement hiding inside a routine plan.

`operation_type: "action"` reads what terraform intends to *do* to a resource, rather than
an attribute of it. This is how you gate on destruction.

The catch this policy exists for: `aws_db_instance.primary` is not being destroyed on
purpose. Its `instance_class` changed, which forces a replacement, and terraform expresses
that as `["delete", "create"]` — a destroy and a recreate. In a plan of any size that is
easy to miss, and it means losing the database.

Select the failing row. The detail pane names the action **replace (destroy first)** and
shows the attribute that forced it: `instance_class`, `db.t3.medium → db.t3.large`. The
ordering matters — destroy-first has downtime, create-first does not — so the two are named
differently rather than both reading "replace".

`aws_db_instance.replica` is only growing its storage, so it updates in place and passes.

**Things to try**

- Change `primary`'s `instance_class` back to `db.t3.medium` and set `actions` to
  `["update"]`. The policy passes.
- Swap `NotContains` for `ContainedIn` with `["delete"]` to write the inverse check.
- Drop `error_tolerance: 1` and change the resource type to one the plan does not contain.
  Without the tolerance a missing resource is a failure; with it the check is skipped.

**Why the resource appears twice**

The `action` operation emits one result per action, so a replacement produces two rows for
the same resource — one for `delete` (which fails) and one for `create` (which passes).
The check as a whole fails, because any failing result fails its check.
