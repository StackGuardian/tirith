/**
 * tirith-lite — a teaching reimplementation of Tirith's evaluation core.
 *
 * ─────────────────────────────────────────────────────────────────────────────
 * WHAT THIS IS, PRECISELY
 *
 * This is NOT Tirith. Tirith is a Python package; this is a few hundred lines of
 * JavaScript that reproduces three providers and thirteen conditions closely
 * enough to teach the shape of a policy in a browser, with no install.
 *
 * It is written against the real thing and matches it where it matters:
 *   - result documents have the same shape as `tirith --json` (see
 *     documentation/docs/tirith-usage/cli-reference.md);
 *   - condition messages are the strings from src/tirith/core/evaluators/*.py,
 *     with values wrapped in backticks by the same rule as utils.json_format_value;
 *   - "the condition is applied to each value independently, and the evaluator
 *     passes only if every value passes" (docs/tirith-reference/evaluators.md);
 *   - `passed` and `final_result` are tri-state: true / false / null-for-skipped.
 *
 * VERIFIED AGAINST THE ENGINE. Every policy on /learn was run through both this
 * file and the installed Python package, and all eleven produce the same
 * final_result and the same per-result outcomes. Re-run that comparison when you
 * change anything below: a teaching engine that quietly disagrees with the real
 * one is worse than no playground, because it is believed.
 *
 * KNOWN DIVERGENCES, say these out loud in the UI, never paper over them:
 *   - `stackguardian/json`, `stackguardian/terraform_plan` and
 *     `stackguardian/kubernetes` are implemented. infracost and sg_workflow are
 *     not, and neither are the terraform_plan operations beyond attribute,
 *     action and count: direct_references, direct_dependencies, provider_config
 *     and terraform_version all run only in the package.
 *   - Messages are formatted by this file's `fmt`, so a value is shown as JSON in
 *     backticks where the Python sometimes shows a repr. Same verdict, different
 *     punctuation.
 *   - `Equals` does not sort nested collections the way the Python does.
 *   - Regexes are JavaScript regexes, not Python's `re`.
 *   - An evaluator whose results are a mix of failures and skips is reported as
 *     failed here. core.py reports it as skipped when the skip comes last, which
 *     is the ordering defect the roadmap's R1 item covers. This file implements
 *     the intended rule rather than the current one, deliberately.
 *
 * The authoritative evaluator is always the installed package.
 * ─────────────────────────────────────────────────────────────────────────────
 */

/** Values are shown in messages as JSON, in backticks. utils.json_format_value. */
function fmt(value) {
  try {
    return '`' + JSON.stringify(value) + '`';
  } catch {
    return '`' + String(value) + '`';
  }
}

const isStr = (v) => typeof v === 'string';
const isList = (v) => Array.isArray(v);
const isDict = (v) => v !== null && typeof v === 'object' && !Array.isArray(v);

function contains(haystack, needle) {
  if (isStr(haystack)) return isStr(needle) && haystack.includes(needle);
  if (isList(haystack)) return haystack.some((x) => deepEq(x, needle));
  if (isDict(haystack)) return Object.keys(haystack).some((k) => deepEq(k, needle));
  return null; // unsupported type
}

function deepEq(a, b) {
  if (a === b) return true;
  if (typeof a === 'boolean') a = a ? 1 : 0;
  if (typeof b === 'boolean') b = b ? 1 : 0;
  if (a === b) return true;
  if (a === null || b === null) return false;
  if (Array.isArray(a) && Array.isArray(b)) {
    return a.length === b.length && a.every((x, i) => deepEq(x, b[i]));
  }
  if (isDict(a) && isDict(b)) {
    const ka = Object.keys(a);
    const kb = Object.keys(b);
    return ka.length === kb.length && ka.every((k) => k in b && deepEq(a[k], b[k]));
  }
  return false;
}

