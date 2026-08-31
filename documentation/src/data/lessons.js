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
export const PLAYGROUND_START = LESSONS[LESSONS.length - 1].policy;
