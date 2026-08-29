import { test } from 'node:test';
import assert from 'node:assert/strict';
import { evaluate, matches } from './cloudflare-page-rule-shadow.mjs';

const rule = (priority, pattern, enabled = true) => ({ priority, pattern, enabled, actions: ['x'] });

test('a broad rule above a specific one shadows it', () => {
  const { winner, shadowed } = evaluate(
    [rule(2, 'example.com/*'), rule(1, 'example.com/promo*')], 'https://example.com/promo');
  assert.equal(winner.pattern, 'example.com/*');
  assert.deepEqual(shadowed.map((s) => s.pattern), ['example.com/promo*']);
});

test('specific above broad is the fix', () => {
  const { winner } = evaluate(
    [rule(2, 'example.com/promo*'), rule(1, 'example.com/*')], 'https://example.com/promo');
  assert.equal(winner.pattern, 'example.com/promo*');
});

test('a pattern without a scheme matches https', () => {
  assert.ok(matches('example.com/*', 'https://example.com/x'));
});

test('a disabled rule never wins', () => {
  const { winner } = evaluate(
    [rule(2, 'example.com/*', false), rule(1, 'example.com/promo*')], 'https://example.com/promo');
  assert.equal(winner.pattern, 'example.com/promo*');
});
