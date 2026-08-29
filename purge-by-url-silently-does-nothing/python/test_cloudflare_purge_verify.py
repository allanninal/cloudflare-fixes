from cloudflare_purge_verify import interpret, purge_will_miss


def test_miss_means_the_purge_worked():
    ok, _ = interpret("MISS", None)
    assert ok


def test_expired_is_success_under_tiered_cache():
    """The lower tier is revalidating against the upper tier. Not a failure."""
    ok, _ = interpret("EXPIRED", "3")
    assert ok


def test_hit_with_a_large_age_is_a_failed_purge():
    ok, msg = interpret("HIT", "86400")
    assert not ok and "cache key" in msg


def test_dynamic_is_not_a_failure():
    ok, _ = interpret("DYNAMIC", None)
    assert ok


def test_a_custom_key_with_headers_blocks_single_file_purge():
    rule = {"cache_key": {"custom_key": {"header": {"include": ["Origin"]}}}}
    assert any("custom cache key" in r for r in purge_will_miss(rule))


def test_a_get_only_expression_is_flagged():
    rule = {"expression": 'http.request.method eq "GET"'}
    assert any("only GET" in r for r in purge_will_miss(rule))


def test_an_expression_that_allows_purge_is_not_flagged():
    rule = {"expression": '(http.request.method eq "GET" or http.request.method eq "PURGE")'}
    assert purge_will_miss(rule) == []


def test_a_plain_rule_is_clean():
    assert purge_will_miss({"expression": 'http.host eq "example.com"'}) == []
