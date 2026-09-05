from dikwp_valueark.defaults import load_defaults


def test_catalog_is_complete():
    data = load_defaults()
    asset_ids = {a["id"] for a in data["assets"]}
    assert len(asset_ids) == 11
    assert len(data["scenarios"]) == 9
    for scenario in data["scenarios"]:
        assert set(scenario["returns"]) == asset_ids
    for profile in data["profiles"].values():
        assert set(profile["template"]) == asset_ids
        assert abs(sum(profile["template"].values()) - 1.0) < 1e-9
    assert data["constitutional_invariants"]["automatic_trade_authority"] == 0
    assert data["constitutional_invariants"]["automatic_broker_connection"] == 0
    assert data["constitutional_invariants"]["leverage_allowed"] is False
    assert data["constitutional_invariants"]["specific_security_recommendation"] is False


def test_alert_presets_include_model_risk():
    data = load_defaults()
    for preset in data["alert_presets"].values():
        assert "correlation_custody_break" in preset
        assert sum(preset.values()) > 0
