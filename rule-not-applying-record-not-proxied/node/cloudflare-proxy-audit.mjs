/**
 * Find Cloudflare rules that can never fire because the record is not proxied.
 *
 * Rules only apply to proxied traffic. A grey-clouded record resolves straight to
 * the origin, so the rule is never consulted.
 */
const API = 'https://api.cloudflare.com/client/v4';
// Records that SHOULD be unproxied. Reporting them would train people to ignore output.
const NEVER_PROXY = new Set(['MX', 'TXT', 'NS', 'SRV', 'CAA', 'PTR']);

/**
 * Pure decision function. Only A, AAAA and CNAME can be proxied at all; mail and
 * metadata records are correctly grey.
 */
export function unproxiedHttpRecords(records) {
  return records.filter((r) => ['A', 'AAAA', 'CNAME'].includes(r.type)
    && !NEVER_PROXY.has(r.type) && !r.proxied);
}

export function deadRules(ruleTargets, unproxied) {
  const grey = new Set(unproxied.map((r) => r.name));
  return ruleTargets.filter((t) => grey.has(t));
}

async function main() {
  const zone = process.argv[process.argv.indexOf('--zone-id') + 1];
  const at = process.argv.indexOf('--rule-target');
  const targets = at === -1 ? [] : process.argv.slice(at + 1).filter((a) => !a.startsWith('--'));
  const token = (process.env.CF_API_TOKEN || "dummy-cf-api-token");
  if (!token) { console.error('set CF_API_TOKEN'); process.exit(2); }

  const res = await fetch(`${API}/zones/${zone}/dns_records?per_page=500`,
    { headers: { Authorization: `Bearer ${token}` } });
  const { result: records = [] } = await res.json();

  const grey = unproxiedHttpRecords(records);
  console.log(`${records.length} record(s); ${grey.length} HTTP record(s) not proxied`);
  for (const rec of grey) {
    console.warn(`DNS ONLY  ${rec.name.padEnd(40)} ${rec.type} -> ${rec.content}  (origin IP is public)`);
  }
  const dead = deadRules(targets, grey);
  for (const t of dead) {
    console.error(`RULE DEAD  a rule targeting ${t} can never fire -- that hostname bypasses Cloudflare`);
  }
  process.exit(dead.length ? 1 : 0);
}

if (import.meta.url === `file://${process.argv[1]}`) main();
