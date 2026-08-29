"""Purge a URL and verify from CF-Cache-Status that it actually cleared.

The purge API is idempotent: clearing an object that is not there succeeds. So a
purge that names the wrong cache key is indistinguishable from one that worked,
unless you go and look.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("cloudflare_purge_verify")

API = "https://api.cloudflare.com/client/v4"
# Objects cached with any of these in the key are not cleared by a dashboard
# single-file purge. Documented list, not a guess.
KEY_HEADERS = {"origin", "x-forwarded-host", "x-host", "x-forwarded-scheme",
               "x-original-url", "x-rewrite-url", "forwarded"}


def purge_will_miss(cache_rule):
    """Pure decision function: can single-file purge clear objects under this rule?

    Two documented reasons it cannot: a custom cache key containing headers or
    cookies (the purge request cannot supply them), and an expression that matches
    only GET (purge uses a different method internally).
    """
    reasons = []
    key = cache_rule.get("cache_key", {}) or {}
    custom = key.get("custom_key", {}) or {}
    if custom.get("header") or custom.get("cookie"):
        reasons.append("custom cache key includes headers or cookies -- dashboard "
                       "single-file purge cannot supply them; use the API with "
                       "headers, or purge by prefix/tag")
    expr = cache_rule.get("expression", "")
    if 'http.request.method eq "GET"' in expr and "PURGE" not in expr:
        reasons.append('expression matches only GET -- purge uses a different method; '
                       'add or http.request.method eq "PURGE"')
    return reasons


def interpret(status, age):
    """What CF-Cache-Status means after a purge.

    EXPIRED is not a failure with tiered cache on: the lower tier is revalidating
    against the upper tier.
    """
    s = (status or "").upper()
    if s in ("MISS", "EXPIRED"):
        return True, f"{s} -- purge took effect"
    if s == "HIT":
        return (False, f"HIT with age={age} -- still serving a stored copy; the purge "
                       "did not match this object's cache key")
    if s in ("DYNAMIC", "BYPASS"):
        return True, f"{s} -- this URL is not cached at all"
    return True, f"{s or 'no CF-Cache-Status'} -- nothing to purge here"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zone-id", required=True)
    ap.add_argument("--url", required=True)
    ap.add_argument("--header", action="append", default=[],
                    help="Name:Value that is part of the cache key; repeatable")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    token = os.environ.get("CF_API_TOKEN")
    if not token:
        log.error("set CF_API_TOKEN")
        return 2
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {token}"})

    headers = {}
    for h in args.header:
        name, _, value = h.partition(":")
        headers[name.strip()] = value.strip()
        if name.strip().lower() in KEY_HEADERS:
            log.info("%s is a known cache-key header -- good that you passed it", name.strip())

    if not args.apply:
        log.info("WOULD purge %s with headers=%s -- pass --apply", args.url, headers or "{}")
        return 0

    body = {"files": [{"url": args.url, "headers": headers} if headers else args.url]}
    r = s.post(f"{API}/zones/{args.zone_id}/purge_cache", json=body, timeout=30)
    r.raise_for_status()
    log.info("purge API returned success=%s (this does NOT mean anything was removed)",
             r.json().get("success"))

    probe = requests.get(args.url, headers=headers, timeout=30)
    ok, msg = interpret(probe.headers.get("CF-Cache-Status"), probe.headers.get("Age"))
    (log.info if ok else log.error)(msg)
    if not ok:
        log.error("try purge by prefix, hostname or tag -- none of those are affected "
                  "by custom cache keys")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
