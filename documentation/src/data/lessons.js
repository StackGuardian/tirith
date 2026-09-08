/**
 * The guided sequence for /learn.
 *
 * Six steps that build one policy against one document, each adding exactly one
 * idea. Every policy here runs in the browser through tirithLite, so the result
 * shown beside a lesson is computed, never transcribed — a lesson cannot drift
 * out of sync with its own output.
 *
 * The document is invented; the syntax, the semantics and the messages are not.
 */

export const INPUT_DOC = `{
  "environment": "production",
  "region": "eu-central-1",
  "services": [
    {
      "name": "api",
      "replicas": 3,
      "public": true,
      "image": "ghcr.io/acme/api:1.4.2"
    },
    {
      "name": "worker",
      "replicas": 1,
      "public": false,
      "image": "ghcr.io/acme/worker:0.9.0"
    },
    {
      "name": "admin",
      "replicas": 2,
      "public": true,
      "image": "ghcr.io/acme/admin:latest"
    }
  ]
}`;

export const LESSONS = [
  {
    id: 'shell',
    n: '01',
    title: 'A policy is a document',
    teaches: 'meta · evaluators · eval_expression',
    body:
      'Every Tirith policy has the same three parts. `meta` names the provider that ' +
      'will read your input. `evaluators` is the list of checks. `eval_expression` ' +
      'says how their results combine into one verdict. Nothing here is a program: ' +
      'it is a description of what to look for.',
    aside:
      'The provider decides what kind of document you are allowed to feed in. ' +
      'stackguardian/json reads any JSON or YAML by key path, which is why it is ' +
      'the one this playground implements.',
    policy: `{
  "meta": {
    "version": "v1",
    "required_provider": "stackguardian/json"
  },
  "evaluators": [
    {
      "id": "right_region",
      "provider_args": {
        "operation_type": "get_value",
        "key_path": "region"
      },
      "condition": {
        "type": "Equals",
        "value": "eu-central-1"
      }
    }
  ],
  "eval_expression": "right_region"
}`,
    tryIt: 'Change the region to `us-east-1` and watch the verdict and the exit code move.',
  },

  {
    id: 'many',
    n: '02',
    title: 'One check, many values',
    teaches: 'wildcards · every value must pass',
    body:
      'A `*` in the key path iterates a list or a dict, and the provider returns one ' +
      'value per match. The condition then runs against **each value independently, ' +
      'and the evaluator passes only if every one passes.** Three services, three ' +
      'result lines, one verdict.',
    aside:
      'This is the rule that surprises people most often. A wildcard check is not ' +
      '"most of them are fine" — a single value that fails, fails the evaluator.',
    policy: `{
  "meta": {
    "version": "v1",
    "required_provider": "stackguardian/json"
  },
  "evaluators": [
    {
      "id": "redundant",
      "description": "Every service runs more than one replica",
      "provider_args": {
        "operation_type": "get_value",
        "key_path": "services.*.replicas"
      },
      "condition": {
        "type": "GreaterThanEqualTo",
        "value": 2
      }
    }
  ],
  "eval_expression": "redundant"
}`,
    tryIt: 'Drop the value to `1`. One failing line is the difference between exit 3 and exit 0.',
  },

  {
    id: 'combine',
    n: '03',
    title: 'Combining checks',
    teaches: '&& · || · grouping',
    body:
      'Give each check an `id`, then join them in `eval_expression`. `a && b` needs ' +
      'both, `a || b` needs either, and parentheses group. The expression is the one ' +
      'part of a policy you cannot derive from the checks themselves.',
    aside:
      'Because the expression names ids, it is also where a policy documents its own ' +
      'intent. Read the expression first when you are trying to understand someone ' +
      "else's rule.",
    policy: `{
  "meta": {
    "version": "v1",
    "required_provider": "stackguardian/json"
  },
  "evaluators": [
    {
      "id": "redundant",
      "provider_args": {
        "operation_type": "get_value",
        "key_path": "services.*.replicas"
      },
      "condition": {
        "type": "GreaterThanEqualTo",
        "value": 2
      }
    },
    {
      "id": "right_region",
      "provider_args": {
        "operation_type": "get_value",
        "key_path": "region"
      },
      "condition": {
        "type": "Equals",
        "value": "eu-central-1"
      }
    }
  ],
  "eval_expression": "redundant && right_region"
}`,
    tryIt: 'Swap `&&` for `||`. One passing check is now enough to carry the whole policy.',
  },

  {
    id: 'detector',
    n: '04',
    title: 'The detector that lies',
    teaches: '! · and the trap under it',
    body:
      'You want "no image on a floating tag". The tempting way: write a check that ' +
      'finds `:latest`, then negate it with `!`. The output below says PASSED — and ' +
      'it is wrong. Look at `admin` in the document. It is on `:latest`, and this ' +
      'policy just waved it through.',
    aside:
      'Because the condition runs against each value and the evaluator passes only ' +
      'if EVERY value passes, `uses_latest` can only pass when all three images are ' +
      '`:latest`. One normal image makes it false, and `!false` is true. The `!` is ' +
      'not the bug — the check underneath it is asking the wrong question.',
    policy: `{
  "meta": {
    "version": "v1",
    "required_provider": "stackguardian/json"
  },
  "evaluators": [
    {
      "id": "uses_latest",
      "description": "Finds images pinned to a floating tag",
      "provider_args": {
        "operation_type": "get_value",
        "key_path": "services.*.image"
      },
      "condition": {
        "type": "RegexMatch",
        "value": ":latest$"
      }
    }
  ],
  "eval_expression": "!uses_latest"
}`,
    tryIt:
      'Fix it: change the condition to `NotContains` with value `":latest"`, and change ' +
      'the expression to plain `no_floating_tag`. Now each image is judged on its own, ' +
      '`admin` fails, and the exit code is 3 — which is what you wanted all along.',
  },

  {
    id: 'tolerance',
    n: '05',
    title: 'When the path is not there',
    teaches: 'error_tolerance · a skip is not a pass',
    body:
      'If a key path matches nothing, that is an error, not a false. By default the ' +
      'check fails. Raise `error_tolerance` to 2 and the provider error is *skipped* ' +
      'instead — and a policy where every check skipped evaluated nothing at all, so ' +
      'it reports `final_result: null` and exits **1**, not 0.',
    aside:
      'A skip is not a pass. This is the distinction that separates a gate that is ' +
      'working from one that is quietly matching nothing.',
    policy: `{
  "meta": {
    "version": "v1",
    "required_provider": "stackguardian/json"
  },
  "evaluators": [
    {
      "id": "budget_set",
      "provider_args": {
        "operation_type": "get_value",
        "key_path": "billing.monthly_budget"
      },
      "condition": {
        "type": "LessThanEqualTo",
        "value": 5000,
        "error_tolerance": 2
      }
    }
  ],
  "eval_expression": "budget_set"
}`,
    tryIt:
      'Set `error_tolerance` to 0. The same missing path now fails the check and the ' +
      'exit code changes from 1 to 3 — different problems, different codes.',
  },

  {
    id: 'together',
    n: '06',
    title: 'The whole thing',
    teaches: 'a policy you would actually commit',
    body:
      'Four checks, a grouped expression, and a description on each so a failing run ' +
      'explains itself. This is the shape of a file you would put under ' +
      '`.tirith/policies` and point a pipeline at.',
    aside:
      'Note the tag check is the corrected form from step 04, not the `!` version. ' +
      'From here the only things that change are the provider and the key paths. The ' +
      'conditions, the expression language and the exit codes are the same for a ' +
      'terraform plan, a Kubernetes manifest or an Infracost breakdown.',
    policy: `{
  "meta": {
    "version": "v1",
    "required_provider": "stackguardian/json"
  },
  "evaluators": [
    {
      "id": "redundant",
      "description": "Every service runs more than one replica",
      "provider_args": {
        "operation_type": "get_value",
        "key_path": "services.*.replicas"
      },
      "condition": {
        "type": "GreaterThanEqualTo",
        "value": 2
      }
    },
    {
      "id": "no_floating_tag",
      "description": "No image may sit on a floating tag",
      "provider_args": {
        "operation_type": "get_value",
        "key_path": "services.*.image"
      },
      "condition": {
        "type": "NotContains",
        "value": ":latest"
      }
    },
    {
      "id": "right_region",
      "description": "Everything lands in the approved region",
      "provider_args": {
        "operation_type": "get_value",
        "key_path": "region"
      },
      "condition": {
        "type": "Equals",
        "value": "eu-central-1"
      }
    },
    {
      "id": "named",
      "description": "Every service carries a name",
      "provider_args": {
        "operation_type": "get_value",
        "key_path": "services.*.name"
      },
      "condition": {
        "type": "IsNotEmpty",
        "value": ""
      }
    }
  ],
  "eval_expression": "(redundant && named) && right_region && no_floating_tag"
}`,
    tryIt:
      'Fix the document instead of the policy: give the worker 2 replicas and pin admin ' +
      'to a real tag, and the whole thing goes green.',
  },
];

