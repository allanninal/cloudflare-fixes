# only one Page Rule applies, and it is the one at the top

You have a broad rule near the top that caches everything, and a specific rule further down that adds a redirect. Both patterns match the URL, so you expect both actions. You get one. Only the highest-priority matching Page Rule takes effect on a request &mdash; every other match is discarded, with no log line, no warning, and no indication in the dashboard that a rule was skipped.

**Full guide with diagrams:** https://www.allanninal.dev/cloudflare/only-one-page-rule-applies/

## Run it

```bash
export DRY_RUN="true"   # report only, write nothing
python python/cloudflare_page_rule_shadow.py
node node/cloudflare-page-rule-shadow.mjs
```

## Test it

```bash
pytest python/test_cloudflare_page_rule_shadow.py
node --test node/cloudflare-page-rule-shadow.test.mjs
```
