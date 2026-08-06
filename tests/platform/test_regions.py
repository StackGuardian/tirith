"""
Tests for the region table and URL resolution.

The failure this replaces: `--api-url` and `--dashboard-url` were independent, so overriding only
the API left every run link in every PR comment pointing at the wrong environment -- which reads as
a broken integration rather than a misconfiguration.
"""

import pytest

from tirith.platform import regions

EU_API = "https://api.app.stackguardian.io/api/v1"
EU_APP = "https://app.stackguardian.io"
US_API = "https://api.us.stackguardian.io/api/v1"
US_APP = "https://us.stackguardian.io"


class TestTable:
    def test_two_production_regions(self):
        assert regions.REGION_IDS == ("eu", "us")

    def test_eu_is_the_default(self):
        assert regions.DEFAULT_REGION_ID == "eu"

    @pytest.mark.parametrize(
        "region_id, api_base, app_base",
        [
            ("eu", "https://api.app.stackguardian.io", EU_APP),
            ("us", "https://api.us.stackguardian.io", US_APP),
        ],
    )
    def test_region_pairs(self, region_id, api_base, app_base):
        region = regions.by_id(region_id)
        assert region.api_base == api_base
        assert region.app_base == app_base

    def test_api_bases_omit_the_api_path(self):
        """Matches Raycast, sg-cli and the terraform provider; normalize_api_url adds it back."""
        for region in regions.REGIONS:
            assert not region.api_base.endswith("/api/v1")

    def test_unknown_region_raises_and_names_the_valid_ones(self):
        """
        Deliberately not Raycast's "fall back to the first region": a typo would silently point a US
        org at production EU, and the only symptom would be an unexplainable auth error.
        """
        with pytest.raises(ValueError) as excinfo:
            regions.by_id("uss")
        assert "eu" in str(excinfo.value)
        assert "us" in str(excinfo.value)


class TestNormalizeApiUrl:
    @pytest.mark.parametrize(
        "given",
        [
            "https://api.app.stackguardian.io",
            "https://api.app.stackguardian.io/",
            "https://api.app.stackguardian.io/api/v1",
            "https://api.app.stackguardian.io/api/v1/",
        ],
    )
    def test_both_spellings_converge(self, given):
        """
        sg-cli's SG_BASE_URL omits /api/v1 and tirith's has always included it, so a value exported
        for one produced 404s from the other.
        """
        assert regions.normalize_api_url(given) == EU_API

    def test_an_empty_value_stays_empty(self):
        assert regions.normalize_api_url("") == ""
        assert regions.normalize_api_url(None) == ""

    def test_a_self_hosted_host_is_left_alone_apart_from_the_suffix(self):
        assert regions.normalize_api_url("https://api.siemens-ag.stackguardian.io") == (
            "https://api.siemens-ag.stackguardian.io/api/v1"
        )


class TestByApiUrl:
    @pytest.mark.parametrize("given", ["https://api.us.stackguardian.io", US_API])
    def test_matches_with_or_without_the_suffix(self, given):
        assert regions.by_api_url(given).id == "us"

    def test_returns_none_for_an_unknown_host(self):
        assert regions.by_api_url("https://api.siemens-ag.stackguardian.io") is None


class TestResolve:
    def test_defaults_to_eu(self):
        api, dashboard, warnings = regions.resolve()
        assert (api, dashboard) == (EU_API, EU_APP)
        assert warnings == []

    def test_region_sets_both_urls(self):
        api, dashboard, warnings = regions.resolve(region_id="us")
        assert (api, dashboard) == (US_API, US_APP)
        assert warnings == []

    def test_explicit_urls_win_over_the_default(self):
        api, dashboard, _w = regions.resolve(
            api_url="https://api.self-hosted.example", dashboard_url="https://self-hosted.example"
        )
        assert api == "https://api.self-hosted.example/api/v1"
        assert dashboard == "https://self-hosted.example"

    @pytest.mark.parametrize(
        "kwargs",
        [
            {"api_url": "https://api.self-hosted.example"},
            {"dashboard_url": "https://self-hosted.example"},
            {"api_url": "https://api.self-hosted.example", "dashboard_url": "https://self-hosted.example"},
        ],
    )
    def test_region_with_an_explicit_url_is_an_error(self, kwargs):
        """They set the same thing; silently picking one would hide the contradiction."""
        with pytest.raises(ValueError, match="cannot be combined"):
            regions.resolve(region_id="us", **kwargs)

    def test_an_api_url_for_a_known_region_infers_its_dashboard(self):
        """
        The footgun the whole module exists for: this used to leave run links on the EU dashboard
        for a US org.
        """
        api, dashboard, warnings = regions.resolve(api_url="https://api.us.stackguardian.io")
        assert api == US_API
        assert dashboard == US_APP
        assert warnings == []

    def test_an_unknown_api_url_without_a_dashboard_warns(self):
        api, dashboard, warnings = regions.resolve(api_url="https://api.self-hosted.example")
        assert api == "https://api.self-hosted.example/api/v1"
        assert dashboard == EU_APP
        assert len(warnings) == 1
        assert "--dashboard-url" in warnings[0]


class TestResolveFromEnvironment:
    def test_sg_region_is_honoured(self):
        api, dashboard, _w = regions.resolve(env={"SG_REGION": "us"})
        assert (api, dashboard) == (US_API, US_APP)

    def test_sg_base_url_without_the_suffix_is_normalized(self):
        api, _d, _w = regions.resolve(env={"SG_BASE_URL": "https://api.us.stackguardian.io"})
        assert api == US_API

    def test_sg_base_url_infers_the_dashboard_too(self):
        _api, dashboard, _w = regions.resolve(env={"SG_BASE_URL": "https://api.us.stackguardian.io"})
        assert dashboard == US_APP

    def test_an_explicit_flag_beats_the_environment(self):
        api, _d, _w = regions.resolve(api_url="https://api.us.stackguardian.io", env={"SG_BASE_URL": "https://x"})
        assert api == US_API

    def test_a_region_flag_beats_a_url_environment(self):
        api, dashboard, warnings = regions.resolve(region_id="us", env={"SG_BASE_URL": "https://x"})
        assert (api, dashboard) == (US_API, US_APP)
        assert warnings == []

    def test_a_url_environment_beats_sg_region_with_a_warning(self):
        """
        Not an error: the environment is inherited config the caller may not control, and failing a
        CI run over a contradiction they did not write would be unhelpful.
        """
        api, _d, warnings = regions.resolve(env={"SG_REGION": "eu", "SG_BASE_URL": "https://api.us.stackguardian.io"})
        assert api == US_API
        assert len(warnings) == 1
        assert "SG_REGION" in warnings[0]