/** What the Playground opens on. */

/* ── stackguardian/terraform_plan ─────────────────────────────────────────────
 *
 * A different provider, deliberately taught after the json track rather than
 * instead of it: the conditions and eval_expression are already understood by
 * this point, so these lessons only have to teach what actually changes, which
 * is how the provider finds a value in the first place.
 *
 * The plan below is a real `terraform show -json` shape, trimmed to the keys the
 * provider reads. Every verdict on this page is computed from it in the browser.
 */

export const PLAN_DOC = `{
  "format_version": "1.2",
  "terraform_version": "1.9.5",
  "resource_changes": [
    {
      "address": "aws_db_instance.orders",
      "type": "aws_db_instance",
      "name": "orders",
      "change": {
        "actions": ["update"],
        "after": {
          "identifier": "orders",
          "storage_encrypted": true,
          "tags": {"Owner": "data"}
        }
      }
    },
    {
      "address": "aws_s3_bucket.assets",
      "type": "aws_s3_bucket",
      "name": "assets",
      "change": {
        "actions": ["create"],
        "after": {
          "bucket": "acme-assets",
          "acl": "private",
          "tags": {"Owner": "platform"}
        }
      }
    },
    {
      "address": "aws_s3_bucket.logs",
      "type": "aws_s3_bucket",
      "name": "logs",
      "change": {
        "actions": ["create"],
        "after": {
          "bucket": "acme-logs",
          "acl": "public-read",
          "tags": {"Owner": "platform"}
        }
      }
    },
    {
      "address": "aws_instance.runner",
      "type": "aws_instance",
      "name": "runner",
      "change": {
        "actions": ["update"],
        "after": {
          "instance_type": "t3.large",
          "tags": {"Owner": "ci"},
          "ebs_block_device": [
            {"device_name": "/dev/sdf", "encrypted": true},
            {"device_name": "/dev/sdg", "encrypted": false}
          ]
        }
      }
    }
  ]
}`;

