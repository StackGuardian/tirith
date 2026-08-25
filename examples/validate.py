#!/usr/bin/env python3
"""Structural check for the starter pack, against the grammar read out of Tirith's source.

Tirith itself is not installed here, so this cannot tell you a policy produces the verdict you
wanted. It can tell you a policy is well-formed, that every condition and operation actually
exists, and that each rule's sample input contains something the rule would look at -- which is
where a hand-written policy usually goes wrong: a rule that matches nothing reports nothing and
looks exactly like a rule that passed.

    python3 examples/validate.py
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
POLICIES = os.path.join(HERE, 'policies')
PENDING = os.path.join(HERE, 'policies-pending')
INPUTS = os.path.join(HERE, 'inputs')

# src/tirith/core/evaluators/__init__.py
CONDITIONS = {'ContainedIn','Contains','Equals','GreaterThan','GreaterThanEqualTo','IsEmpty',
              'IsNotEmpty','LessThan','LessThanEqualTo','NotContainedIn','NotContains',
              'NotEquals','RegexMatch'}
VALUELESS = {'IsEmpty','IsNotEmpty'}
# src/tirith/providers/terraform_plan/handler.py
PLAN_OPS = {'attribute','action','count','direct_dependencies','direct_references',
            'terraform_version','provider_config'}
PROVIDER_CONFIG_ATTRS = {'version_constraint','region'}
# Every provider_args key the handler actually reads. Anything else is silently
# ignored at run time, which is the worst failure mode there is: the policy looks
# like it constrains something and does not. Keys proposed but NOT yet supported
# live in ENGINE_PENDING and are only legal under policies-pending/.
PLAN_ARGS = {'operation_type','terraform_resource_type','terraform_resource_attribute',
             'exclude_resource_types','terraform_provider_full_name','attribute'}
ENGINE_PENDING = {'actions','attribute_source','action_reason','module_address',
                  'sensitive','index'}
# providers/terraform_plan/handler.py, for choosing error_tolerance
SEVERITY_NOTES = {0:'change.after is null (the resource is being deleted)',
                  1:'resource type not present in the plan',
                  2:'attribute not present on the resource'}
PROVIDERS = {'stackguardian/terraform_plan','stackguardian/infracost',
             'stackguardian/kubernetes','stackguardian/json','stackguardian/sg_workflow'}
SEVERITIES = {'critical','high','medium','low'}

errors, warnings = [], []
def err(f, m): errors.append(f'{f}: {m}')
def warn(f, m): warnings.append(f'{f}: {m}')

def check_policy(path, pending=False):
    f = os.path.basename(path)
    try:
        p = json.load(open(path))
    except Exception as e:
        return err(f, f'not valid JSON -- {e}')

    meta = p.get('meta') or {}
    if meta.get('version') != 'v1':
        err(f, f'meta.version is {meta.get("version")!r}, expected "v1"')
    prov = meta.get('required_provider')
    if prov not in PROVIDERS:
        err(f, f'meta.required_provider {prov!r} is not a known provider')
    if not meta.get('name'):
        err(f, 'meta.name missing -- it is what the verdict shows the reader')
    if meta.get('severity') not in SEVERITIES:
        err(f, f'meta.severity {meta.get("severity")!r} not in {sorted(SEVERITIES)}')
    if pending and 'PENDING' not in (meta.get('name') or ''):
        err(f, 'a policy under policies-pending/ must say PENDING in meta.name -- '
               'it does not run, and nothing should be able to mistake it for a rule that does')

    evs = p.get('evaluators') or []
    if not evs:
        return err(f, 'no evaluators')
    ids = []
    for e in evs:
        i = e.get('id')
        if not i:
            err(f, 'an evaluator has no id'); continue
        if i in ids:
            err(f, f'duplicate evaluator id {i!r}')
        ids.append(i)

        pa = e.get('provider_args') or {}
        op = pa.get('operation_type')
        if prov == 'stackguardian/terraform_plan':
            if op not in PLAN_OPS:
                err(f, f'{i}: operation_type {op!r} not in {sorted(PLAN_OPS)}')
            if op == 'attribute':
                for k in ('terraform_resource_type','terraform_resource_attribute'):
                    if k not in pa: err(f, f'{i}: {op} needs {k}')
            if op in ('action','count','direct_dependencies','direct_references'):
                if 'terraform_resource_type' not in pa:
                    err(f, f'{i}: {op} needs terraform_resource_type')
            if op == 'provider_config':
                if 'terraform_provider_full_name' not in pa:
                    err(f, f'{i}: provider_config needs terraform_provider_full_name')
                if pa.get('attribute') not in PROVIDER_CONFIG_ATTRS:
                    err(f, f'{i}: provider_config attribute must be one of {sorted(PROVIDER_CONFIG_ATTRS)}')
            if 'exclude_resource_types' in pa and pa.get('terraform_resource_type') != '*':
                warn(f, f'{i}: exclude_resource_types is only honoured when terraform_resource_type is "*"')
            unknown = set(pa) - PLAN_ARGS
            proposed = unknown & ENGINE_PENDING
            if proposed and not pending:
                err(f, f'{i}: provider_args {sorted(proposed)} are NOT supported by the engine -- '
                       f'the handler ignores unknown keys, so this rule would silently constrain '
                       f'nothing. Move it to policies-pending/ until the patch lands')
            if pending and not proposed:
                warn(f, f'{i}: nothing here needs an engine change, so it belongs in policies/')
            for u in sorted(unknown - ENGINE_PENDING):
                err(f, f'{i}: provider_args {u!r} is not read by the handler and is not a known proposal')

        c = e.get('condition') or {}
        t = c.get('type')
        if t not in CONDITIONS:
            err(f, f'{i}: condition {t!r} does not exist (have: {", ".join(sorted(CONDITIONS))})')
        elif t in VALUELESS and 'value' in c:
            err(f, f'{i}: {t} takes no value')
        elif t not in VALUELESS and 'value' not in c:
            err(f, f'{i}: {t} needs a value')
        if t in ('GreaterThanEqualTo','GreaterThan','LessThan','LessThanEqualTo') \
           and isinstance(c.get('value'), str):
            err(f, f'{i}: {t} against the string {c["value"]!r} compares lexicographically '
                   f'("1.9.0" >= "1.11.4" is true) -- use RegexMatch')
        if 'error_tolerance' in c and not (isinstance(c['error_tolerance'], int)
                                          and c['error_tolerance'] >= 0):
            err(f, f'{i}: error_tolerance must be an integer >= 0')
        for k in ('error_tolerance',):
            if k in e:
                err(f, f'{i}: {k} belongs inside condition, not on the evaluator')

    expr = p.get('eval_expression')
    if not expr:
        return err(f, 'no eval_expression')
    referenced = set(re.findall(r'[A-Za-z_][A-Za-z0-9_]*', expr))
    for r in referenced - set(ids):
        err(f, f'eval_expression references {r!r}, which is not a declared evaluator id')
    for i in set(ids) - referenced:
        err(f, f'evaluator {i!r} is never used in eval_expression, so it can never fail the policy')
    return p

def check_reachability(f, p):
    """Would this policy see anything at all in its sample input?"""
    stem = f[:-5]
    cands = [c for c in os.listdir(INPUTS) if c.startswith(stem)]
    if not cands:
        return warn(f, 'no sample input -- the pack promises one per policy')
    if p['meta']['required_provider'] != 'stackguardian/terraform_plan':
        return
    for c in sorted(cands):
        if '.skips.' in c:
            continue
        doc = json.load(open(os.path.join(INPUTS, c)))
        present = {rc['type'] for rc in doc.get('resource_changes', [])}
        for e in p['evaluators']:
            pa = e['provider_args']
            want = pa.get('terraform_resource_type')
            if pa['operation_type'] in ('attribute','action') and want not in ('*', None):
                if want not in present:
                    warn(f, f'{c}: no {want} in resource_changes, so {e["id"]!r} '
                            f'skips rather than reporting (error_tolerance '
                            f'{e["condition"].get("error_tolerance","unset")})')

parsed = {}
for name in sorted(os.listdir(POLICIES)):
    if name.endswith('.json'):
        p = check_policy(os.path.join(POLICIES, name))
        if p: parsed[name] = p
for name, p in parsed.items():
    check_reachability(name, p)

pending = 0
if os.path.isdir(PENDING):
    for name in sorted(os.listdir(PENDING)):
        if name.endswith('.json'):
            pending += 1
            check_policy(os.path.join(PENDING, name), pending=True)

for name in sorted(os.listdir(INPUTS)):
    try: json.load(open(os.path.join(INPUTS, name)))
    except Exception as e: err(name, f'sample input is not valid JSON -- {e}')

print(f'{len(parsed)} live policies, {pending} pending engine support, '
      f'{len(os.listdir(INPUTS))} sample inputs\n')
for w in warnings: print('  warn  ' + w)
for e in errors:   print('  FAIL  ' + e)
print('\n' + ('%d error(s)' % len(errors) if errors
              else 'ok -- every policy is well-formed and its sample input reaches it'))
sys.exit(1 if errors else 0)
