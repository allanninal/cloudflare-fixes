from cloudflare_ssl_mode_check import diagnose


def test_strict_with_a_redirecting_origin_is_fine():
    assert diagnose("strict", True, True) == []


def test_flexible_plus_origin_redirect_is_the_loop():
    problems = diagnose("flexible", False, True)
    assert any("redirect loop" in p for p in problems)


def test_flexible_alone_is_still_flagged_as_insecure():
    """It works, but the second hop is plaintext behind a padlock."""
    problems = diagnose("flexible", False, False)
    assert problems and not any("redirect loop" in p for p in problems)


def test_full_without_strict_is_flagged():
    assert any("does not validate" in p for p in diagnose("full", False, False))


def test_ssl_off_is_reported():
    assert any("SSL is off" in p for p in diagnose("off", False, False))
