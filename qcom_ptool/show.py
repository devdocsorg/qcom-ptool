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
    """Print the ``show`` usage text and exit.

    :raises SystemExit: Always, with status 1.

    Example: ``qcom-ptool show`` without ``--board`` calls this function.
    """
    print(
        "\n\tUsage: %s --board <board.yaml> [--hlos <name>] "
        "[--boot-fw <name>] [--root <dir>]\n" % sys.argv[0]
    )
    sys.exit(1)


def main(argv: list[str] | None = None) -> int:
    """Resolve a board file and print the result as YAML.

    :param argv: Command line including the program name; defaults to ``sys.argv``.
    :returns: 0 on success, or 1 when the board cannot be resolved.
    :raises SystemExit: With status 1 when ``--board`` is missing or an option is invalid.

    Example: ``main(["show", "--board", "platforms/boards/glymur-crd.yaml"])`` prints
    both storages of the Glymur-CRD board.
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
