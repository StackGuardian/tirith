from enum import IntEnum, unique


@unique
class ExitStatus(IntEnum):
    """Program exit status code constants."""

    SUCCESS = 0
    ERROR = 1
    ERROR_TIMEOUT = 2

    # A policy said no, under `--fail-on-error`. Distinct from ERROR so a caller can
    # tell "your infrastructure violates a policy" from "tirith could not reach the platform" --
    # the same distinction --fail-on-error exists to draw, one level up.
    ERROR_POLICY_FAILED = 3

    # <http://www.tldp.org/LDP/abs/html/exitcodes.html>
    # 128+2 SIGINT
    ERROR_CTRL_C = 130
