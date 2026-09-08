# restrict-instance-type: exact

`filter_attribute_not_in_list(resources, "instance_type", allowed_types)` returns the violators.
The Tirith condition is the desired state: `ContainedIn allowed_types`.

`param allowed_types` becomes `{{ var.allowed_types }}` and lives in `variables.json`, so the same
policy serves every environment. `error_tolerance: 1` skips a plan with no `aws_instance`, which is
what the Sentinel `length(...) is 0` did on an empty set.

| Plan | Sentinel | Tirith |
| --- | --- | --- |
| `should-fail.json` (an `m5.24xlarge`) | fail | exit 3 |
| `should-pass.json` | pass | exit 0 |
