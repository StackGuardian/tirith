/**
 * SPECIMEN DATA — the live hero.
 *
 * Each specimen is a real Tirith policy, in real Tirith syntax, verified against
 * documentation/docs/tirith-providers/*.md and docs/tirith-reference/evaluators.md.
 * Nothing here invents a capability the tool does not have.
 *
 * The one axis (`condition.value`) is genuinely evaluated in the browser against the
 * specimen's items, using the same rule the evaluator reference states:
 *
 *   "The condition is applied to each value independently, and the evaluator passes
 *    only if every value passes."
 *
 * so the verdict the page shows is the verdict tirith would report for this document.
 *
 * SYNTHETIC: the `items` arrays are demonstration data standing in for a real
 * `terraform show -json` / `infracost breakdown` document. Resource addresses and
 * values are invented so the grid has something to move. They are labelled in the UI.
 * No claim, metric, customer or capability is invented anywhere in this file.
 */

// The placeholder the axis value is substituted into, so the renderer can find the
// one number the slider owns and mark it up without re-parsing the JSON.
export const AXIS_SLOT = '«VALUE»';

/*
 * READING THE POLICY
 *
 * A visitor who does not already write Tirith policies sees twenty-two lines of JSON
 * and no way in: `provider_args`, `operation_type` and `eval_expression` are not
 * guessable, and the page was asking them to infer the language from one sample.
 *
 * Every policy answers the same three questions in the same order, so each specimen
 * carries the answers in plain English. They are rendered as a three-part band above
 * the JSON, numbered 1-2-3, and the same numerals mark the matching regions of the
 * document — so the sentence and the syntax are visibly the same object, and no
 * paragraph has to explain the mapping.
 *
 * `test` takes the formatted axis value because that clause is the one the slider
 * rewrites: read the English, drag the number, watch both change.
 */
export const READING_STEPS = [
  {region: 'source', n: '1', label: 'Reads'},
  {region: 'subject', n: '2', label: 'Pulls out'},
  {region: 'test', n: '3', label: 'Passes only if'},
];

/*
 * Which region of the document each key belongs to. Regions are resolved by brace
 * depth at render time (see regionsFor in Specimen.js), so a key that opens a block
 * claims the whole block, including its closing brace.
 */
export const REGION_BY_KEY = {
  required_provider: 'source',
  provider_args: 'subject',
  condition: 'test',
};

const money = (n) => `$${n.toLocaleString('en-US')}`;

