# Cloudflare Fixes

Python and Node.js scripts that detect and repair Cloudflare configuration problems — shadowed page rules, purges that clear nothing and Flexible SSL loops.

Every fix is safe by default. The scripts start in a dry run mode that reports what they would do, so you can read the plan before anything writes.

By **[Allan Niñal](https://github.com/allanninal)** — AI Solutions Engineer. I build AI powered tools, data products, and AWS automation.
Full write ups with diagrams for each fix live at **[allanninal.dev/cloudflare](https://www.allanninal.dev/cloudflare/)**.

[![Follow on GitHub](https://img.shields.io/github/followers/allanninal?label=Follow%20%40allanninal&style=social)](https://github.com/allanninal)

## The fixes

- [only one Page Rule applies, and it is the one at the top](./only-one-page-rule-applies/) — https://www.allanninal.dev/cloudflare/only-one-page-rule-applies/
- [a cache purge that reports success and clears nothing](./purge-by-url-silently-does-nothing/) — https://www.allanninal.dev/cloudflare/purge-by-url-silently-does-nothing/
- [a Cloudflare rule that never applies because the record is grey-clouded](./rule-not-applying-record-not-proxied/) — https://www.allanninal.dev/cloudflare/rule-not-applying-record-not-proxied/
- [ERR_TOO_MANY_REDIRECTS is almost always Flexible SSL](./too-many-redirects-flexible-ssl/) — https://www.allanninal.dev/cloudflare/too-many-redirects-flexible-ssl/

## How to run one

Each folder holds the same script in Python and in Node.js, plus its test. Set the environment variables named in that folder's README, keep `DRY_RUN=true` for the first pass, and read what it reports before letting it write.

## Tests

Every fix ships with its test. Run them locally:

```bash
pip install pytest requests
pytest -q
node --test
```

## License

MIT. Use it, change it, ship it.