function cmp(a, b, op) {
  if (typeof a !== typeof b) {
    return {error: `'${op}' not supported between instances of different types`};
  }
  if (typeof a === 'number' || typeof a === 'string') {
    switch (op) {
      case '>':
        return {value: a > b};
      case '>=':
        return {value: a >= b};
      case '<':
        return {value: a < b};
      case '<=':
        return {value: a <= b};
      default:
        return {error: 'unknown operator'};
    }
  }
  return {error: `'${op}' not supported for this type`};
}

function comparison(op, passWord, failWord) {
  return (input, data) => {
    const r = cmp(input, data, op);
    if (r.error) return {passed: false, message: r.error};
    return {
      passed: r.value,
      message: r.value
        ? `${fmt(input)} is ${passWord} ${fmt(data)}`
        : `${fmt(input)} is ${failWord} ${fmt(data)}`,
    };
  };
}

/** The thirteen condition types, with the messages the Python emits. */
export const CONDITIONS = {
  Equals: (i, d) => ({
    passed: deepEq(i, d),
    message: deepEq(i, d)
      ? `${fmt(i)} is equal to ${fmt(d)}`
      : `${fmt(i)} is not equal to ${fmt(d)}`,
  }),
  NotEquals: (i, d) => ({
    passed: !deepEq(i, d),
    message: !deepEq(i, d)
      ? `${fmt(i)} is not equal to ${fmt(d)}`
      : `${fmt(i)} is equal to ${fmt(d)}`,
  }),
  GreaterThan: comparison('>', 'greater than', 'not greater than'),
  GreaterThanEqualTo: comparison(
    '>=',
    'greater than equal to',
    'not greater than or equal to',
  ),
  LessThan: comparison('<', 'less than', 'not less than'),
  LessThanEqualTo: comparison(
    '<=',
    'less than equal to',
    'not less than or equal to',
  ),
  IsEmpty: (i) => {
    const empty =
      i === null ||
      i === '' ||
      (isList(i) && i.length === 0) ||
      (isDict(i) && Object.keys(i).length === 0);
    return {
      passed: empty,
      message: empty ? `${fmt(i)} is empty` : `${fmt(i)} is not empty`,
    };
  },
  IsNotEmpty: (i) => {
    // Numbers, booleans and null are never "not empty" — evaluators.md is explicit.
    const notEmpty =
      (isStr(i) && i.length > 0) ||
      (isList(i) && i.length > 0) ||
      (isDict(i) && Object.keys(i).length > 0);
    return {
      passed: notEmpty,
      message: notEmpty ? `${fmt(i)} is not empty` : `${fmt(i)} is empty`,
    };
  },
  RegexMatch: (i, d) => {
    if (!isStr(i) && !isList(i) && !isDict(i)) {
      return {passed: false, message: `${fmt(i)} does not match regex pattern ${fmt(d)}`};
    }
    let re;
    try {
      re = new RegExp(d);
    } catch (e) {
      return {passed: false, message: String(e.message)};
    }
    const hay = isStr(i) ? i : JSON.stringify(i);
    const hit = re.test(hay);
    return {
      passed: hit,
      message: hit
        ? `${fmt(i)} matches regex pattern ${fmt(d)}`
        : `${fmt(i)} does not match regex pattern ${fmt(d)}`,
    };
  },
  ContainedIn: (i, d) => {
    const hit = contains(d, i);
    if (hit === null) {
      return {
        passed: false,
        message: `${fmt(d)} is an unsupported data type for evaluating against value in 'condition.value'`,
      };
    }
    return {
      passed: hit,
      message: hit
        ? `Found ${fmt(i)} inside ${fmt(d)}`
        : `Failed to find ${fmt(i)} inside ${fmt(d)}`,
    };
  },
  NotContainedIn: (i, d) => {
    const hit = contains(d, i);
    if (hit === null) {
      return {
        passed: false,
        message: `${fmt(d)} is an unsupported data type for evaluating against value in 'condition.value'`,
      };
    }
    return {
      passed: !hit,
      message: hit ? `Found ${fmt(i)} inside ${fmt(d)}` : `Did not find ${fmt(i)} inside ${fmt(d)}`,
    };
  },
  Contains: (i, d) => {
    const hit = contains(i, d);
    if (hit === null) {
      return {
        passed: false,
        message: `${fmt(i)} is an unsupported data type for evaluating against value in 'condition.value'`,
      };
    }
    return {
      passed: hit,
      message: hit ? `Found ${fmt(d)} inside ${fmt(i)}` : `Failed to find ${fmt(d)} inside ${fmt(i)}`,
    };
  },
  NotContains: (i, d) => {
    const hit = contains(i, d);
    if (hit === null) {
      return {
        passed: false,
        message: `${fmt(i)} is an unsupported data type for evaluating against value in 'condition.value'`,
      };
    }
    return {
      passed: !hit,
      message: hit ? `Found ${fmt(d)} inside ${fmt(i)}` : `Did not find ${fmt(d)} inside ${fmt(i)}`,
    };
  },
};

