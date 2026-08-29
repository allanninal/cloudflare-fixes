import { test } from 'node:test';
import assert from 'node:assert/strict';
import { unproxiedHttpRecords, deadRules } from './cloudflare-proxy-audit.mjs';

const rec = (name, type = 'A', proxied = true) => ({ name, type, proxied, content: '203.0.113.1' });

test('a proxied record is not reported', () => {
  assert.deepEqual(unproxiedHttpRecords([rec('app.example.com')]), []);
});

test('a grey-clouded A record is reported', () => {
  assert.equal(unproxiedHttpRecords([rec('app.example.com', 'A', false)]).length, 1);
});

test('MX records are never reported', () => {
  assert.deepEqual(unproxiedHttpRecords([rec('example.com', 'MX', false)]), []);
});

test('a rule on a grey hostname is dead', () => {
  const grey = unproxiedHttpRecords([rec('app.example.com', 'A', false)]);
  assert.deepEqual(deadRules(['app.example.com'], grey), ['app.example.com']);
});
