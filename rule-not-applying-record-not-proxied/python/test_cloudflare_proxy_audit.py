from cloudflare_proxy_audit import unproxied_http_records, dead_rules


def rec(name, rtype="A", proxied=True):
    return {"name": name, "type": rtype, "proxied": proxied, "content": "203.0.113.1"}


def test_a_proxied_record_is_not_reported():
    assert unproxied_http_records([rec("app.example.com")]) == []


def test_a_grey_clouded_a_record_is_reported():
    out = unproxied_http_records([rec("app.example.com", proxied=False)])
    assert len(out) == 1


def test_mx_records_are_never_reported():
    """MX must be grey. Reporting it is how a report becomes noise."""
    assert unproxied_http_records([rec("example.com", "MX", proxied=False)]) == []


def test_txt_records_are_never_reported():
    assert unproxied_http_records([rec("example.com", "TXT", proxied=False)]) == []


def test_a_rule_on_a_grey_hostname_is_dead():
    grey = unproxied_http_records([rec("app.example.com", proxied=False)])
    assert dead_rules(["app.example.com"], grey) == ["app.example.com"]


def test_a_rule_on_a_proxied_hostname_is_live():
    grey = unproxied_http_records([rec("app.example.com", proxied=True)])
    assert dead_rules(["app.example.com"], grey) == []