export const CONDITION_NAMES = Object.keys(CONDITIONS);

/**
 * stackguardian/json `get_value`.
 *
 * `*` as a path segment iterates every element of a list or every value of a
 * dict, producing one value per match. Without `*`, one value of whatever shape
 * lives at the path.
 */
export function getValues(doc, keyPath) {
  const parts = String(keyPath).split('.');
  let current = [doc];
  for (const part of parts) {
    const next = [];
    for (const node of current) {
      if (part === '*') {
        if (isList(node)) next.push(...node);
        else if (isDict(node)) next.push(...Object.values(node));
      } else if (isDict(node) && part in node) {
        next.push(node[part]);
      } else if (isList(node) && /^\d+$/.test(part) && node[Number(part)] !== undefined) {
        next.push(node[Number(part)]);
      }
    }
    current = next;
    if (current.length === 0) break;
  }
  return current;
}

/* ── providers ────────────────────────────────────────────────────────────────
 *
 * Three of the five that ship. Each returns the same shape the Python providers
 * return, a list of outputs, so the evaluator loop below does not know or care
 * which provider produced them:
 *
 *   {value, meta}                     a value to run the condition against
 *   {err, severity, meta}             the provider could not produce one
 *
 * `severity` is the number `error_tolerance` is compared against, and the
 * comparison is `severity > tolerance` fails, otherwise the check is skipped.
 * The severities are copied from the handlers, not invented: they are the
 * difference between "this resource type is not in your plan" and "this
 * attribute is missing from a resource that is", and a lesson that got them
 * wrong would teach the wrong error_tolerance.
 */

const NOT_FOUND = Symbol('not found');

/** pydash.get: a dot path with numeric list indices, or NOT_FOUND. */
function pget(data, path) {
  let node = data;
  for (const part of String(path).split('.')) {
    if (isDict(node) && part in node) node = node[part];
    else if (isList(node) && /^\d+$/.test(part) && node[Number(part)] !== undefined) node = node[Number(part)];
    else return NOT_FOUND;
  }
  return node;
}

/**
 * The `a.*.b` form of terraform_resource_attribute.
 *
 * Mirrors _get_exp_attribute in the handler, including the part that looks odd:
 * every segment is resolved against the *original* attribute dictionary rather
 * than against the previous segment's result. The list branch returns early, so
 * that only shows up on paths that do not match, and reproducing it is the point
 * of the playground.
 */
function expandAttribute(parts, data) {
  const out = [];
  for (let i = 0; i < parts.length; i += 1) {
    const expr = parts[i];
    const val = pget(data, expr);
    if (isList(val) && i < parts.length - 1) {
      for (const item of val) {
        const sub = expandAttribute(parts.slice(i + 1), item);
        if (sub.length) out.push(...sub);
        // A list item without the attribute is still evaluated, as None, so a
        // policy over a list cannot pass by the item simply being absent.
        else out.push(null);
      }
      return out;
    }
    if (i === parts.length - 1 && val !== NOT_FOUND) {
      out.push(val);
    } else if (expr.endsWith('.*')) {
      const base = pget(data, expr.slice(0, -2));
      if (base !== NOT_FOUND && isList(base)) out.push(...base);
    }
  }
  return out;
}

