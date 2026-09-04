"""
CLI
"""

import argparse
import json
import logging
import os
import sys
import textwrap

from tirith.logging import setup_logging
from tirith.prettyprinter import pretty_print_policy_set_result, pretty_print_result_dict
from tirith.status import ExitStatus
from tirith import __version__

from . import packs
from .core import start_policy_evaluation
from .core.core import start_policy_set_evaluation

logger = logging.getLogger(__name__)


def eprint(*args, **kwargs):
    """
    Just like print() but prints to sys.stderr instead of stdout.
    Use it when printing error messages.
    """
    print(*args, file=sys.stderr, **kwargs)


# Subcommands are dispatched before the flat parser sees anything. argparse cannot express an
# optional subcommand alongside options like `-policy-path` (a single dash and a long name), and the
# local-evaluation surface is a contract: tests/core/test_output_compatibility.py asserts its --json
# output is byte-identical to a golden file. An explicit pre-dispatch leaves that untouched.
#
# Named `platform` because that is what it evaluates against: the policies your StackGuardian
# organization enforces, run on the platform, rather than policy files in your repository.
#
# It was briefly `remote` on this branch, on the argument that "platform check" can read as *a check of
# the platform*. Reverted -- the vagueness is minor next to having one name, and the concern that
# prompted the rename was really that the open-source surface could not gate at all, which
# `--fail-on-error` fixed. No alias in either direction: nothing is released, so there is no caller to
# keep working.
SUBCOMMAND = "platform"


def collect_policy_paths(policy_path, pack_names):
    """
    Every policy to run, as (name, path) pairs, in the order they were asked for.

    `name` is what the result reports each policy as: the path relative to the directory that
    was given, or `<pack>/<file>` for a packed one. Relative, so a report does not depend on
    where the run happened.
    """
    collected = []
    for name in pack_names:
        pack = packs.resolve_pack(name)
        if pack is None:
            raise ValueError(f"unknown pack '{name}'. Run `tirith --list-packs` to see what is available.")
        collected += packs.pack_policy_paths(pack)

    if policy_path and os.path.isdir(policy_path):
        for dirpath, dirnames, filenames in os.walk(policy_path):
            # Prune in place so os.walk does not descend into hidden directories at all.
            dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
            for filename in sorted(filenames):
                if filename.endswith(".json") and not filename.startswith("."):
                    full = os.path.join(dirpath, filename)
                    collected.append((os.path.relpath(full, policy_path), full))
    elif policy_path:
        collected.append((os.path.basename(policy_path), policy_path))

    return collected


def print_pack_listing():
    installed = packs.list_packs()
    if not installed:
        print("No policy packs are bundled with this installation.")
        return
    width = max(len(pack.name) for pack in installed)
    for pack in installed:
        print(f"{pack.name:{width}}  {pack.count:>5} policies  {pack.description}")


# `ui` joins it on the same terms: dispatched before the flat parser, so the local-evaluation
# surface and its golden-file output are untouched. It is an optional extra -- it needs Python
# 3.9 and tirith supports 3.8 -- so tui/cli.py reports the missing extra rather than failing on
# an import here.
UI_SUBCOMMAND = "ui"
SUBCOMMANDS = {SUBCOMMAND, UI_SUBCOMMAND}


