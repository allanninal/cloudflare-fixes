"""Detect the Cloudflare settings combination that causes a redirect loop.

Flexible SSL plus an origin that forces HTTPS is the classic cause: Cloudflare
requests over HTTP, the origin redirects to HTTPS, Cloudflare follows it back. Both
ends are behaving correctly, which is why it is hard to see from either one.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("cloudflare_ssl_mode_check")

API = "https://api.cloudflare.com/client/v4"


def diagnose(ssl_mode, always_https, origin_forces_https):
    """Pure decision function over three settings.

    The loop needs a plaintext hop AND something redirecting it back. Either alone
    is fine, which is why this checks the combination rather than the SSL mode on
    its own.
    """
    problems = []
    if ssl_mode == "off":
        problems.append("SSL is off entirely; visitors are unencrypted")
    if ssl_mode == "flexible":
        if origin_forces_https:
            problems.append("Flexible SSL with an origin that forces HTTPS -- this is "
                            "the redirect loop. Set Full (strict).")
        else:
            problems.append("Flexible SSL: the Cloudflare-to-origin hop is plaintext "
                            "even though visitors see a padlock")
    if ssl_mode == "full":
        problems.append("Full (not strict) does not validate the origin certificate; "
                        "use Full (strict) unless the origin is self-signed")
    if always_https and origin_forces_https and ssl_mode in ("flexible", "off"):
        problems.append("Always Use HTTPS and an origin redirect are stacked on a "
                        "plaintext origin hop")
    return problems


def get(session, url):
    r = session.get(url, timeout=30)
    r.raise_for_status()
    return r.json().get("result", {})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zone-id", required=True)
    ap.add_argument("--origin-forces-https", action="store_true",
                    help="set if the origin redirects http to https")
    ap.add_argument("--set-mode", choices=["full", "strict"],
                    help="'strict' maps to Cloudflare's full(strict)")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    token = os.environ.get("CF_API_TOKEN")
    if not token:
        log.error("set CF_API_TOKEN")
        return 2
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {token}"})

    ssl_mode = get(s, f"{API}/zones/{args.zone_id}/settings/ssl").get("value")
    always = get(s, f"{API}/zones/{args.zone_id}/settings/always_use_https").get("value") == "on"
    log.info("ssl mode=%s  always_use_https=%s  origin_forces_https=%s",
             ssl_mode, always, args.origin_forces_https)

    problems = diagnose(ssl_mode, always, args.origin_forces_https)
    for p in problems:
        log.error(p)

    if args.set_mode:
        value = "strict" if args.set_mode == "strict" else "full"
        if args.apply:
            s.patch(f"{API}/zones/{args.zone_id}/settings/ssl",
                    json={"value": value}, timeout=30).raise_for_status()
            log.info("ssl mode set to %s -- purge the cache, a 301 outlives the fix", value)
        else:
            log.info("WOULD set ssl mode to %s -- pass --apply", value)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