function jsonProvide(args, input) {
  if (args.operation_type !== 'get_value') {
    return [{err: `operation_type: ${args.operation_type} is not supported`, severity: 99}];
  }
  const values = getValues(input, args.key_path);
  if (values.length === 0) {
    return [{err: `key_path: \`${args.key_path}\` is not found`, severity: 2}];
  }
  return values.map((value) => ({value}));
}

function terraformProvide(args, input) {
  const changes = input && input.resource_changes;
  if (!isList(changes) || changes.length === 0) {
    return [{err: 'No Terraform resources changes are found', severity: 0}];
  }

  const type = args.terraform_resource_type;
  const exclude = args.exclude_resource_types || [];
  // `*` means every resource, and is the only case exclude_resource_types applies
  // to: naming a type explicitly and then excluding it is a contradiction the
  // handler does not entertain.
  const matches = (rc) => (type === '*' ? !exclude.includes(rc.type) : rc.type === type);

  if (args.operation_type === 'attribute') {
    const attribute = args.terraform_resource_attribute;
    const out = [];
    let resourceFound = false;
    let attributeFound = false;

    for (const rc of changes) {
      if (!matches(rc)) continue;
      resourceFound = true;
      const after = rc.change && rc.change.after;
      if (!after) {
        out.push({err: `No Terraform changes found for resource type: '${type}'`, severity: 0});
        continue;
      }
      let local = false;
      if (attribute in after) {
        attributeFound = true;
        local = true;
        out.push({value: after[attribute], meta: rc});
      } else if (attribute.includes('.') || attribute.includes('*')) {
        const vals = expandAttribute(attribute.split('.*.'), after);
        if (vals.length) {
          attributeFound = true;
          local = true;
          for (const v of vals) out.push({value: v, meta: rc});
        }
      }
      if (!local) out.push({err: `attribute: '${attribute}' is not found`, severity: 2});
    }

    if (out.length === 0) {
      if (!resourceFound) return [{err: `resource_type: '${type}' is not found`, severity: 1}];
      if (!attributeFound) return [{err: `attribute: '${attribute}' is not found`, severity: 2}];
    }
    return out;
  }

  if (args.operation_type === 'action') {
    const out = [];
    let found = false;
    for (const rc of changes) {
      if (!matches(rc)) continue;
      found = true;
      for (const action of (rc.change && rc.change.actions) || []) out.push({value: action, meta: rc});
    }
    if (!found) out.push({err: `resource_type: '${type}' is not found`, severity: 1});
    return out;
  }

  if (args.operation_type === 'count') {
    // No "not found" error here, deliberately: zero of a resource is a real answer
    // and often the one you are gating on.
    let count = 0;
    let meta = null;
    for (const rc of changes) {
      if (!matches(rc)) continue;
      meta = rc;
      count += 1;
    }
    return [{value: count, meta}];
  }

  return [{err: `operation_type: '${args.operation_type}' is not supported`, severity: 99}];
}

function kubernetesProvide(args, input) {
  if (args.operation_type !== 'attribute') {
    return [{err: `operation_type: ${args.operation_type} is not supported`, severity: 99}];
  }
  const kind = args.kubernetes_kind;
  const path = args.attribute_path || '';
  if (kind === undefined || kind === null) {
    return [{err: 'kubernetes_kind must be provided', severity: 99}];
  }
  if (path === '') return [{err: 'attribute_path must be provided', severity: 99}];

  // The CLI reads a multi-document YAML file and hands the provider a list. The
  // playground parses JSON, so the same manifests arrive as a JSON array.
  const resources = isList(input) ? input : [input];
  const out = [];
  let found = false;
  for (const resource of resources) {
    if (!isDict(resource) || resource.kind !== kind) continue;
    found = true;
    let values = getValues(resource, path);
    // place_none_if_not_found: a manifest missing the attribute is evaluated as
    // null rather than skipped, so it cannot pass by omission.
    if (values.length === 0) values = [null];
    out.push({value: path.includes('*') ? values : values[0], meta: resource});
  }
  if (!found) out.push({err: `kind: ${kind} is not found`, severity: 1});
  return out;
}

