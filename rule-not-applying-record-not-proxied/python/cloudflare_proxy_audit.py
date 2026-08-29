"""Find Cloudflare rules that can never fire because the record is not proxied.

Rules only apply to proxied traffic. A grey-clouded record resolves straight to the
origin, so the rule is never consulted -- which looks identical to a rule that
matches and does nothing.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("cloudflare_proxy_audit")

API = "https://api.cloudflare.com/client/v4"
# Records that SHOULD be unproxied. Proxying these breaks them, so they are not
# findings -- reporting them would train people to ignore the output.
NEVER_PROXY = {"MX", "TXT", "NS", "SRV", "CAA", "PTR"}


def unproxied_http_records(records):
    """Pure decision function.

    Only A, AAAA and CNAME records can be proxied at all. Mail and metadata records
    are correctly grey and must not be reported.
    """
    return [r for r in records
            if r.get("type") in {"A", "AAAA", "CNAME"}
            and r.get("type") not in NEVER_PROXY
            and not r.get("proxied", False)]


def dead_rules(rule_targets, unproxied_names):
    """Which configured hostnames point at something Cloudflare never sees?"""
    grey = {r["name"] for r in unproxied_names}
    return [t for t in rule_targets if t in grey]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zone-id", required=True)
    ap.add_argument("--rule-target", nargs="*", default=[],
                    help="hostnames your rules apply to")
    args = ap.parse_args()

    token = os.environ.get("CF_API_TOKEN")
    if not token:
        log.error("set CF_API_TOKEN")
        return 2
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {token}"})

    r = s.get(f"{API}/zones/{args.zone_id}/dns_records",
              params={"per_page": 500}, timeout=30)
    r.raise_for_status()
    records = r.json().get("result", [])

    grey = unproxied_http_records(records)
    log.info("%d record(s); %d HTTP record(s) not proxied", len(records), len(grey))
    for rec in grey:
        log.warning("DNS ONLY  %-40s %s -> %s  (origin IP is public; rules will not run)",
                    rec["name"], rec["type"], rec.get("content"))

    dead = dead_rules(args.rule_target, grey)
    for t in dead:
        log.error("RULE DEAD  a rule targeting %s can never fire -- that hostname "
                  "bypasses Cloudflare entirely", t)
    return 1 if dead else 0


if __name__ == "__main__":
    sys.exit(main())
