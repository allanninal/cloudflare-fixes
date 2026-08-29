# a Cloudflare rule that never applies because the record is grey-clouded

The redirect rule is right. The cache rule is right. You have re-read them four times and the syntax is fine. They never fire because the hostname they apply to is set to DNS only &mdash; the grey cloud &mdash; so requests go straight to your origin and never pass through Cloudflare at all. There is nothing wrong with the rule. Cloudflare is simply not in the path.

**Full guide with diagrams:** https://www.allanninal.dev/cloudflare/rule-not-applying-record-not-proxied/

## Run it

```bash
export DRY_RUN="true"   # report only, write nothing
python python/cloudflare_proxy_audit.py
node node/cloudflare-proxy-audit.mjs
```

## Test it

```bash
pytest python/test_cloudflare_proxy_audit.py
node --test node/cloudflare-proxy-audit.test.mjs
```
