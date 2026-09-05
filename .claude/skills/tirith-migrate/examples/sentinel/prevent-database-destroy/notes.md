# prevent-database-destroy: exact

`find_resources_being_destroyed()` selects resources whose actions contain `"delete"`, which
includes a replacement (`["delete", "create"]`). Tirith's `action` operation emits one result per
action in the list, so the universal form is what matches: `NotEquals "delete"` with no negation.
Every action must be something other than delete, and a replacement's `delete` element fails it.

The tempting form, `ContainedIn ["delete"]` with `!` in the expression, is a different policy: on a
replacement it yields one pass and one fail, the evaluator fails, and `!` flips that to a pass. Use
it only when the source policy deliberately allows replacements.

`error_tolerance: 1` skips a plan with no `aws_db_instance`, which Sentinel's empty filter also
passed. Without it the guard exits `3` on every plan that has no database.

| Plan | Sentinel | Tirith |
| --- | --- | --- |
| `should-fail.json` (pure delete) | fail | exit 3 |
| `should-fail-replacement.json` (delete and create) | fail | exit 3 |
| `should-pass.json` (in-place update) | pass | exit 0 |
