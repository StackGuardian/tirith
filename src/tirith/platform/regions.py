"""
StackGuardian regions, and the one place URLs are resolved.

A region is a well-known (API, dashboard) pair, so asking a caller for both URLs is asking them to
keep two constants in sync for no reason. Getting it half right is the common failure: overriding
only the API leaves every run link in every PR comment pointing at the wrong environment, which
looks like a broken integration rather than a misconfiguration.

`region` is the same identifier the Raycast extension uses, so a user who has configured one
recognises the other.

Note the API base here excludes `/api/v1`, matching Raycast, sg-cli and the terraform provider.
`--api-url` and `$SG_BASE_URL` have always included it, and `normalize_api_url` accepts both -- a
value exported for sg-cli previously produced 404s from tirith.
"""

import collections

Region = collections.namedtuple("Region", "id name api_base app_base")

# Only production regions are listed. Internal environments are reachable through --api-url /
# $SG_BASE_URL, which is also what a self-hosted or vanity host (api.<customer>.stackguardian.io)
# needs, so they are supported rather than merely tolerated.
#
# The dashboard uses a third spelling for the same regions ('eu1-europe' / 'us1-east'). These ids are
# the CLI and action spelling; there are two regions, not four.
REGIONS = (
    Region("eu", "Europe", "https://api.app.stackguardian.io", "https://app.stackguardian.io"),
    Region("us", "United States", "https://api.us.stackguardian.io", "https://us.stackguardian.io"),
)

DEFAULT_REGION_ID = "eu"

REGION_IDS = tuple(region.id for region in REGIONS)

API_PATH = "/api/v1"


def by_id(region_id):
    """
    Look up a region, raising on an unknown id.

    Deliberately not the "fall back to the first region" behaviour the Raycast extension uses:
    here a typo would silently evaluate a US org's infrastructure against production EU, and the
    only symptom would be an authentication error the user cannot explain.
    """
    for region in REGIONS:
        if region.id == region_id:
            return region
    raise ValueError(f"Unknown region '{region_id}'. Valid regions: {', '.join(REGION_IDS)}")


def normalize_api_url(api_url):
    """
    Accept an API base with or without the `/api/v1` suffix.

    tirith's own flag has always included it; every other StackGuardian client omits it. Rejecting
    one spelling would be a papercut for anyone who has already exported SG_BASE_URL for sg-cli.
    """
    trimmed = (api_url or "").rstrip("/")
    if not trimmed:
        return trimmed
    if trimmed.endswith(API_PATH):
        return trimmed
    return f"{trimmed}{API_PATH}"


def by_api_url(api_url):
    """Find the region an API URL belongs to, tolerating the `/api/v1` suffix. None if unknown."""
    normalized = normalize_api_url(api_url)
    for region in REGIONS:
        if normalized == normalize_api_url(region.api_base):
            return region
    return None


def resolve(region_id=None, api_url=None, dashboard_url=None, env=None):
    """
    Resolve (api_url, dashboard_url, warnings) from a region, explicit URLs and the environment.

    Precedence, highest first:

      1. explicit --api-url / --dashboard-url
      2. --region
      3. $SG_BASE_URL / $SG_DASHBOARD_URL, then $SG_REGION
      4. the default region

    Explicit URLs beat a region because they are the only way to reach a self-hosted install, so
    they have to keep working permanently rather than as a deprecation shim. Passing both a region
    and an explicit URL is a caller error -- they contradict each other, and silently picking one
    would hide it.

    A URL environment variable beats $SG_REGION rather than erroring: environment is inherited
    config the caller may not control, and failing a CI run over it would be unhelpful.
    """
    env = {} if env is None else env
    warnings = []

    env_api_url = env.get("SG_BASE_URL")
    env_dashboard_url = env.get("SG_DASHBOARD_URL")
    env_region_id = env.get("SG_REGION")

    if region_id and (api_url or dashboard_url):
        which = " and ".join(
            name for name, value in (("--api-url", api_url), ("--dashboard-url", dashboard_url)) if value
        )
        raise ValueError(f"--region and {which} cannot be combined; they set the same thing")

    effective_region_id = region_id or env_region_id
    if effective_region_id and not region_id and (env_api_url or env_dashboard_url):
        warnings.append(
            f"both $SG_REGION and $SG_BASE_URL/$SG_DASHBOARD_URL are set; using the URLs and "
            f"ignoring region '{effective_region_id}'"
        )
        effective_region_id = None

    if effective_region_id:
        region = by_id(effective_region_id)
        return normalize_api_url(region.api_base), region.app_base, warnings

    resolved_api = api_url or env_api_url
    resolved_dashboard = dashboard_url or env_dashboard_url
    default_region = by_id(DEFAULT_REGION_ID)

    if not resolved_api and not resolved_dashboard:
        return normalize_api_url(default_region.api_base), default_region.app_base, warnings

    if not resolved_api:
        resolved_api = default_region.api_base

    if not resolved_dashboard:
        # The footgun this function exists for: setting only the API leaves every run link pointing
        # at the default environment. Infer the dashboard when the API is a region we know, and say
        # so out loud when it is not.
        matched = by_api_url(resolved_api)
        if matched:
            resolved_dashboard = matched.app_base
        else:
            resolved_dashboard = default_region.app_base
            warnings.append(
                f"no dashboard URL given and '{resolved_api}' is not a known region, so run links "
                f"will point at {resolved_dashboard}; pass --dashboard-url to fix them"
            )

    return normalize_api_url(resolved_api), resolved_dashboard.rstrip("/"), warnings
