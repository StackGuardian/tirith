# prevent-database-destroy: approximate

`find_resources_being_destroyed()` selects resources whose actions contain `"delete"`, which
includes a replacement (`["delete", "create"]`). Tirith's `action` operation emits one result per
action in the list, so `ContainedIn ["delete"]` on a replacement yields one pass and one fail, the
evaluator fails, and `!` turns that into a pass. **A replacement does not fire the guard.**

| Plan | Sentinel | Tirith |
| --- | --- | --- |
| `should-fail.json` (pure delete) | fail | exit 3 |
| `should-pass.json` (in-place update) | pass | exit 0 |
| `diverges.json` (replacement) | **fail** | **exit 0** |

Say this to the reader. A team that migrates a destroy guard and later sees a forced replacement
sail through will not think of it as a fidelity note.
