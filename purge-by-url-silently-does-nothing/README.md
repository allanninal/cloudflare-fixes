# a cache purge that reports success and clears nothing

You deployed, you purged the URL, the API returned success: true, and the old version is still being served. Purge by single file matches on the full cache key, not on the URL you typed. If the object was stored under a key that includes a header or a cookie, your purge request describes a different object &mdash; and clearing an object that does not exist is not an error, so the API says it worked.

**Full guide with diagrams:** https://www.allanninal.dev/cloudflare/purge-by-url-silently-does-nothing/

## Run it

```bash
export DRY_RUN="true"   # report only, write nothing
python python/cloudflare_purge_verify.py
node node/cloudflare-purge-verify.mjs
```

## Test it

```bash
pytest python/test_cloudflare_purge_verify.py
node --test node/cloudflare-purge-verify.test.mjs
```
