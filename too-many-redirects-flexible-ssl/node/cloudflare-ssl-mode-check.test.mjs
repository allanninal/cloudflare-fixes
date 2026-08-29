import { test } from 'node:test';
import assert from 'node:assert/strict';
import { diagnose } from './cloudflare-ssl-mode-check.mjs';

test('strict with a redirecting origin is fine', () => {
  assert.deepEqual(diagnose('strict', true, true), []);
});

test('flexible plus an origin redirect is the loop', () => {
  assert.ok(diagnose('flexible', false, true).some((p) => p.includes('redirect loop')));
});

test('flexible alone is still flagged as insecure', () => {
  const p = diagnose('flexible', false, false);
  assert.ok(p.length && !p.some((x) => x.includes('redirect loop')));
});

test('full without strict is flagged', () => {
  assert.ok(diagnose('full', false, false).some((p) => p.includes('does not validate')));
});
