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
          "tags": {}
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
          "tags": {"Owner": "ci"}
        }
      }
    }
  ]
}`;

export const TF_LESSONS = [
  {
    id: 'tf-attribute',
    n: '07',
    title: 'A plan is not a document',
    teaches: 'terraform_resource_type · terraform_resource_attribute',
    body:
      'Everything you have learned still applies. The conditions are the same thirteen and ' +
      'the expression grammar is unchanged. What changes is the address: there is no ' +
      '`key_path` here, because a plan is not a tree you walk. It is a list of resource ' +
      'changes, so you name a **resource type** and an **attribute on it**, and the provider ' +
      'returns one value per matching resource.',
    aside:
      'Two buckets match, so one evaluator produces two results and the failing one names ' +
      'the value that failed. `"*"` as the resource type means every resource in the plan, ' +
      'and `exclude_resource_types` narrows that back down. A missing resource type is an ' +
      'error of severity 1, a missing attribute is severity 2, which is why error_tolerance ' +
      'can tell "you have no buckets" apart from "your bucket has no acl".',
    tryIt: 'Change `acl` on `aws_s3_bucket.logs` to `private`, and the whole plan passes.',
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
    id: 'tf-action',
    n: '08',
    title: 'Gate the change, not the value',
    teaches: 'operation_type: action',
    body:
      'This is the operation with no equivalent in the json world, and it is the reason a ' +
      'plan is worth reading at all. `action` does not ask what a resource *is*. It asks ' +
      'what Terraform is **about to do to it**: `create`, `update`, `delete`, `no-op`. A ' +
      'policy over actions gates the change itself, which is the only moment the damage is ' +
      'still preventable.',
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
    id: 'tf-count',
    n: '09',
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
      'returns `0` and passes, with no error and no skip. Worth knowing before you reach ' +
      'for `count` as a safety net: it cannot tell you that it looked and found nothing.',
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
    "metadata": {"name": "api"},
    "spec": {
      "replicas": 3,
      "template": {
        "spec": {
          "containers": [
            {"name": "api", "image": "ghcr.io/acme/api:1.4.2"}
          ]
        }
      }
    }
  },
  {
    "apiVersion": "apps/v1",
    "kind": "Deployment",
    "metadata": {"name": "worker"},
    "spec": {
      "replicas": 1,
      "template": {
        "spec": {
          "containers": [
            {"name": "worker", "image": "ghcr.io/acme/worker:latest"}
          ]
        }
      }
    }
  },
  {
    "apiVersion": "v1",
    "kind": "Service",
    "metadata": {"name": "api"},
    "spec": {"type": "LoadBalancer"}
  }
]`;

export const K8S_LESSONS = [
  {
    id: 'k8s-kind',
    n: '10',
    title: 'Pick a kind, then a path',
    teaches: 'kubernetes_kind · attribute_path',
    body:
      'Kubernetes input is a list of manifests, so the provider needs two things: which ' +
      '`kind` to look at, and where inside it to look. Manifests of other kinds are ignored ' +
      'rather than failed, which is what lets one policy run against a whole directory of ' +
      'YAML. The `Service` in this document is simply not consulted.',
    aside:
      'Two Deployments match, so there are two results and the single-replica one fails. ' +
      'A kind that appears nowhere is an error of severity 1, so `error_tolerance: 1` turns ' +
      '"this repository has no Ingress" from a failure into a skip.',
    tryIt: 'Give `worker` 2 replicas and it passes. Change the kind to `Ingress` to see the severity 1 error instead.',
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
    id: 'k8s-wildcard',
    n: '11',
    title: 'The same star, a different meaning',
    teaches: 'why a passing policy can still be wrong',
    body:
      'Put `*` in a Kubernetes `attribute_path` and you do **not** get one value per match. ' +
      'You get a single value that is the whole list. That matters because `Contains` on a ' +
      'list is membership, not substring: `":latest"` is not an element of ' +
      '`["ghcr.io/acme/worker:latest"]`, so the check below passes while an image really is ' +
      'pinned to `latest`. A green policy that gates nothing.',
    aside:
      'Terraform’s `.*.` does the opposite: it emits one result per element, which is why ' +
      'the same instinct works there and fails here. Naming a container fixes it, at the ' +
      'cost of only checking that one. This is the failure the whole site is about, and it ' +
      'is why "the check is green" and "the check is working" are different claims.',
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
    id: 'json',
    provider: 'stackguardian/json',
    title: 'Any JSON or YAML document',
    lede:
      'The provider to learn first, because it reads anything with keys and values and gets ' +
      'out of the way of the syntax you are actually learning.',
    input: INPUT_DOC,
    lessons: LESSONS,
  },
  {
    id: 'terraform',
    provider: 'stackguardian/terraform_plan',
    title: 'An OpenTofu or Terraform plan',
    lede:
      'The provider the tool exists for. Same conditions, same expressions; what changes is ' +
      'that you address a resource type and an attribute instead of a path, and that you can ' +
      'gate on what the change is about to do.',
    input: PLAN_DOC,
    lessons: TF_LESSONS,
  },
  {
    id: 'kubernetes',
    provider: 'stackguardian/kubernetes',
    title: 'Kubernetes manifests',
    lede:
      'A list of manifests rather than one document, and one wildcard that behaves the ' +
      'opposite way to the one you just learned.',
    input: K8S_DOC,
    lessons: K8S_LESSONS,
  },
];

export const PLAYGROUND_START = LESSONS[LESSONS.length - 1].policy;