export const PROVIDERS = {
  'stackguardian/json': jsonProvide,
  'stackguardian/terraform_plan': terraformProvide,
  'stackguardian/kubernetes': kubernetesProvide,
};

export const PROVIDER_NAMES = Object.keys(PROVIDERS);

/* ── eval_expression ──────────────────────────────────────────────────────────
 * Supports `&&`, `||`, `!` and parentheses over evaluator ids, which is the
 * grammar documented in docs/tirith-reference/eval-expressions.md.
 *
 * Three-valued: a skipped evaluator is null, and null propagates unless the
 * other operand already decides the answer (false && null is false).
 */
function tokenize(expr) {
  const out = [];
  const re = /\s*(&&|\|\||!|\(|\)|[A-Za-z_][A-Za-z0-9_]*)/g;
  let m;
  let consumed = 0;
  while ((m = re.exec(expr)) !== null) {
    if (m.index !== consumed) break;
    out.push(m[1]);
    consumed = re.lastIndex;
  }
  if (consumed !== expr.length) {
    throw new Error(`could not parse eval_expression near "${expr.slice(consumed).trim()}"`);
  }
  return out;
}

export function evalExpression(expr, values) {
  const tokens = tokenize(expr);
  let pos = 0;
  const peek = () => tokens[pos];
  const eat = (t) => {
    if (tokens[pos] !== t) throw new Error(`expected "${t}" in eval_expression`);
    pos += 1;
  };

  function primary() {
    if (peek() === '!') {
      pos += 1;
      const v = primary();
      return v === null ? null : !v;
    }
    if (peek() === '(') {
      eat('(');
      const v = orExpr();
      eat(')');
      return v;
    }
    const id = tokens[pos];
    if (id === undefined) throw new Error('eval_expression ended unexpectedly');
    if (!(id in values)) throw new Error(`eval_expression names "${id}", which is not an evaluator id`);
    pos += 1;
    return values[id];
  }

  function andExpr() {
    let left = primary();
    while (peek() === '&&') {
      pos += 1;
      const right = primary();
      if (left === false || right === false) left = false;
      else if (left === null || right === null) left = null;
      else left = true;
    }
    return left;
  }

  function orExpr() {
    let left = andExpr();
    while (peek() === '||') {
      pos += 1;
      const right = andExpr();
      if (left === true || right === true) left = true;
      else if (left === null || right === null) left = null;
      else left = false;
    }
    return left;
  }

  const result = orExpr();
  if (pos !== tokens.length) throw new Error('trailing tokens in eval_expression');
  return result;
}

/**
 * Evaluate a policy against an input document.
 *
 * Returns `{document, errors}` where `document` has the shape of `tirith --json`
 * output, or `{document: null, errors: [...]}` when the policy or input could
 * not be read at all — which is exit 1 territory, not a verdict.
 */