export const TF_LESSONS = [
  {
    id: 'tf-shell',
    n: '01',
    title: 'A policy is a document',
    teaches: 'meta · evaluators · eval_expression',
    body:
      'Every Tirith policy has the same three parts. `meta` names the provider that will read ' +
      'your input. `evaluators` is the list of checks. `eval_expression` says how their ' +
      'results combine into one verdict. Nothing here is a program: it is a description of ' +
      'what to look for in a plan you are about to apply.',
    aside:
      'A plan is not a tree you walk, so there is no path here. It is a list of resource ' +
      'changes, and you address one by naming a **resource type** and an **attribute on it**. ' +
      'One database matches, so there is one result.',
    tryIt: 'Change the value to `false`. The verdict, the message and the exit code all move together.',
    policy: `{
  "meta": {
    "version": "v1",
    "required_provider": "stackguardian/terraform_plan"
  },
  "evaluators": [
    {
      "id": "db_encrypted",
      "provider_args": {
        "operation_type": "attribute",
        "terraform_resource_type": "aws_db_instance",
        "terraform_resource_attribute": "storage_encrypted"
      },
      "condition": {
        "type": "Equals",
        "value": true
      }
    }
  ],
  "eval_expression": "db_encrypted"
}`,
  },
  {
    id: 'tf-many',
    n: '02',
    title: 'One check, every matching resource',
    teaches: 'many results · every one must pass',
    body:
      'Name a type that matches more than one resource and the check runs against each of ' +
      'them separately. The evaluator passes only if **every** result passes, so you write ' +
      'the rule once and it covers the bucket somebody adds next month without you editing ' +
      'anything.',
    aside:
      'Two buckets, two results, and the failing one names the value that failed rather than ' +
      'just the rule. That is the difference between a report you can act on and a red cross.',
    tryIt: 'Change `acl` on `aws_s3_bucket.logs` to `private` and the whole plan passes.',
    policy: `{
  "meta": {
    "version": "v1",
    "required_provider": "stackguardian/terraform_plan"
  },
  "evaluators": [
    {
      "id": "buckets_private",
      "provider_args": {
        "operation_type": "attribute",
        "terraform_resource_type": "aws_s3_bucket",
        "terraform_resource_attribute": "acl"
      },
      "condition": {
        "type": "Equals",
        "value": "private"
      }
    }
  ],
  "eval_expression": "buckets_private"
}`,
  },
  {
    id: 'tf-every',
    n: '03',
    title: 'Every resource in the plan',
    teaches: '"*" · exclude_resource_types',
    body:
      '`"*"` as the resource type means every resource the plan touches, whatever it is. This ' +
      'is how you write the rules that are actually organisational policy rather than ' +
      'service-specific: everything must be owned, everything must be tagged, nothing may be ' +
      'created outside a region. `exclude_resource_types` carves out the ones that genuinely ' +
      'cannot comply.',
    aside:
      'Four resources, four results, in plan order. Note what the printed report does *not* ' +
      'say: results are numbered, not named, so `4. FAILED` means the fourth resource rather ' +
      'than `aws_instance.runner`. The address is carried in the `--json` output under `meta` ' +
      'and shown by `tirith ui`; putting it in the printed message is on the roadmap and has ' +
      'not shipped.',
    tryIt: 'Change one resource’s `Owner` tag to `""`, then count down the list to find which resource line 4 is.',
    policy: `{
  "meta": {
    "version": "v1",
    "required_provider": "stackguardian/terraform_plan"
  },
  "evaluators": [
    {
      "id": "everything_owned",
      "provider_args": {
        "operation_type": "attribute",
        "terraform_resource_type": "*",
        "terraform_resource_attribute": "tags.Owner",
        "exclude_resource_types": ["aws_iam_policy_document"]
      },
      "condition": {
        "type": "IsNotEmpty"
      }
    }
  ],
  "eval_expression": "everything_owned"
}`,
  },
  {
    id: 'tf-combine',
    n: '04',
    title: 'Combining checks',
    teaches: '&& · || · grouping',
    body:
      'Each evaluator has an `id`, and `eval_expression` combines those ids with `&&`, `||`, ' +
      '`!` and parentheses. That is the whole grammar. The evaluators do not know about each ' +
      'other; the expression is the only place their results meet.',
    aside:
      'Both checks run whatever the expression says, so you always see every result. The ' +
      'expression decides the single verdict at the end, and only that verdict reaches the ' +
      'exit code.',
    tryIt: 'Swap `&&` for `||`. One passing check is now enough to carry the whole policy, which is usually not what you want.',
    policy: `{
  "meta": {
    "version": "v1",
    "required_provider": "stackguardian/terraform_plan"
  },
  "evaluators": [
    {
      "id": "buckets_private",
      "provider_args": {
        "operation_type": "attribute",
        "terraform_resource_type": "aws_s3_bucket",
        "terraform_resource_attribute": "acl"
      },
      "condition": {
        "type": "Equals",
        "value": "private"
      }
    },
    {
      "id": "db_encrypted",
      "provider_args": {
        "operation_type": "attribute",
        "terraform_resource_type": "aws_db_instance",
        "terraform_resource_attribute": "storage_encrypted"
      },
      "condition": {
        "type": "Equals",
        "value": true
      }
    }
  ],
  "eval_expression": "buckets_private && db_encrypted"
}`,
  },
  {
    id: 'tf-action',
    n: '05',
    title: 'Gate the change, not the value',
    teaches: 'operation_type: action',
    body:
      'This is the operation with no equivalent in a document, and it is the reason a plan is ' +
      'worth reading at all. `action` does not ask what a resource *is*. It asks what ' +
      'Terraform is **about to do to it**: `create`, `update`, `delete`, `no-op`. A policy ' +
      'over actions gates the change itself, which is the only moment the damage is still ' +
      'preventable.',
    aside:
      'This is the shape of "no pull request may destroy a database". A resource can carry ' +
      'more than one action, and every one of them is checked, so a replacement, which ' +
      'terraform reports as delete then create, cannot slip past a rule written about ' +
      'creation.',
    tryIt: 'Change an `actions` array to `["delete"]` and watch a green plan turn red.',
    policy: `{
  "meta": {
    "version": "v1",
    "required_provider": "stackguardian/terraform_plan"
  },
  "evaluators": [
    {
      "id": "nothing_destroyed",
      "provider_args": {
        "operation_type": "action",
        "terraform_resource_type": "*"
      },
      "condition": {
        "type": "NotEquals",
        "value": "delete"
      }
    }
  ],
  "eval_expression": "nothing_destroyed"
}`,
  },
  {
    id: 'tf-nested',
    n: '06',
    title: 'Reaching inside a resource',
    teaches: 'nested attributes · one result per element',
    body:
      'Real resources are not flat. A block that repeats, like `ebs_block_device`, arrives as ' +
      'a list, and `.*.` walks into it. Each element becomes its **own result**, so one ' +
      'attached volume that is unencrypted fails the check even though its neighbour on the ' +
      'same instance is fine.',
    aside:
      'Remember this shape. The Kubernetes provider spells its wildcard the same way and ' +
      'means something different by it, which is the subject of the last lesson in that ' +
      'track and the easiest way on this whole site to write a policy that gates nothing.',
    tryIt: 'Set both `encrypted` values to `true`. Then delete the `.*.` and see the attribute stop resolving.',
    policy: `{
  "meta": {
    "version": "v1",
    "required_provider": "stackguardian/terraform_plan"
  },
  "evaluators": [
    {
      "id": "volumes_encrypted",
      "provider_args": {
        "operation_type": "attribute",
        "terraform_resource_type": "aws_instance",
        "terraform_resource_attribute": "ebs_block_device.*.encrypted"
      },
      "condition": {
        "type": "Equals",
        "value": true
      }
    }
  ],
  "eval_expression": "volumes_encrypted"
}`,
  },
  {
    id: 'tf-tolerance',
    n: '07',
    title: 'When the attribute is not there',
    teaches: 'error_tolerance · a skip is not a pass',
    body:
      'Nothing in this plan sets `server_side_encryption`, so the provider cannot produce a ' +
      'value to judge. That is not a violation, and it is not compliance either. Tirith ' +
      'reports it as an **error with a severity**, and `error_tolerance` decides whether that ' +
      'error fails the check or skips it.',
    aside:
      'Severity 1 means the resource type is not in the plan. Severity 2 means the resource ' +
      'is there but the attribute is not. `severity > tolerance` fails, anything else skips. ' +
      'With every check skipped the verdict is neither true nor false, and the exit code is ' +
      '`1`, not `0`: a policy that evaluated nothing must never look like a policy that ' +
      'passed.',
    tryIt: 'Drop `error_tolerance` to `1`. The skip becomes a failure and the exit code changes from 1 to 3.',
    policy: `{
  "meta": {
    "version": "v1",
    "required_provider": "stackguardian/terraform_plan"
  },
  "evaluators": [
    {
      "id": "bucket_encryption",
      "provider_args": {
        "operation_type": "attribute",
        "terraform_resource_type": "aws_s3_bucket",
        "terraform_resource_attribute": "server_side_encryption"
      },
      "condition": {
        "type": "Equals",
        "value": "AES256",
        "error_tolerance": 2
      }
    }
  ],
  "eval_expression": "bucket_encryption"
}`,
  },
  {
    id: 'tf-count',
    n: '08',
    title: 'Zero is an answer',
    teaches: 'operation_type: count · and the error that does not happen',
    body:
      '`count` returns one number: how many resources of a type this change touches. The ' +
      'detail worth knowing is what it does **not** do. Every other operation reports an ' +
      'error when the resource type is absent from the plan, and that error can fail your ' +
      'check. `count` reports `0`, because zero of something is a real answer and usually ' +
      'the one you are gating on.',
    aside:
      'Two buckets, so this fails. The same policy against a plan with no buckets at all ' +
      'returns `0` and passes, with no error and no skip. Worth knowing before you reach for ' +
      '`count` as a safety net: it cannot tell you that it looked and found nothing.',
    tryIt: 'Raise the value to `2` and it passes. Then delete both buckets from the plan: still passing, on `0`.',
    policy: `{
  "meta": {
    "version": "v1",
    "required_provider": "stackguardian/terraform_plan"
  },
  "evaluators": [
    {
      "id": "bucket_budget",
      "provider_args": {
        "operation_type": "count",
        "terraform_resource_type": "aws_s3_bucket"
      },
      "condition": {
        "type": "LessThanEqualTo",
        "value": 1
      }
    }
  ],
  "eval_expression": "bucket_budget"
}`,
  },
  {
    id: 'tf-together',
    n: '09',
    title: 'The whole thing',
    teaches: 'a policy you would actually commit',
    body:
      'Four rules over one plan: everything is owned, buckets are private, attached volumes ' +
      'are encrypted, and nothing is destroyed. This is the size of a real starting policy, ' +
      'and it is the file you would put in `.tirith/policies` and point a pipeline at.',
    aside:
      'The report tells you which rule refused and which value refused it, which is what ' +
      'makes a red build actionable rather than a thing to re-run. Under `--fail-on-error` ' +
      'this exits `3`, and the pipeline stops before `apply`.',
    tryIt: 'Fix the plan until it passes: `logs` to private, and the second volume encrypted. The exit code goes to 0.',
    policy: `{
  "meta": {
    "version": "v1",
    "required_provider": "stackguardian/terraform_plan"
  },
  "evaluators": [
    {
      "id": "everything_owned",
      "provider_args": {
        "operation_type": "attribute",
        "terraform_resource_type": "*",
        "terraform_resource_attribute": "tags.Owner"
      },
      "condition": {
        "type": "IsNotEmpty"
      }
    },
    {
      "id": "buckets_private",
      "provider_args": {
        "operation_type": "attribute",
        "terraform_resource_type": "aws_s3_bucket",
        "terraform_resource_attribute": "acl"
      },
      "condition": {
        "type": "Equals",
        "value": "private"
      }
    },
    {
      "id": "volumes_encrypted",
      "provider_args": {
        "operation_type": "attribute",
        "terraform_resource_type": "aws_instance",
        "terraform_resource_attribute": "ebs_block_device.*.encrypted"
      },
      "condition": {
        "type": "Equals",
        "value": true
      }
    },
    {
      "id": "nothing_destroyed",
      "provider_args": {
        "operation_type": "action",
        "terraform_resource_type": "*"
      },
      "condition": {
        "type": "NotEquals",
        "value": "delete"
      }
    }
  ],
  "eval_expression": "everything_owned && buckets_private && volumes_encrypted && nothing_destroyed"
}`,
  },
];

