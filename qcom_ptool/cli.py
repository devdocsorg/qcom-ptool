# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause

import argparse
import runpy
import sys

from qcom_ptool import __version__

SUBCOMMANDS = {
    "gen_partition": "qcom_ptool.gen_partition",
    "gen_contents": "qcom_ptool.gen_contents",
    "gen_udev_rules": "qcom_ptool.gen_udev_rules",
    "ptool": "qcom_ptool.ptool",
    "msp": "qcom_ptool.msp",
    "show": "qcom_ptool.show",
}


def _build_parser() -> argparse.ArgumentParser:
    """Build the parser for the top-level ``qcom-ptool`` command.

    Returns:
        argparse.ArgumentParser: A parser accepting ``-V``/``--version`` and one subcommand name.

    Example:
        ``_build_parser().parse_known_args(["ptool", "-x", "partitions.xml"])`` returns the
        ``ptool`` subcommand and ``["-x", "partitions.xml"]``.
    """
    parser = argparse.ArgumentParser(
        prog="qcom-ptool",
        description=(
            "Qualcomm partition tool - GPT partition table generator and "
            "mass storage programmer."
        ),
        epilog=(
            "Run 'qcom-ptool <subcommand> -h' to see the options accepted by "
            "each subcommand."
        ),
    )
    parser.add_argument(
        "-V", "--version", action="version", version=f"%(prog)s {__version__}"
    )
    parser.add_argument(
        "subcommand",
        choices=sorted(SUBCOMMANDS),
        metavar="subcommand",
        help="one of: " + ", ".join(sorted(SUBCOMMANDS)),
    )
    return parser


def main() -> None:
    """Run the ``qcom-ptool`` command: dispatch to the selected subcommand module.

    The remaining arguments are passed to the subcommand as its ``sys.argv``, and
    the module runs as ``__main__``, so its exit status is the command's.

    Raises:
        SystemExit: The subcommand name is invalid, ``-h`` or ``-V`` is given, or
            the subcommand exits.

    Example:
        ``qcom-ptool gen_partition -i platforms/qcs6490-rb3gen2/ufs/partitions.conf -o partitions.xml``
    """
    parser = _build_parser()
    args, rest = parser.parse_known_args()

    module_name = SUBCOMMANDS[args.subcommand]
    # Present argv to the legacy script as if it had been invoked directly as
    # "<subcommand> <args...>". The scripts read sys.argv via getopt.
    sys.argv = [f"qcom-ptool {args.subcommand}", *rest]
    runpy.run_module(module_name, run_name="__main__")


if __name__ == "__main__":
    main()
