/**
 * Purge a URL and verify from CF-Cache-Status that it actually cleared.
 *
 * The purge API is idempotent: clearing an object that is not there succeeds. So a
 * purge that names the wrong cache key looks exactly like one that worked.
 */
const API = 'https://api.cloudflare.com/client/v4';
// Objects cached with any of these in the key are not cleared by a dashboard
// single-file purge. Documented list, not a guess.
const KEY_HEADERS = new Set(['origin', 'x-forwarded-host', 'x-host',
  'x-forwarded-scheme', 'x-original-url', 'x-rewrite-url', 'forwarded']);

/**
 * Pure decision function: can single-file purge clear objects under this rule?
 * Two documented reasons it cannot -- a custom cache key containing headers or
 * cookies, and an expression matching only GET.
 */
export function purgeWillMiss(cacheRule) {
  const reasons = [];
  const custom = cacheRule.cache_key?.custom_key ?? {};
  if (custom.header || custom.cookie) {
    reasons.push('custom cache key includes headers or cookies -- dashboard single-file '
      + 'purge cannot supply them; use the API with headers, or purge by prefix/tag');
  }
  const expr = cacheRule.expression ?? '';
  if (expr.includes('http.request.method eq "GET"') && !expr.includes('PURGE')) {
    reasons.push('expression matches only GET -- purge uses a different method; '
      + 'add or http.request.method eq "PURGE"');
  }
  return reasons;
}

/** What CF-Cache-Status means after a purge. EXPIRED is fine with tiered cache. */
export function interpret(status, age) {
  const s = (status ?? '').toUpperCase();
  if (s === 'MISS' || s === 'EXPIRED') return [true, `${s} -- purge took effect`];
  if (s === 'HIT') {
    return [false, `HIT with age=${age} -- still serving a stored copy; the purge did `
      + "not match this object's cache key"];
  }
  if (s === 'DYNAMIC' || s === 'BYPASS') return [true, `${s} -- this URL is not cached at all`];
  return [true, `${s || 'no CF-Cache-Status'} -- nothing to purge here`];
}

async function main() {
  const arg = (n) => process.argv[process.argv.indexOf(n) + 1];
  const zone = arg('--zone-id');
  const url = arg('--url');
  const apply = process.argv.includes('--apply');
  const headers = {};
  process.argv.forEach((a, i) => {
    if (a !== '--header') return;
    const [name, ...rest] = process.argv[i + 1].split(':');
    headers[name.trim()] = rest.join(':').trim();
    if (KEY_HEADERS.has(name.trim().toLowerCase())) {
      console.log(`${name.trim()} is a known cache-key header -- good that you passed it`);
    }
  });
  const token = (process.env.CF_API_TOKEN || "dummy-cf-api-token");
  if (!token) { console.error('set CF_API_TOKEN'); process.exit(2); }

  if (!apply) {
    console.log(`WOULD purge ${url} with headers=${JSON.stringify(headers)} -- pass --apply`);
    process.exit(0);
  }

  const files = [Object.keys(headers).length ? { url, headers } : url];
  const res = await fetch(`${API}/zones/${zone}/purge_cache`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ files }),
  });
  const { success } = await res.json();
  console.log(`purge API returned success=${success} (this does NOT mean anything was removed)`);

  const probe = await fetch(url, { headers });
  const [ok, msg] = interpret(probe.headers.get('cf-cache-status'), probe.headers.get('age'));
  (ok ? console.log : console.error)(msg);
  if (!ok) {
    console.error('try purge by prefix, hostname or tag -- none are affected by custom cache keys');
  }
  process.exit(ok ? 0 : 1);
}

if (import.meta.url === `file://${process.argv[1]}`) main();
