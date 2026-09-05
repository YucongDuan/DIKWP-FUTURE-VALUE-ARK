from dikwp_valueark.dashboard import dashboard_text


def test_dashboard_is_standalone_and_contains_controls():
    text = dashboard_text()
    assert "DIKWP FutureValue Ark OS" in text
    assert "id=\"runBtn\"" in text
    assert "automatic_trade_authority" in text
    assert "connect-src 'none'" in text
    assert "fetch(" not in text
    assert "XMLHttpRequest" not in text
    assert "WebSocket(" not in text
    assert "https://" not in text  # no external runtime resources or links


def test_dashboard_embeds_all_assets_and_scenarios():
    text = dashboard_text()
    for token in ["global_equity", "ai_tech", "correlation_custody_break", "agentic_cyber_liquidity"]:
        assert token in text
