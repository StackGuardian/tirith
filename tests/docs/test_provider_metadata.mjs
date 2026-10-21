import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import test from 'node:test';

const source = await readFile(new URL('../../documentation/src/data/tirithLite.js', import.meta.url), 'utf8');
const {evaluatePolicy} = await import(`data:text/javascript;base64,${Buffer.from(source).toString('base64')}`);
const example = new URL('../../src/tirith/tui/examples/01-required-tags/', import.meta.url);
const policy = JSON.parse(await readFile(new URL('policy.json', example), 'utf8'));
const input = await readFile(new URL('input.json', example), 'utf8');
const provider = policy.meta.provider;

function evaluate(meta) {
  return evaluatePolicy(JSON.stringify({...policy, meta}), input);
}

test('the browser reads Terraform resources with meta.provider', () => {
  const result = evaluate(policy.meta);
  assert.equal(result.fatal, undefined);
  assert.equal(result.document.meta.required_provider, provider);
  assert.equal(Object.hasOwn(result.document.meta, 'provider'), false);
  assert.equal(result.document.evaluators[0].result[0].meta.address, 'aws_instance.web');
  assert.equal(result.document.evaluators[0].result[0].passed, true);
});

test('legacy and canonical spellings produce identical browser results', () => {
  const {provider: ignored, ...meta} = policy.meta;
  assert.deepEqual(evaluate({...meta, required_provider: provider}), evaluate(policy.meta));
});

test('meta.provider wins over a conflicting legacy provider', () => {
  assert.deepEqual(
    evaluate({...policy.meta, required_provider: 'stackguardian/json'}),
    evaluate(policy.meta),
  );
});

test('an invalid canonical provider cannot fall back to the legacy provider', () => {
  const result = evaluate({...policy.meta, provider: 'stackguardian/unknown', required_provider: provider});
  assert.equal(result.document, null);
  assert.match(result.fatal, /stackguardian\/unknown/);
});
