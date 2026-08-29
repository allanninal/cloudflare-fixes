/**
 * Detect the Cloudflare settings combination that causes a redirect loop.
 *
 * Flexible SSL plus an origin that forces HTTPS is the classic cause. Both ends are
 * behaving correctly, which is why it is hard to see from either one.
 */
const API = 'https://api.cloudflare.com/client/v4';

/**
 * Pure decision function over three settings.
 *
 * The loop needs a plaintext hop AND something redirecting it back. Either alone is
 * fine, which is why this checks the combination.
 */
export function diagnose(sslMode, alwaysHttps, originForcesHttps) {
  const problems = [];
  if (sslMode === 'off') problems.push('SSL is off entirely; visitors are unencrypted');
  if (sslMode === 'flexible') {
    problems.push(originForcesHttps
      ? 'Flexible SSL with an origin that forces HTTPS -- this is the redirect loop. Set Full (strict).'
      : 'Flexible SSL: the Cloudflare-to-origin hop is plaintext even though visitors see a padlock');
  }
  if (sslMode === 'full') {
    problems.push('Full (not strict) does not validate the origin certificate; '
      + 'use Full (strict) unless the origin is self-signed');
  }
  if (alwaysHttps && originForcesHttps && ['flexible', 'off'].includes(sslMode)) {
    problems.push('Always Use HTTPS and an origin redirect are stacked on a plaintext origin hop');
  }
  return problems;
}

async function main() {
  const zone = process.argv[process.argv.indexOf('--zone-id') + 1];
  const originForces = process.argv.includes('--origin-forces-https');
  const apply = process.argv.includes('--apply');
  const setMode = process.argv[process.argv.indexOf('--set-mode') + 1];
  const token = (process.env.CF_API_TOKEN || "dummy-cf-api-token");
  if (!token) { console.error('set CF_API_TOKEN'); process.exit(2); }
  const headers = { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' };

  const get = async (path) => (await (await fetch(`${API}${path}`, { headers })).json()).result ?? {};
  const sslMode = (await get(`/zones/${zone}/settings/ssl`)).value;
  const always = (await get(`/zones/${zone}/settings/always_use_https`)).value === 'on';
  console.log(`ssl mode=${sslMode}  always_use_https=${always}  origin_forces_https=${originForces}`);

  const problems = diagnose(sslMode, always, originForces);
  problems.forEach((p) => console.error(p));

  if (process.argv.includes('--set-mode')) {
    const value = setMode === 'strict' ? 'strict' : 'full';
    if (apply) {
      await fetch(`${API}/zones/${zone}/settings/ssl`,
        { method: 'PATCH', headers, body: JSON.stringify({ value }) });
      console.log(`ssl mode set to ${value} -- purge the cache, a 301 outlives the fix`);
    } else {
      console.log(`WOULD set ssl mode to ${value} -- pass --apply`);
    }
  }
  process.exit(problems.length ? 1 : 0);
}

if (import.meta.url === `file://${process.argv[1]}`) main();
