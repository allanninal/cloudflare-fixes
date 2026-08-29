from cloudflare_page_rule_shadow import evaluate, matches


def rule(priority, pattern, enabled=True):
    return {"priority": priority, "pattern": pattern, "enabled": enabled, "actions": ["x"]}


def test_broad_rule_above_specific_shadows_it():
    rules = [rule(2, "example.com/*"), rule(1, "example.com/promo*")]
    winner, shadowed = evaluate(rules, "https://example.com/promo")
    assert winner["pattern"] == "example.com/*"
    assert [s["pattern"] for s in shadowed] == ["example.com/promo*"]


def test_specific_above_broad_is_the_fix():
    rules = [rule(2, "example.com/promo*"), rule(1, "example.com/*")]
    winner, _ = evaluate(rules, "https://example.com/promo")
    assert winner["pattern"] == "example.com/promo*"


def test_a_pattern_without_a_scheme_matches_https():
    """Omitting the scheme widens the match rather than narrowing it."""
    assert matches("example.com/*", "https://example.com/x")


def test_a_pattern_with_a_scheme_does_not_match_the_other_one():
    assert not matches("http://example.com/*", "https://example.com/x")


def test_a_disabled_rule_never_wins():
    rules = [rule(2, "example.com/*", enabled=False), rule(1, "example.com/promo*")]
    winner, shadowed = evaluate(rules, "https://example.com/promo")
    assert winner["pattern"] == "example.com/promo*"
    assert shadowed == []


def test_no_match_is_not_an_error():
    assert evaluate([rule(1, "other.com/*")], "https://example.com/") == (None, [])
