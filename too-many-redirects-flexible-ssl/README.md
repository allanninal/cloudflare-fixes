# ERR_TOO_MANY_REDIRECTS is almost always Flexible SSL

The site was fine yesterday. Now every request ends in ERR_TOO_MANY_REDIRECTS and the origin logs show the same request arriving over and over. Nothing changed on the server. What changed is that the origin started forcing HTTPS &mdash; a plugin, a new vhost, a security header &mdash; while Cloudflare is still set to Flexible, which means it talks to the origin over plain HTTP. The origin redirects to HTTPS, Cloudflare answers that redirect, and the two of them loop until the browser gives up.

**Full guide with diagrams:** https://www.allanninal.dev/cloudflare/too-many-redirects-flexible-ssl/

## Run it

```bash
export DRY_RUN="true"   # report only, write nothing
python python/cloudflare_ssl_mode_check.py
node node/cloudflare-ssl-mode-check.mjs
```

## Test it

```bash
pytest python/test_cloudflare_ssl_mode_check.py
node --test node/cloudflare-ssl-mode-check.test.mjs
```
