# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause
"""
``qcom-ptool show`` - print a board's fully-resolved spec.

Derived boards and heavy ``includes:`` use make the effective partition
layout impossible to read from a single file. This subcommand resolves all
``extends`` / ``includes`` / variant overlays and prints the result as YAML,
so reviewers and integrators can see exactly what will be emitted without
chasing the composition chain by hand.
"""

from __future__ import annotations

import getopt
import sys
from typing import NoReturn

import yaml  # type: ignore[import-untyped]

from qcom_ptool.board import resolve_board


def usage() -> NoReturn:
    """Print the ``show`` command-line usage and exit with status 1.

    Raises:
        SystemExit: Always.

    Example:
        ``qcom-ptool show`` without ``--board`` prints this usage.
    """
    print(
        "\n\tUsage: %s --board <board.yaml> [--hlos <name>] "
        "[--boot-fw <name>] [--root <dir>]\n" % sys.argv[0]
    )
    sys.exit(1)


def main(argv: list[str] | None = None) -> int:
    """Run ``show``: print a board's fully resolved storage layout as YAML.

    Args:
        argv (list[str] | None): Command line including the program name; ``sys.argv`` when None.

    Returns:
        int: 0 when the board is printed, 1 when it cannot be resolved.

    Raises:
        SystemExit: ``--board`` is missing or the options are invalid; usage is printed.

    Example:
        ``main(["show", "--board", "platforms/boards/glymur-crd.yaml"])`` prints the
        resolved board and returns ``0``.
    """
    if argv is None:
        argv = sys.argv

    board_file: str | None = None
    root: str | None = None
    hlos: str | None = None
    boot_fw: str | None = None

    try:
        opts, _rem = getopt.getopt(argv[1:], "", ["board=", "hlos=", "boot-fw=", "root="])
        for opt, arg in opts:
            if opt == "--board":
                board_file = arg
            elif opt == "--hlos":
                hlos = arg
            elif opt == "--boot-fw":
                boot_fw = arg
            elif opt == "--root":
                root = arg
    except Exception as argerr:
        print(str(argerr))
        usage()

    if board_file is None:
        usage()

    try:
        board = resolve_board(board_file, root=root, hlos=hlos, boot_fw=boot_fw)
    except Exception as e:
        print("Error: ", e)
        return 1

    yaml.safe_dump(dict(board), sys.stdout, sort_keys=False, default_flow_style=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
