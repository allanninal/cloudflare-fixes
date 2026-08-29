/**
 * Find Page Rules that match but never run.
 *
 * Only the highest-priority matching rule takes effect. Every other match is
 * discarded silently, so a rule can be present, enabled, correct and dead.
 */
const API = 'https://api.cloudflare.com/client/v4';

const toRegExp = (pattern) => new RegExp(
  `^${pattern.replace(/[.+^${}()|[\]\\]/g, '\\$&').replace(/\*/g, '.*')}$`);

/**
 * Strip the optional scheme from both sides before comparing. A pattern with no
 * scheme matches http and https, so a raw string compare makes it look narrower
 * than it is -- the opposite of the truth.
 */
export function matches(pattern, url) {
  const target = pattern.includes('://') ? url : url.replace(/^https?:\/\//, '');
  return toRegExp(pattern).test(target);
}

/** Return { winner, shadowed } for one URL. Disabled rules never match at all. */
export function evaluate(rules, url) {
  const active = rules.filter((r) => r.enabled !== false).sort((a, b) => b.priority - a.priority);
  const hits = active.filter((r) => matches(r.pattern, url));
  return { winner: hits[0] ?? null, shadowed: hits.slice(1) };
}

async function main() {
  const zone = process.argv[process.argv.indexOf('--zone-id') + 1];
  const ui = process.argv.indexOf('--url');
  const urls = process.argv.slice(ui + 1).filter((a) => !a.startsWith('--'));
  const token = (process.env.CF_API_TOKEN || "");
  if (!token) { console.error('set CF_API_TOKEN'); process.exit(2); }

  const res = await fetch(`${API}/zones/${zone}/pagerules`,
    { headers: { Authorization: `Bearer ${token}` } });
  const { result: raw = [] } = await res.json();

  const rules = raw.map((item) => ({
    priority: item.priority ?? 0,
    pattern: item.targets[0].constraint.value,
    enabled: item.status === 'active',
    actions: (item.actions ?? []).map((a) => a.id),
  }));

  for (const d of rules.filter((r) => !r.enabled)) {
    console.warn(`DISABLED  ${d.pattern} -- still counts against your rule quota`);
  }

  let shadowedAny = false;
  for (const url of urls) {
    const { winner, shadowed } = evaluate(rules, url);
    if (!winner) { console.log(`${url} -- no Page Rule matches`); continue; }
    console.log(`${url} -> ${winner.pattern}  actions=${winner.actions}`);
    for (const s of shadowed) {
      shadowedAny = true;
      console.error(`  SHADOWED  ${s.pattern} (actions=${s.actions}) matches but never runs`);
    }
  }
  process.exit(shadowedAny ? 1 : 0);
}

if (import.meta.url === `file://${process.argv[1]}`) main();
