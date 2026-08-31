/**
 * tirith-lite — a teaching reimplementation of Tirith's evaluation core.
 *
 * ─────────────────────────────────────────────────────────────────────────────
 * WHAT THIS IS, PRECISELY
 *
 * This is NOT Tirith. Tirith is a Python package; this is a few hundred lines of
 * JavaScript that reproduces one provider and thirteen conditions closely enough
 * to teach the shape of a policy in a browser, with no install.
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
 * KNOWN DIVERGENCES — say these out loud in the UI, never paper over them:
 *   - Only `stackguardian/json` is implemented. terraform_plan, kubernetes,
 *     infracost and sg_workflow are not.
 *   - `Equals` does not sort nested collections the way the Python does.
 *   - Regexes are JavaScript regexes, not Python's `re`.
 *   - Error severities are approximated: a missing key_path is severity 2, which
 *     is the one case the error_tolerance lesson needs.
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
  const provider = meta.required_provider;
  if (provider && provider !== 'stackguardian/json') {
    return {
      document: null,
      fatal:
        `this browser playground only implements stackguardian/json; ` +
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
    if (args.operation_type !== 'get_value') {
      const message = `Unsupported operation type: ${args.operation_type}`;
      passedById[id] = false;
      return {id, passed: false, description: ev.description ?? null, result: [{passed: false, message, meta: null}]};
    }

    const values = getValues(input, args.key_path);

    if (values.length === 0) {
      // Severity 2 in the real provider: skipped at error_tolerance >= 2.
      const message = `key_path: \`${args.key_path}\` is not found`;
      if (tolerance >= 2) {
        passedById[id] = null;
        return {id, passed: null, description: ev.description ?? null, result: [{passed: null, message, meta: null}]};
      }
      errors.push(message);
      passedById[id] = false;
      return {id, passed: false, description: ev.description ?? null, result: [{passed: false, message, meta: null}]};
    }

    const result = values.map((v) => {
      const r = fn(v, cond.value);
      return {passed: r.passed, message: r.message, meta: null};
    });
    const passed = result.every((r) => r.passed);
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
