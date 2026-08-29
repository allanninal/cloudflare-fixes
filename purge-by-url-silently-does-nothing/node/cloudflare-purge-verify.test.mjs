import { test } from 'node:test';
import assert from 'node:assert/strict';
import { interpret, purgeWillMiss } from './cloudflare-purge-verify.mjs';

test('MISS means the purge worked', () => {
  assert.equal(interpret('MISS', null)[0], true);
});

test('EXPIRED is success under tiered cache', () => {
  assert.equal(interpret('EXPIRED', '3')[0], true);
});

test('HIT with a large age is a failed purge', () => {
  const [ok, msg] = interpret('HIT', '86400');
  assert.equal(ok, false);
  assert.ok(msg.includes('cache key'));
});

test('a custom key with headers blocks single-file purge', () => {
  const rule = { cache_key: { custom_key: { header: { include: ['Origin'] } } } };
  assert.ok(purgeWillMiss(rule).some((r) => r.includes('custom cache key')));
});

test('an expression that allows PURGE is not flagged', () => {
  const rule = { expression: '(http.request.method eq "GET" or http.request.method eq "PURGE")' };
  assert.deepEqual(purgeWillMiss(rule), []);
});