/* ── stackguardian/kubernetes ─────────────────────────────────────────────────
 *
 * The CLI reads a multi-document YAML file and hands the provider a list of
 * manifests. The playground parses JSON, so the same manifests are written as a
 * JSON array here. Nothing else differs: the provider iterates a list either way.
 */

export const K8S_DOC = `[
  {
    "apiVersion": "apps/v1",
    "kind": "Deployment",
    "metadata": {"name": "api", "namespace": "production"},
    "spec": {
      "replicas": 3,
      "template": {
        "spec": {
          "containers": [
            {
              "name": "api",
              "image": "ghcr.io/acme/api:1.4.2",
              "resources": {"limits": {"cpu": "500m", "memory": "512Mi"}},
              "securityContext": {"runAsNonRoot": true, "allowPrivilegeEscalation": false},
              "readinessProbe": {"httpGet": {"path": "/healthz", "port": 8080}}
            }
          ]
        }
      }
    }
  },
  {
    "apiVersion": "apps/v1",
    "kind": "Deployment",
    "metadata": {"name": "worker", "namespace": "production"},
    "spec": {
      "replicas": 1,
      "template": {
        "spec": {
          "containers": [
            {
              "name": "worker",
              "image": "docker.io/library/redis:latest",
              "securityContext": {"runAsNonRoot": false}
            }
          ]
        }
      }
    }
  },
  {
    "apiVersion": "v1",
    "kind": "Service",
    "metadata": {"name": "api", "namespace": "production"},
    "spec": {"type": "ClusterIP", "ports": [{"port": 80, "targetPort": 8080}]}
  }
]`;

