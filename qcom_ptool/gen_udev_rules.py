# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause

"""Generate udev rules for Qualcomm raw partitions."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from qcom_ptool.loaders import load as load_spec

DATA_DIR = Path(__file__).with_name("data")
FILESYSTEM_NAMES_FILE = DATA_DIR / "filesystem-partition-names.list"
TEMPLATE_FILE = DATA_DIR / "55-qcom-raw-partitions-noblkid.rules.in"
RULES_PLACEHOLDER = "@QCOM_RAW_PARTITION_RULES@"
NAME_RE = re.compile(r"[A-Za-z0-9_.+-]+")
DEFAULT_LAYOUT_GLOB = "platforms/*/*/partitions.conf"


def load_filesystem_names() -> set[str]:
    """Load names of partitions that may contain filesystems.

    :returns: Partition names from ``filesystem-partition-names.list``.
    :raises ValueError: If a name is invalid or duplicated, or the list is empty.

    Example: ``"rootfs" in load_filesystem_names()`` returns ``True``.
    """
    names: set[str] = set()
    for line_number, line in enumerate(
        FILESYSTEM_NAMES_FILE.read_text(encoding="utf-8").splitlines(), start=1
    ):
        name = line.partition("#")[0].strip()
        if not name:
            continue
        if NAME_RE.fullmatch(name) is None:
            raise ValueError(
                f"{FILESYSTEM_NAMES_FILE}:{line_number}: invalid name: {name}"
            )
        if name in names:
            raise ValueError(
                f"{FILESYSTEM_NAMES_FILE}:{line_number}: duplicate name: {name}"
            )
        names.add(name)

    if not names:
        raise ValueError(f"filesystem name list is empty: {FILESYSTEM_NAMES_FILE}")
    return names


def load_partition_names(inputs: list[Path]) -> set[str]:
    """Load and merge partition names from all supplied layouts.

    :param inputs: Partition layout files to load.
    :returns: Every partition name except empty names and ``last_parti``.
    :raises ValueError: If a layout contains a name unsafe for a udev rule.

    Example: ``load_partition_names([Path("platforms/qcs6490-rb3gen2/ufs/partitions.conf")])``
    """
    names: set[str] = set()
    for path in inputs:
        spec = load_spec(str(path))
        for partitions in spec["partitions"].values():
            for partition in partitions:
                name = partition["label"]
                if name and name != "last_parti":
                    if NAME_RE.fullmatch(name) is None:
                        raise ValueError(f"{path}: invalid partition name: {name}")
                    names.add(name)
    return names


def load_raw_partition_names(inputs: list[Path]) -> list[str]:
    """Return known raw partition names from the supplied layouts.

    :param inputs: Partition layout files to load.
    :returns: Sorted names that are not listed as filesystem partitions.

    Example: ``"xbl_a" in load_raw_partition_names(layouts)`` returns ``True`` for a
    layout with an ``xbl_a`` partition.
    """
    return sorted(load_partition_names(inputs) - load_filesystem_names())


def discover_inputs(inputs: list[Path] | None) -> list[Path]:
    """Use explicit layouts or discover all layouts in the current repo.

    :param inputs: Explicit layout paths, or ``None``/empty to search
        ``platforms/*/*/partitions.conf`` below the current directory.
    :returns: The layout paths to scan.
    :raises ValueError: If no layout is supplied or found.

    Example: ``discover_inputs(None)`` run from the repository root returns every
    ``partitions.conf`` under ``platforms/``.
    """
    if inputs:
        return inputs

    discovered = sorted(Path.cwd().glob(DEFAULT_LAYOUT_GLOB))
    if not discovered:
        raise ValueError(
            "no partition layouts found; run from the qcom-ptool repository "
            "or provide one or more -i/--input paths"
        )
    return discovered


def render_rules(names: list[str]) -> str:
    """Render the udev rules template for the supplied partition names.

    :param names: Raw partition names to match.
    :returns: The rules file text with one ``ENV{PARTNAME}`` rule per name.
    :raises ValueError: If the template does not contain exactly one placeholder.

    Example: ``render_rules(["xbl_a"])`` contains ``ENV{PARTNAME}=="xbl_a"``.
    """
    rules = "\n".join(
        f'ENV{{PARTNAME}}=="{name}", GOTO="qcom_raw_noblkid"'
        for name in names
    )
    template = TEMPLATE_FILE.read_text(encoding="utf-8")
    if template.count(RULES_PLACEHOLDER) != 1:
        raise ValueError("rules template must contain exactly one placeholder")
    return template.replace(RULES_PLACEHOLDER, rules)


def generate_rules(inputs: list[Path] | None = None) -> str:
    """Render rules for raw partitions in all supplied layouts.

    :param inputs: Explicit layout paths, or ``None`` to discover them.
    :returns: The rendered rules file text.
    :raises ValueError: If no layout is found or a name or template is invalid.

    Example: ``generate_rules()`` run from the repository root renders rules for all layouts.
    """
    return render_rules(load_raw_partition_names(discover_inputs(inputs)))


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse the ``gen_udev_rules`` command-line options.

    :param argv: Arguments without the program name; ``None`` reads ``sys.argv``.
    :returns: Namespace with ``input`` (list of paths or ``None``) and ``output``.
    :raises SystemExit: With status 2 when ``-o/--output`` is missing.

    Example: ``parse_args(["-o", "55-qcom-raw-partitions-noblkid.rules"]).input`` returns ``None``.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-i",
        "--input",
        action="append",
        type=Path,
        help="partition layout to scan; may be repeated (defaults to platforms/*/*/partitions.conf)",
    )
    parser.add_argument("-o", "--output", required=True, type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Write the udev rules file for raw Qualcomm partitions.

    :param argv: Arguments without the program name; ``None`` reads ``sys.argv``.
    :returns: 0 on success, or 2 when a layout, name list, template or output fails.

    Example: ``main(["-o", "55-qcom-raw-partitions-noblkid.rules"])`` prints
    ``generated: 55-qcom-raw-partitions-noblkid.rules``.
    """
    args = parse_args(argv)
    try:
        content = generate_rules(args.input)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(content, encoding="utf-8")
    except (OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    print(f"generated: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
