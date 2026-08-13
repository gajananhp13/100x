import pytest

from app.core.integrations.platforms import INTEGRATIONS
from app.core.integrations.registry import PLATFORM_BY_ID, build_integration

ALL_PLATFORM_IDS = sorted(PLATFORM_BY_ID.keys())


def test_every_platform_has_an_integration_class():
    assert set(INTEGRATIONS.keys()) == set(PLATFORM_BY_ID.keys())


def test_platform_defs_match_integration_ids():
    for pid in ALL_PLATFORM_IDS:
        assert INTEGRATIONS[pid].platform_id == pid
        assert INTEGRATIONS[pid].platform_label == PLATFORM_BY_ID[pid].label
        assert INTEGRATIONS[pid].real_api == PLATFORM_BY_ID[pid].real_api


@pytest.mark.parametrize("pid", ALL_PLATFORM_IDS)
def test_every_platform_collects_simulated_data(pid):
    integration = build_integration(pid, force_mock=True)
    data = integration.collect("aaravmehta")
    assert data["_source"] == "mock"
    assert isinstance(data, dict) and len(data) > 2


def test_real_platforms_simulate_when_forced():
    github = build_integration("github", force_mock=True)
    assert github.collect("aaravmehta")["_source"] == "mock"
    leetcode = build_integration("leetcode", force_mock=True)
    assert leetcode.collect("aaravmehta")["_source"] == "mock"


def test_unknown_platform_raises():
    with pytest.raises(KeyError):
        build_integration("myspace")