export const K8S_LESSONS = [
  {
    id: 'k8s-kind',
    n: '01',
    title: 'Pick a kind, then a path',
    teaches: 'kubernetes_kind · attribute_path',
    body:
      'Kubernetes input is a list of manifests, so the provider needs two things: which `kind` ' +
      'to look at, and where inside it to look. Manifests of other kinds are ignored rather ' +
      'than failed, which is what lets one policy run against a whole directory of YAML. The ' +
      '`Service` in this document is simply not consulted.',
    aside:
      'Two Deployments match, so there are two results. `api` is fine and `worker` is not, ' +
      'which is the pattern for this whole track: one bad Deployment, and each lesson catches ' +
      'a different thing wrong with it.',
    tryIt:
      'Give `worker` 2 replicas and the check passes. Then change the kind to `Service`: it has no ' +
      '`spec.replicas`, so the value is null and the failure you get is about comparing types, not ' +
      'about a missing path.',
    policy: `{
  "meta": {
    "version": "v1",
    "required_provider": "stackguardian/kubernetes"
  },
  "evaluators": [
    {
      "id": "not_a_single_point",
      "provider_args": {
        "operation_type": "attribute",
        "kubernetes_kind": "Deployment",
        "attribute_path": "spec.replicas"
      },
      "condition": {
        "type": "GreaterThanEqualTo",
        "value": 2
      }
    }
  ],
  "eval_expression": "not_a_single_point"
}`,
  },
  {
    id: 'k8s-two-kinds',
    n: '02',
    title: 'One policy, two kinds',
    teaches: 'several evaluators · && · || · grouping',
    body:
      'One evaluator reads one kind, so a policy that spans Deployments and Services is two ' +
      'evaluators and an expression. Each has an `id`, and `eval_expression` combines those ' +
      'ids with `&&`, `||`, `!` and parentheses. That is the whole grammar; the evaluators ' +
      'never see each other.',
    aside:
      'Both checks run whatever the expression says, so you always see every result: the ' +
      'Service passes, a Deployment does not, and the expression turns those into one verdict ' +
      'at the end. Only that verdict reaches the exit code.',
    tryIt: 'Swap `&&` for `||`. The passing Service now carries the whole policy, which is almost never what you meant.',
    policy: `{
  "meta": {
    "version": "v1",
    "required_provider": "stackguardian/kubernetes"
  },
  "evaluators": [
    {
      "id": "not_a_single_point",
      "provider_args": {
        "operation_type": "attribute",
        "kubernetes_kind": "Deployment",
        "attribute_path": "spec.replicas"
      },
      "condition": {
        "type": "GreaterThanEqualTo",
        "value": 2
      }
    },
    {
      "id": "not_exposed",
      "provider_args": {
        "operation_type": "attribute",
        "kubernetes_kind": "Service",
        "attribute_path": "spec.type"
      },
      "condition": {
        "type": "NotEquals",
        "value": "LoadBalancer"
      }
    }
  ],
  "eval_expression": "not_a_single_point && not_exposed"
}`,
  },
  {
    id: 'k8s-registry',
    n: '03',
    title: 'Where the image came from',
    teaches: 'indexing into containers · RegexMatch',
    body:
      'Containers are a list, so reaching one means indexing it: `containers.0` is the first ' +
      'container in the pod template. `RegexMatch` then does what an allowlist needs, which is ' +
      'to say where an image may come from rather than enumerating every image you have ever ' +
      'approved.',
    aside:
      'An unpinned public image is the supply-chain problem stated plainly: `worker` pulls ' +
      'from Docker Hub, so anything that lands under that name lands in your cluster. The ' +
      'regex is anchored with `^` on purpose; without it, `ghcr.io/acme/` would match anywhere ' +
      'in the string and `evil.example.com/ghcr.io/acme/x` would pass.',
    tryIt: 'Point `worker` at `ghcr.io/acme/worker:0.9.0` and the check passes. Then drop the `^` and see what else it lets through.',
    policy: `{
  "meta": {
    "version": "v1",
    "required_provider": "stackguardian/kubernetes"
  },
  "evaluators": [
    {
      "id": "approved_registry",
      "provider_args": {
        "operation_type": "attribute",
        "kubernetes_kind": "Deployment",
        "attribute_path": "spec.template.spec.containers.0.image"
      },
      "condition": {
        "type": "RegexMatch",
        "value": "^ghcr\\\\.io/acme/"
      }
    }
  ],
  "eval_expression": "approved_registry"
}`,
  },
  {
    id: 'k8s-wildcard',
    n: '04',
    title: 'The same star, a different meaning',
    teaches: 'why a passing policy can still be wrong',
    body:
      'Put `*` in a Kubernetes `attribute_path` and you do **not** get one value per match. ' +
      'You get a single value that is the whole list. That matters because `Contains` on a ' +
      'list is membership, not substring: `":latest"` is not an element of ' +
      '`["docker.io/library/redis:latest"]`, so the check below **passes** while an image ' +
      'really is pinned to `latest`. A green policy that gates nothing.',
    aside:
      'Terraform’s `.*.` does the opposite: it emits one result per element, which is why the ' +
      'same instinct works there and fails here. Naming a container fixes it, at the cost of ' +
      'only checking that one. This is why "the check is green" and "the check is working" ' +
      'are different claims, and why the last lesson here evaluates a policy against a ' +
      'manifest that should fail it.',
    tryIt: 'Change `containers.*.image` to `containers.0.image`. The verdict flips to failed and names the image.',
    policy: `{
  "meta": {
    "version": "v1",
    "required_provider": "stackguardian/kubernetes"
  },
  "evaluators": [
    {
      "id": "no_latest_tag",
      "provider_args": {
        "operation_type": "attribute",
        "kubernetes_kind": "Deployment",
        "attribute_path": "spec.template.spec.containers.*.image"
      },
      "condition": {
        "type": "NotContains",
        "value": ":latest"
      }
    }
  ],
  "eval_expression": "no_latest_tag"
}`,
  },
  {
    id: 'k8s-limits',
    n: '05',
    title: 'A missing path is not an error here',
    teaches: 'resource limits · null instead of a severity',
    body:
      'A container with no memory limit can take the node down and everything scheduled on it ' +
      'with it, so this is the check most clusters want first. It also shows the sharpest ' +
      'difference between this provider and the Terraform one: `worker` has no `resources` at ' +
      'all, and instead of an error with a severity, the provider returns **null** and the ' +
      'condition judges that.',
    aside:
      'That distinction decides what `error_tolerance` can do for you. In a plan, a missing ' +
      'attribute is severity 2 and can be tolerated into a skip. Here it is an ordinary value ' +
      'that fails an `IsNotEmpty`, and no tolerance setting will turn it into a skip. Which is ' +
      'the safer default: absence is a failure unless you say otherwise.',
    tryIt: 'Add `"resources": {"limits": {"memory": "256Mi"}}` to the worker container and the policy passes.',
    policy: `{
  "meta": {
    "version": "v1",
    "required_provider": "stackguardian/kubernetes"
  },
  "evaluators": [
    {
      "id": "memory_limited",
      "provider_args": {
        "operation_type": "attribute",
        "kubernetes_kind": "Deployment",
        "attribute_path": "spec.template.spec.containers.0.resources.limits.memory"
      },
      "condition": {
        "type": "IsNotEmpty"
      }
    }
  ],
  "eval_expression": "memory_limited"
}`,
  },
  {
    id: 'k8s-security',
    n: '06',
    title: 'Running as root, by default',
    teaches: 'securityContext · two rules over one container',
    body:
      'Kubernetes defaults are permissive: unless a manifest says otherwise, a container runs ' +
      'as whatever user its image declares, which is very often root, and may escalate ' +
      'privileges. These are the two settings that a cluster policy almost always pins, and ' +
      'they are the rules that survive contact with an image you did not build.',
    aside:
      '`worker` sets `runAsNonRoot: false` explicitly, so it fails. A manifest that omits ' +
      '`securityContext` entirely returns null and fails the same way, which is the behaviour ' +
      'you want: a container is not non-root because nobody mentioned it.',
    tryIt: 'Set `runAsNonRoot` to `true` on `worker`. It still fails, because that container has no `allowPrivilegeEscalation` at all.',
    policy: `{
  "meta": {
    "version": "v1",
    "required_provider": "stackguardian/kubernetes"
  },
  "evaluators": [
    {
      "id": "non_root",
      "provider_args": {
        "operation_type": "attribute",
        "kubernetes_kind": "Deployment",
        "attribute_path": "spec.template.spec.containers.0.securityContext.runAsNonRoot"
      },
      "condition": {
        "type": "Equals",
        "value": true
      }
    },
    {
      "id": "no_escalation",
      "provider_args": {
        "operation_type": "attribute",
        "kubernetes_kind": "Deployment",
        "attribute_path": "spec.template.spec.containers.0.securityContext.allowPrivilegeEscalation"
      },
      "condition": {
        "type": "Equals",
        "value": false
      }
    }
  ],
  "eval_expression": "non_root && no_escalation"
}`,
  },
  {
    id: 'k8s-tolerance',
    n: '07',
    title: 'When the kind is not there',
    teaches: 'error_tolerance · a skip is not a pass',
    body:
      'A missing *path* returns null here, but a missing **kind** is different: the provider ' +
      'cannot look at anything at all, so it reports an error with severity 1. This document ' +
      'has no `Ingress`, and that is the situation `error_tolerance` exists for. One policy ' +
      'set runs across many repositories, and not every repository has every kind.',
    aside:
      '`severity > tolerance` fails, anything else skips. At tolerance 1 the check is skipped, ' +
      'and because it is the only check, the verdict is neither true nor false and the exit ' +
      'code is `1` rather than `0`. A policy that evaluated nothing must never look like a ' +
      'policy that passed.',
    tryIt: 'Drop `error_tolerance` to `0`. The skip becomes a failure and the exit code changes from 1 to 3.',
    policy: `{
  "meta": {
    "version": "v1",
    "required_provider": "stackguardian/kubernetes"
  },
  "evaluators": [
    {
      "id": "ingress_is_tls",
      "provider_args": {
        "operation_type": "attribute",
        "kubernetes_kind": "Ingress",
        "attribute_path": "spec.tls"
      },
      "condition": {
        "type": "IsNotEmpty",
        "error_tolerance": 1
      }
    }
  ],
  "eval_expression": "ingress_is_tls"
}`,
  },
  {
    id: 'k8s-together',
    n: '08',
    title: 'The whole thing',
    teaches: 'a policy you would actually commit',
    body:
      'Five rules over one directory of manifests: every Deployment is replicated, pulls from ' +
      'an approved registry, pins a memory limit, runs as non-root, and no Service is exposed ' +
      'to the internet. This is the size of a real starting policy, and it is the file you ' +
      'would put in `.tirith/policies` and point at `kubectl kustomize` output.',
    aside:
      'The report names the rule that refused and the value that refused it, so a red build ' +
      'tells you which manifest to open. Under `--fail-on-error` this exits `3`, before ' +
      '`kubectl apply` ever runs.',
    tryIt: 'Fix `worker` until it passes: 2 replicas, a ghcr.io image, a memory limit, and runAsNonRoot true.',
    policy: `{
  "meta": {
    "version": "v1",
    "required_provider": "stackguardian/kubernetes"
  },
  "evaluators": [
    {
      "id": "not_a_single_point",
      "provider_args": {
        "operation_type": "attribute",
        "kubernetes_kind": "Deployment",
        "attribute_path": "spec.replicas"
      },
      "condition": {
        "type": "GreaterThanEqualTo",
        "value": 2
      }
    },
    {
      "id": "approved_registry",
      "provider_args": {
        "operation_type": "attribute",
        "kubernetes_kind": "Deployment",
        "attribute_path": "spec.template.spec.containers.0.image"
      },
      "condition": {
        "type": "RegexMatch",
        "value": "^ghcr\\\\.io/acme/"
      }
    },
    {
      "id": "memory_limited",
      "provider_args": {
        "operation_type": "attribute",
        "kubernetes_kind": "Deployment",
        "attribute_path": "spec.template.spec.containers.0.resources.limits.memory"
      },
      "condition": {
        "type": "IsNotEmpty"
      }
    },
    {
      "id": "non_root",
      "provider_args": {
        "operation_type": "attribute",
        "kubernetes_kind": "Deployment",
        "attribute_path": "spec.template.spec.containers.0.securityContext.runAsNonRoot"
      },
      "condition": {
        "type": "Equals",
        "value": true
      }
    },
    {
      "id": "not_exposed",
      "provider_args": {
        "operation_type": "attribute",
        "kubernetes_kind": "Service",
        "attribute_path": "spec.type"
      },
      "condition": {
        "type": "NotEquals",
        "value": "LoadBalancer"
      }
    }
  ],
  "eval_expression": "not_a_single_point && approved_registry && memory_limited && non_root && not_exposed"
}`,
  },
];