def main(args=None) -> ExitStatus:
    """
    The main function.

    Pre-process args, handle some special types of invocations,
    and run the main program with error handling.

    Return exit status code.
    """
    argv = list(sys.argv[1:] if args is None else args)

    if argv and argv[0] == UI_SUBCOMMAND:
        from tirith.tui import cli as tui_cli

        return tui_cli.main(argv)

    if argv and argv[0] in SUBCOMMANDS:
        from tirith.platform import cli as platform_cli

        return platform_cli.main(argv)

    try:

        class _WidthFormatter(argparse.RawTextHelpFormatter):
            def __init__(self, prog="PROG") -> None:
                super().__init__(prog, max_help_position=300)

        parser = argparse.ArgumentParser(
            description="Tirith (StackGuardian Policy Framework)",
            formatter_class=_WidthFormatter,
            epilog=textwrap.dedent(
                """\
         Subcommands:

            tirith platform check --help   Evaluate against the policies your StackGuardian
                                           organization enforces, rather than local files.
            tirith ui --help               Explore results, build policies and experiment in
                                           an interactive interface. Needs the 'tui' extra.

         About Tirith:
         
            * Abstract away the implementation complexity of policy engine underneath.
            * Simplify creation of declarative policies that are easy to read and interpret.
            * Provide a standard framework for scanning various configurations with granularity.
            * Provide modularity to enable easy extensibility
            * Github - https://github.com/StackGuardian/tirith
            * Docs - https://github.com/StackGuardian/tirith#readme
        """
            ),
        )
        parser.add_argument(
            "-policy-path",
            metavar="PATH",
            type=str,
            dest="policyPath",
            help="Path to a Tirith policy file, or a directory of them",
        )
        parser.add_argument(
            "--pack",
            metavar="NAME",
            type=str,
            default=[],
            action="append",
            dest="packs",
            help="Bundled policy pack(s) to run. Repeatable, and combines with -policy-path.",
        )
        parser.add_argument(
            "--list-packs",
            dest="listPacks",
            action="store_true",
            help="List the policy packs bundled with this installation and exit",
        )
        parser.add_argument(
            "-input-path",
            metavar="PATH",
            type=str,
            dest="inputPath",
            help="Input file path",
        )
        parser.add_argument(
            "-var-path",
            metavar="PATH",
            type=str,
            default=[],
            action="append",
            dest="varPaths",
            help="Variable file path(s)",
        )
        parser.add_argument(
            "-var",
            metavar="PATH",
            type=str,
            default=[],
            action="append",
            dest="inlineVars",
            help="Inline variable(s)",
        )
        parser.add_argument(
            "--json",
            dest="json",
            action="store_true",
            help="Only print the result in JSON form (useful for passing output to other programs)",
        )
        parser.add_argument(
            "--verbose",
            dest="verbose",
            action="store_true",
            help="Show detailed logs of from the run",
        )
        parser.add_argument(
            "--fail-on-error",
            dest="failOnError",
            action="store_true",
            help="Exit 3 when a policy fails, instead of 0. Off by default for compatibility.",
        )
        parser.add_argument("--version", action="version", version=__version__)

        args = parser.parse_args(argv)

        if not argv:
            parser.print_help()
            sys.exit(0)

        if args.listPacks:
            print_pack_listing()
            return ExitStatus.SUCCESS

        for pack_name in args.packs:
            if packs.resolve_pack(pack_name) is None:
                eprint(f"Unknown policy pack '{pack_name}'")
                eprint("Run `tirith --list-packs` to see the packs bundled with this installation.")
                return ExitStatus.ERROR

        if not args.policyPath and not args.packs:
            eprint("'-policy-path' argument is required")
            eprint("-policy-path argument is required. Provide a path to SG policy")
            return ExitStatus.ERROR
        if not args.inputPath:
            eprint("Path to input file should be provided to '--input-path' argument")
            eprint(
                "-input-path argument is required. Provide a path to JSON file compatible with the provider defined in the SG policy"
            )
            return ExitStatus.ERROR

        if args.json:
            # Disable all logging output
            logging.disable(logging.CRITICAL)
        else:
            setup_logging(verbose=args.verbose)

        # A single policy file keeps the result document, the printer and the exit codes it has
        # always had -- tests/core/test_output_compatibility.py pins those bytes. A directory or a
        # --pack is a *set*, and gets the aggregate document instead. The shape follows how the run
        # was asked for, not how many policies matched, so a directory holding one policy still
        # reports as a set.
        is_set = bool(args.packs) or (args.policyPath and os.path.isdir(args.policyPath))

        try:
            if is_set:
                policy_paths = collect_policy_paths(args.policyPath, args.packs)
                if not policy_paths:
                    eprint("No policies found to evaluate")
                    return ExitStatus.ERROR
                result = start_policy_set_evaluation(policy_paths, args.inputPath, args.varPaths, args.inlineVars)
            else:
                result = start_policy_evaluation(args.policyPath, args.inputPath, args.varPaths, args.inlineVars)

            if args.json:
                formatted_result = json.dumps(result, indent=3)
                print(formatted_result)
            elif is_set:
                pretty_print_policy_set_result(result, verbose=args.verbose)
            else:
                pretty_print_result_dict(result)

            # Without --fail-on-error this returns 0 whether the policy passed or failed, which is
            # what it has always done: the verdict is in the output, and changing that silently would
            # turn every existing green CI job red on upgrade.
            #
            # But a gate that cannot fail is not a gate, and this was the only way to run tirith
            # without an account -- so the honest answer was an opt-in flag rather than pointing
            # people at the hosted path when they need an exit code that means something.
            #
            # 3, not 1, and the distinction is the point: 3 says the infrastructure violates a policy,
            # 1 says tirith could not tell you. The same split `platform check` uses, because a caller
            # scripting both should not have to learn two vocabularies.
            #
            # `final_result` is tri-state, and that is what decides:
            #
            #   True    every check that ran passed              -> 0
            #   False   a check ran and said no                  -> 3
            #   None    nothing ran; every check was skipped     -> 1
            #   absent  the policy could not be loaded at all    -> 1
            #
            # None is not a pass. A policy whose every check was skipped -- `error_tolerance` swallowing
            # a provider that found nothing -- checked precisely nothing, and reporting that as green is
            # the failure this whole flag exists to prevent. `absent` is the missing-variables path,
            # which returns `errors` and no result at all.
            #
            # `errors` is deliberately NOT consulted. It reads like a tool-failure signal and is not: it
            # is populated only by the eval-expression pass, and the one thing that puts a message there
            # beside a real verdict is the informational "these ids are not defined and have been
            # removed" note. Gating on it inverted both halves of this contract -- a genuine violation
            # whose expression mentioned a typo'd id exited 1, while a policy naming an unknown provider
            # exited 3.
            #
            # Known limit, worth stating rather than pretending otherwise: a *misconfigured* policy -- an
            # unsupported `condition.type`, an unknown `required_provider` -- surfaces from the engine as
            # an ordinary failed evaluator with no error attached, so it is indistinguishable from a
            # violation here and exits 3. Fixing that means the engine reporting it distinctly, not this
            # branch guessing from free text.
            #
            # A set run reads the same tri-state off `final_result`, which the set runner has
            # already rolled up: any policy that said no makes the set False, and `None` means
            # nothing reached a verdict at all. The one thing that is deliberately *not* a
            # failure is a policy that skipped, because for a pack of any size that is the normal
            # case -- most checks do not apply to most plans -- and counting them would make every
            # pack run red regardless of the infrastructure.
            if args.failOnError:
                final_result = result.get("final_result")
                if "final_result" not in result or final_result is None:
                    return ExitStatus.ERROR
                if final_result is not True:
                    return ExitStatus.ERROR_POLICY_FAILED
            return ExitStatus.SUCCESS
        except Exception as e:
            # TODO:write an exception class for all provider exceptions.
            if args.json:
                # Print empty JSON
                print("{}")
            else:
                logger.exception(e)
                eprint("ERROR")
            return ExitStatus.ERROR

        # TODO: move to core
        # if not args.inputType:
        #     print("'--input-type' argument is required")
        #     return ExitStatus.ERROR

        # inputType = args.inputType

    except KeyboardInterrupt:
        eprint("\nFailed because of Keyboard Interrupt")
        return ExitStatus.ERROR_CTRL_C
    except SystemExit as e:
        if e.code != ExitStatus.SUCCESS:
            eprint("\nFailed because of System Exit")
            return ExitStatus.ERROR
    except Exception as e:
        # TODO: Further distinction between expected and unexpected errors.
        eprint(f"\n {type(e)}: {str(e)}")
        eprint("\nFailed because of an unhandled exception")
        return ExitStatus.ERROR
