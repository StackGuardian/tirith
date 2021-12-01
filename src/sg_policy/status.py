from enum import IntEnum, unique


@unique
class ExitStatus(IntEnum):
    """Program exit status code constants."""

    SUCCESS = 0
    ERROR = 1
    ERROR_TIMEOUT = 2

    # <http://www.tldp.org/LDP/abs/html/exitcodes.html>
    # 128+2 SIGINT
    ERROR_CTRL_C = 130
