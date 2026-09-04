from enum import IntEnum, unique


@unique
class ExitStatus(IntEnum):
    """Program exit status code constants."""

    SUCCESS = 0
    ERROR = 1

    # 2 is deliberately absent. It used to be ERROR_TIMEOUT, but nothing ever returned it -- a
    # timeout is caught alongside URLError in the client and reported as ERROR. Meanwhile argparse
    # already exits 2 of its own accord on a usage error, so a caller seeing 2 has passed a bad
    # argument, not waited too long. Reclaiming it would make those two indistinguishable.

    # A policy said no, under `--fail-on-error`. Distinct from ERROR so a caller can
    # tell "your infrastructure violates a policy" from "tirith could not reach the platform" --
    # the same distinction --fail-on-error exists to draw, one level up.
    ERROR_POLICY_FAILED = 3

    # <http://www.tldp.org/LDP/abs/html/exitcodes.html>
    # 128+2 SIGINT
    ERROR_CTRL_C = 130