/**
 * The page, as tracks.
 *
 * Each track is a provider, its own input document, and the lessons that run
 * against it. The numbering is continuous across the page rather than restarting
 * per track, which is the section grammar the rest of the site uses.
 */
export const TRACKS = [
  {
    id: 'terraform',
    provider: 'stackguardian/terraform_plan',
    tab: 'Terraform plan',
    title: 'An OpenTofu or Terraform plan',
    lede:
      'The provider Tirith exists for, and the one to learn on. Nine lessons that build one ' +
      'policy a rule at a time, against a plan of the shape your pipeline already produces ' +
      'with `terraform show -json`.',
    /*
     * What the track teaches, for the reader deciding which one to open. Deliberately not a
     * summary of the lessons: it is the reason to pick this track over the other two.
     */
    forYou: 'Start here. The syntax you learn on a plan is the same syntax everywhere else.',
    input: PLAN_DOC,
    lessons: TF_LESSONS,
    /*
     * The playground opens on the track's most representative *correct* policy, which is not
     * always its last lesson. The Kubernetes track ends on a policy that deliberately passes
     * while being wrong, and seeding an empty-canvas playground with that would be handing
     * the reader the trap with none of the explanation attached.
     */
    playground: TF_LESSONS[TF_LESSONS.length - 1].policy,
  },
  {
    id: 'kubernetes',
    provider: 'stackguardian/kubernetes',
    tab: 'Kubernetes',
    title: 'Kubernetes manifests',
    lede:
      'A list of manifests rather than one document. Eight lessons over two Deployments and a ' +
      'Service, one of which is a mess: replicas, registries, limits, `securityContext`, and ' +
      'the wildcard that behaves the opposite way to the one in the Terraform track.',
    forYou: 'Eight lessons. Lesson 04 is the most useful mistake on this site.',
    input: K8S_DOC,
    lessons: K8S_LESSONS,
    playground: K8S_LESSONS[0].policy,
  },
  {
    id: 'json',
    provider: 'stackguardian/json',
    tab: 'JSON or YAML',
    title: 'Any JSON or YAML document',
    lede:
      'The provider that reads anything with keys and values, addressed by key path. Useful ' +
      'for the documents nobody wrote a provider for: a lockfile, an SBOM, a config file, ' +
      'the response from one of your own APIs.',
    forYou: 'Six lessons. Come here when the thing you need to gate is not IaC at all.',
    input: INPUT_DOC,
    lessons: LESSONS,
    playground: LESSONS[LESSONS.length - 1].policy,
  },
];

/*
 * Superseded by each track's own `playground` seed, and kept only long enough to say so:
 * nothing imports this. Delete it on the next pass through this file.
 */
export const PLAYGROUND_START = TRACKS[0].playground;
