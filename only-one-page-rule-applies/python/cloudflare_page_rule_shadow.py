"""Find Page Rules that match but never run.

Only the highest-priority matching rule takes effect. Every other match is
discarded silently, so a rule can be present, enabled, correct and dead.
"""
import argparse
import fnmatch
import logging
import os
import sys
from urllib.parse import urlsplit

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("cloudflare_page_rule_shadow")

API = "https://api.cloudflare.com/client/v4"


def normalise(pattern, url):
    """Strip the optional scheme from both sides before comparing.

    A pattern with no scheme matches http and https. Comparing raw strings would
    make such a pattern look narrower than it is -- the opposite of the truth.
    """
    if "://" not in pattern:
        url = urlsplit(url).netloc + urlsplit(url).path + (
            "?" + urlsplit(url).query if urlsplit(url).query else "")
    return pattern, url


def matches(pattern, url):
    pat, target = normalise(pattern, url)
    return fnmatch.fnmatch(target, pat)


def evaluate(rules, url):
    """Return (winner, shadowed) for one URL.

    rules: list of dicts with 'priority', 'pattern', 'enabled', 'actions'.
    Higher priority wins. Disabled rules never match at all.
    """
    active = sorted((r for r in rules if r.get("enabled", True)),
                    key=lambda r: -r["priority"])
    hits = [r for r in active if matches(r["pattern"], url)]
    if not hits:
        return None, []
    return hits[0], hits[1:]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zone-id", required=True)
    ap.add_argument("--url", nargs="+", required=True)
    args = ap.parse_args()

    token = os.environ.get("CF_API_TOKEN")
    if not token:
        log.error("set CF_API_TOKEN")
        return 2

    r = requests.get(f"{API}/zones/{args.zone_id}/pagerules",
                     headers={"Authorization": f"Bearer {token}"}, timeout=30)
    r.raise_for_status()
    raw = r.json().get("result", [])

    rules = [{
        "priority": item.get("priority", 0),
        "pattern": item["targets"][0]["constraint"]["value"],
        "enabled": item.get("status") == "active",
        "actions": [a.get("id") for a in item.get("actions", [])],
    } for item in raw]

    disabled = [x for x in rules if not x["enabled"]]
    for d in disabled:
        log.warning("DISABLED  %s -- still counts against your rule quota", d["pattern"])

    shadowed_any = False
    for url in args.url:
        winner, shadowed = evaluate(rules, url)
        if not winner:
            log.info("%s -- no Page Rule matches", url)
            continue
        log.info("%s -> %s  actions=%s", url, winner["pattern"], winner["actions"])
        for s in shadowed:
            shadowed_any = True
            log.error("  SHADOWED  %s (actions=%s) matches but never runs -- only the "
                      "highest-priority match applies", s["pattern"], s["actions"])
    return 1 if shadowed_any else 0


if __name__ == "__main__":
    sys.exit(main())