export const SPECIMENS = [
  {
    id: 'terraform_plan',
    chip: 'Terraform',
    chipSub: 'Plan & state',
    provider: 'stackguardian/terraform_plan',
    // What the provider hands the condition, in the provider's own vocabulary.
    returns: 'one value per matching resource instance',
    aggregate: false,
    input: 'plan.json',
    inputCommand: 'terraform show -json tfplan > plan.json',
    docPath: '/docs/tirith-providers/terraform-plan-provider/',
    axis: {
      label: 'condition.value',
      hint: 'LessThanEqualTo',
      min: 20,
      max: 500,
      step: 10,
      initial: 100,
      unit: 'GiB',
      format: (n) => `${n} GiB`,
    },
    itemUnit: 'GiB',
    itemLabel: 'size',
    reading: {
      source: 'the terraform plan',
      subject: 'the size of every aws_ebs_volume',
      test: (value) => `every one is ${value} or less`,
    },
    // Passes when the volume is at or below the axis value.
    passes: (item, axis) => item.value <= axis,
    policy: `{
  "meta": {
    "version": "v1",
    "required_provider": "stackguardian/terraform_plan"
  },
  "evaluators": [
    {
      "id": "volume_within_limit",
      "description": "No volume may exceed the standard size",
      "provider_args": {
        "operation_type": "attribute",
        "terraform_resource_type": "aws_ebs_volume",
        "terraform_resource_attribute": "size"
      },
      "condition": {
        "type": "LessThanEqualTo",
        "value": ${AXIS_SLOT}
      }
    }
  ],
  "eval_expression": "volume_within_limit"
}`,
    items: [
      {address: 'aws_ebs_volume.api_data', value: 40},
      {address: 'aws_ebs_volume.cache', value: 60},
      {address: 'aws_ebs_volume.search_index', value: 120},
      {address: 'aws_ebs_volume.metrics_cold', value: 400},
      {address: 'aws_ebs_volume.ledger_primary', value: 90},
      {address: 'aws_ebs_volume.media_ingest', value: 320},
      {address: 'aws_ebs_volume.session_store', value: 30},
      {address: 'aws_ebs_volume.registry_layers', value: 160},
      {address: 'aws_ebs_volume.warehouse_spill', value: 440},
      {address: 'aws_ebs_volume.vault_data', value: 45},
    ],
  },

  {
    id: 'infracost',
    chip: 'Infracost',
    chipSub: 'Cost breakdown',
    provider: 'stackguardian/infracost',
    returns: 'a single number — the sum of the selected resources',
    aggregate: true,
    input: 'infracost.json',
    inputCommand: 'infracost breakdown --path . --format json > infracost.json',
    docPath: '/docs/tirith-providers/infracost-provider/',
    axis: {
      label: 'condition.value',
      hint: 'LessThanEqualTo',
      min: 200,
      max: 4000,
      step: 50,
      initial: 1200,
      unit: 'USD/mo',
      format: (n) => `${money(n)}/mo`,
    },
    itemUnit: 'USD/mo',
    itemLabel: 'monthly cost',
    reading: {
      source: 'the Infracost estimate',
      subject: 'the total monthly cost of everything in it',
      test: (value) => `the total is ${value} or less`,
    },
    passes: null, // aggregate: the sum is the single value that is compared
    policy: `{
  "meta": {
    "version": "v1",
    "required_provider": "stackguardian/infracost"
  },
  "evaluators": [
    {
      "id": "monthly_cost_ceiling",
      "description": "The whole stack stays under the monthly ceiling",
      "provider_args": {
        "operation_type": "total_monthly_cost",
        "resource_type": ["*"]
      },
      "condition": {
        "type": "LessThanEqualTo",
        "value": ${AXIS_SLOT}
      }
    }
  ],
  "eval_expression": "monthly_cost_ceiling"
}`,
    items: [
      {address: 'aws_eks_cluster.platform', value: 219},
      {address: 'aws_eks_node_group.general', value: 486},
      {address: 'aws_rds_cluster.ledger', value: 372},
      {address: 'aws_elasticache_cluster.sessions', value: 98},
      {address: 'aws_nat_gateway.egress[0]', value: 34},
      {address: 'aws_nat_gateway.egress[1]', value: 34},
      {address: 'aws_lb.public', value: 23},
      {address: 'aws_opensearch_domain.search', value: 264},
      {address: 'aws_s3_bucket.media', value: 41},
      {address: 'aws_cloudfront_distribution.cdn', value: 87},
    ],
  },

  {
    id: 'kubernetes',
    chip: 'Kubernetes',
    chipSub: 'Manifests',
    provider: 'stackguardian/kubernetes',
    returns: 'one value per matching manifest path',
    aggregate: false,
    input: 'manifests.yml',
    inputCommand: 'helm template my-release ./chart > manifests.yml',
    docPath: '/docs/tirith-providers/kubernetes-provider/',
    axis: {
      label: 'condition.value',
      hint: 'GreaterThanEqualTo',
      min: 1,
      max: 6,
      step: 1,
      initial: 2,
      unit: 'replicas',
      format: (n) => `${n} replica${n === 1 ? '' : 's'}`,
    },
    itemUnit: '',
    itemLabel: 'spec.replicas',
    reading: {
      source: 'the Kubernetes manifests',
      subject: 'spec.replicas on every Deployment',
      test: (value) => `every one is ${value} or more`,
    },
    passes: (item, axis) => item.value >= axis,
    policy: `{
  "meta": {
    "version": "v1",
    "required_provider": "stackguardian/kubernetes"
  },
  "evaluators": [
    {
      "id": "no_single_replica_deployments",
      "description": "Every Deployment carries redundancy",
      "provider_args": {
        "operation_type": "attribute",
        "kubernetes_kind": "Deployment",
        "attribute_path": "spec.replicas"
      },
      "condition": {
        "type": "GreaterThanEqualTo",
        "value": ${AXIS_SLOT}
      }
    }
  ],
  "eval_expression": "no_single_replica_deployments"
}`,
    items: [
      {address: 'Deployment/api-gateway', value: 4},
      {address: 'Deployment/checkout', value: 3},
      {address: 'Deployment/ledger-writer', value: 2},
      {address: 'Deployment/notifications', value: 1},
      {address: 'Deployment/search-indexer', value: 1},
      {address: 'Deployment/media-transcoder', value: 6},
      {address: 'Deployment/webhooks', value: 2},
      {address: 'Deployment/admin-console', value: 1},
    ],
  },

  {
    id: 'json',
    chip: 'JSON',
    chipSub: 'Any document',
    provider: 'stackguardian/json',
    returns: 'one value per wildcard match',
    aggregate: false,
    input: 'service-catalog.json',
    inputCommand: 'cat service-catalog.json',
    docPath: '/docs/tirith-providers/json-provider/',
    axis: {
      label: 'condition.value',
      hint: 'GreaterThanEqualTo',
      min: 30,
      max: 100,
      step: 5,
      initial: 80,
      unit: '%',
      format: (n) => `${n}%`,
    },
    itemUnit: '%',
    itemLabel: 'coverage',
    reading: {
      source: 'service-catalog.json',
      subject: 'services.*.coverage — every match',
      test: (value) => `every one is ${value} or more`,
    },
    passes: (item, axis) => item.value >= axis,
    policy: `{
  "meta": {
    "version": "v1",
    "required_provider": "stackguardian/json"
  },
  "evaluators": [
    {
      "id": "coverage_floor",
      "description": "Every service meets the coverage floor",
      "provider_args": {
        "operation_type": "get_value",
        "key_path": "services.*.coverage"
      },
      "condition": {
        "type": "GreaterThanEqualTo",
        "value": ${AXIS_SLOT}
      }
    }
  ],
  "eval_expression": "coverage_floor"
}`,
    items: [
      {address: 'services.api-gateway', value: 91},
      {address: 'services.checkout', value: 84},
      {address: 'services.ledger', value: 96},
      {address: 'services.notifications', value: 62},
      {address: 'services.search', value: 73},
      {address: 'services.media', value: 45},
      {address: 'services.webhooks', value: 88},
      {address: 'services.billing', value: 67},
    ],
  },
];