export function evaluatePolicy(policyText, inputText) {
  let policy;
  let input;
  try {
    policy = JSON.parse(policyText);
  } catch (e) {
    return {document: null, fatal: `policy.json is not valid JSON — ${e.message}`};
  }
  try {
    input = JSON.parse(inputText);
  } catch (e) {
    return {document: null, fatal: `input.json is not valid JSON — ${e.message}`};
  }

  const meta = policy.meta || {};
  const provider = meta.required_provider || 'stackguardian/json';
  const provide = PROVIDERS[provider];
  if (!provide) {
    return {
      document: null,
      fatal:
        `this browser playground implements ${PROVIDER_NAMES.join(', ')}; ` +
        `"${provider}" runs in the installed package.`,
    };
  }

  const errors = [];
  const evaluators = Array.isArray(policy.evaluators) ? policy.evaluators : [];
  const passedById = {};

  const reported = evaluators.map((ev) => {
    const id = ev.id;
    const args = ev.provider_args || {};
    const cond = ev.condition || {};
    const tolerance = Number(cond.error_tolerance || 0);
    const fn = CONDITIONS[cond.type];

    if (!fn) {
      const message = `Unsupported condition type: ${cond.type}`;
      passedById[id] = false;
      return {id, passed: false, description: ev.description ?? null, result: [{passed: false, message, meta: null}]};
    }

    const outputs = provide(args, input);

    const result = outputs.map((o) => {
      if (o.err !== undefined) {
        // `severity > tolerance` fails, otherwise the check is skipped. Copied from
        // core.py rather than reasoned about: the boundary case, severity equal to
        // tolerance, is a skip, and getting it backwards would invert every lesson
        // that teaches error_tolerance.
        if (o.severity > tolerance) {
          errors.push(o.err);
          return {passed: false, message: o.err, meta: o.meta ?? null};
        }
        return {passed: null, message: o.err, meta: o.meta ?? null};
      }
      const r = fn(o.value, cond.value);
      return {passed: r.passed, message: r.message, meta: o.meta ?? null};
    });

    /*
     * Three-valued, and deliberately not a transcription of the engine.
     *
     * core.py sets its running verdict to None inside the skip branch without
     * checking whether an earlier result already failed, so an evaluator that
     * fails and *then* skips is reported as unevaluated. That is the defect the
     * roadmap's "a rule that could not run is never reported as success" item
     * exists to fix (src/data/roadmap.js). A teaching playground that reproduced
     * it would teach an ordering artefact as a rule, so this is the intended
     * semantics: any failure decides, and only an evaluator with nothing but
     * skips is skipped.
     */
    let passed;
    if (result.some((r) => r.passed === false)) passed = false;
    else if (result.some((r) => r.passed === true)) passed = true;
    else passed = null;

    passedById[id] = passed;
    return {id, passed, description: ev.description ?? null, result};
  });

  let finalResult = null;
  const expr = policy.eval_expression;
  if (!expr) {
    return {document: null, fatal: 'policy has no eval_expression'};
  }
  try {
    finalResult = evalExpression(expr, passedById);
  } catch (e) {
    return {document: null, fatal: e.message};
  }

  return {
    document: {
      meta,
      final_result: finalResult,
      evaluators: reported,
      errors,
      eval_expression: expr,
    },
  };
}

/** The exit code the CLI would return under --fail-on-error. */
export function exitCodeFor(document) {
  if (!document) return 1;
  if (document.final_result === true) return 0;
  if (document.final_result === false) return 3;
  return 1; // every check skipped — the policy evaluated nothing
}

/** The pretty printer, reproduced: src/tirith/prettyprinter.py. */
export function prettyPrint(document) {
  const lines = [];
  let passedN = 0;
  let failedN = 0;
  let skippedN = 0;

  for (const check of document.evaluators) {
    const state = check.passed === true ? 'PASSED' : check.passed === null ? 'SKIPPED' : 'FAILED';
    const kind = check.passed === true ? 'pass' : check.passed === null ? 'skip' : 'fail';
    if (check.passed === true) passedN += 1;
    else if (check.passed === null) skippedN += 1;
    else failedN += 1;

    lines.push({kind, text: `Check: ${check.id}`});
    lines.push({kind, text: `  ${state}`});
    check.result.forEach((r, i) => {
      const rState = r.passed === true ? 'PASSED' : check.passed === null ? 'SKIPPED' : 'FAILED';
      const rKind = r.passed === true ? 'pass' : check.passed === null ? 'skip' : 'fail';
      lines.push({kind: rKind, text: `    ${i + 1}. ${rState}: ${r.message}`});
    });
    lines.push({kind: 'blank', text: ''});
  }

  if (document.errors.length) {
    lines.push({kind: 'fail', text: 'Errors:'});
    document.errors.forEach((e) => lines.push({kind: 'fail', text: `- ${e}`}));
    lines.push({kind: 'blank', text: ''});
  }

  lines.push({kind: 'plain', text: `Passed: ${passedN} Failed: ${failedN} Skipped: ${skippedN}`});
  lines.push({kind: 'blank', text: ''});
  lines.push({kind: 'plain', text: 'Final expression used:'});
  lines.push({kind: 'dim', text: `-> ${document.eval_expression}`});
  return lines;
}
