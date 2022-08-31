#!/usr/bin/env python
"""
Entrypoint module when invoked like `python -m sg_policy`.
"""
import sys


def main():
    try:
        from .cli import main

        exit_status = main()
    except KeyboardInterrupt:
        from sg_policy.status import ExitStatus

        exit_status = ExitStatus.ERROR_CTRL_C

    if exit_status is not None and exit_status.value:
        sys.exit(exit_status.value)


if __name__ == "__main__":
    main()