/**
 * Evaluate a specimen at an axis value, the way tirith would.
 *
 * Per-item specimens: every extracted value must pass, so one failing resource
 * fails the evaluator. Aggregate specimens (infracost) extract exactly one value —
 * the sum — so the grid shows contributions, not verdicts, and only the total is
 * compared. That difference is real, and the UI says so rather than smoothing it.
 */
export function evaluate(specimen, axisValue) {
  if (specimen.aggregate) {
    const total = specimen.items.reduce((sum, item) => sum + item.value, 0);
    const passed = total <= axisValue;
    return {
      aggregate: true,
      total,
      passed,
      valuesExtracted: 1,
      failing: passed ? 0 : 1,
      results: specimen.items.map((item) => ({...item, passed: null})),
    };
  }

  const results = specimen.items.map((item) => ({
    ...item,
    passed: specimen.passes(item, axisValue),
  }));
  const failing = results.filter((r) => !r.passed).length;

  return {
    aggregate: false,
    total: null,
    passed: failing === 0,
    valuesExtracted: results.length,
    failing,
    results,
  };
}

/** `final_result` and the exit code tirith reports, from the evaluator reference. */
export function verdict(evaluation) {
  return evaluation.passed
    ? {finalResult: 'true', exit: 0, word: 'PASSED'}
    : {finalResult: 'false', exit: 3, word: 'FAILED'};
}

/* ---------------------------------------------------------------------------
 * The pretty-printed report, reproduced exactly.
 *
 * Format from src/tirith/prettyprinter.py (pretty_print_result_dict):
 *
 *     Check: <id>
 *       FAILED
 *         1. PASSED: <message>
 *         2. FAILED: <message>
 *
 *     Passed: 0 Failed: 1 Skipped: 0
 *
 *     Final expression used:
 *     -> <eval_expression>
 *
 * Messages come from the evaluator classes in src/tirith/core/evaluators/, and
 * values are wrapped in backticks by utils.json_format_value.
 *
 * Note what is NOT in any of these lines: the resource address. That is real,
 * and it is the reason `tirith ui` exists — the README says so in as many words.
 * ------------------------------------------------------------------------- */

const MESSAGES = {
  LessThanEqualTo: {
    pass: (a, b) => `\`${a}\` is less than equal to \`${b}\``,
    fail: (a, b) => `\`${a}\` is not less than or equal to \`${b}\``,
  },
  GreaterThanEqualTo: {
    pass: (a, b) => `\`${a}\` is greater than equal to \`${b}\``,
    fail: (a, b) => `\`${a}\` is not greater than or equal to \`${b}\``,
  },
};

export function commandLine(specimen) {
  return `tirith --fail-on-error -policy-path policy.json -input-path ${specimen.input}`;
}

export function resultLines(specimen, axisValue, evaluation) {
  const id = specimen.policy.match(/"id":\s*"([^"]+)"/)[1];
  const expr = specimen.policy.match(/"eval_expression":\s*"([^"]+)"/)[1];
  const msg = MESSAGES[specimen.axis.hint];
  const lines = [];

  lines.push({kind: evaluation.passed ? 'pass' : 'fail', text: `Check: ${id}`});
  lines.push({
    kind: evaluation.passed ? 'pass' : 'fail',
    text: `  ${evaluation.passed ? 'PASSED' : 'FAILED'}`,
  });

  if (specimen.aggregate) {
    // The provider summed everything into one value, so there is exactly one
    // result line — which is the point of the infracost specimen.
    lines.push({
      kind: evaluation.passed ? 'pass' : 'fail',
      text: `    1. ${evaluation.passed ? 'PASSED' : 'FAILED'}: ${
        evaluation.passed
          ? msg.pass(evaluation.total, axisValue)
          : msg.fail(evaluation.total, axisValue)
      }`,
    });
  } else {
    evaluation.results.forEach((r, i) => {
      lines.push({
        kind: r.passed ? 'pass' : 'fail',
        text: `    ${i + 1}. ${r.passed ? 'PASSED' : 'FAILED'}: ${
          r.passed ? msg.pass(r.value, axisValue) : msg.fail(r.value, axisValue)
        }`,
      });
    });
  }

  lines.push({kind: 'blank', text: ''});
  lines.push({
    kind: 'plain',
    text: `Passed: ${evaluation.passed ? 1 : 0} Failed: ${
      evaluation.passed ? 0 : 1
    } Skipped: 0`,
  });
  lines.push({kind: 'blank', text: ''});
  lines.push({kind: 'plain', text: 'Final expression used:'});
  lines.push({kind: 'dim', text: `-> ${expr}`});
  return lines;
}
