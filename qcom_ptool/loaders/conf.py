# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause
"""
Loader for the legacy ``--disk`` / ``--partition`` line-format files under
``platforms/``.

A ``.conf`` file is an unstructured stream of comment lines, blank lines,
exactly one ``--disk`` line, and any number of ``--partition`` lines. Each
significant line is itself a getopt-style option list. This module parses
both layers and returns a :class:`qcom_ptool.spec.LoadedSpec`.

The parsing helpers are kept individually addressable so the unit tests
under ``tests/unit/`` can characterise each layer in isolation.
"""

from __future__ import annotations

import getopt
import re
from collections.abc import Mapping

from qcom_ptool.spec import (
    DISK_PARAMS_DEFAULTS,
    PARTITION_ENTRY_DEFAULTS,
    DiskParams,
    LoadedSpec,
    PartitionEntry,
    PartitionsByLun,
)


class ConfParseError(ValueError):
    """Raised when a ``.conf`` file cannot be parsed."""


# ---------------------------------------------------------------------------
# Size string parsing
# ---------------------------------------------------------------------------


def partition_size_in_kb(size: str) -> int:
    """Convert a size string ("1024", "1KB", "2MB", "1GB") to KB.

    Bare integers are interpreted as bytes and divided by 1024. Strings with a
    K/M/G suffix (any case, with optional 'B') return the kilobyte equivalent.
    Anything else raises ``ValueError``; callers may catch and reformat.

    :param size: Size string.
    :returns: Size in kilobytes.
    :raises ValueError: If the string has letters but no K, M or G suffix.

    Example: ``partition_size_in_kb("2MB")`` returns ``2048``.
    """
    if not re.search("[a-zA-Z]+", size):
        return int(size) // 1024
    m = re.search("([0-9]+)(?=[Kk][Bb]?)", size)
    if m:
        return int(m.group(0))
    m = re.search("([0-9]+)(?=[Mm][Bb]?)", size)
    if m:
        return int(m.group(0)) * 1024
    m = re.search("([0-9]+)(?=[Gg][Bb]?)", size)
    if m:
        return int(m.group(0)) * 1024 * 1024
    raise ValueError("Unrecognized size format: '%s'" % size)


# ---------------------------------------------------------------------------
# Option-list -> normalised dict
# ---------------------------------------------------------------------------


def disk_options(argv: list[tuple[str, str]]) -> DiskParams:
    """Translate parsed ``--disk`` options into the canonical disk dict.

    :param argv: ``(option, value)`` pairs from :func:`getopt.gnu_getopt`.
    :returns: A copy of ``DISK_PARAMS_DEFAULTS`` updated from the options.

    Example: ``disk_options([("--type", "ufs")])["type"]`` returns ``"ufs"``.
    """
    disk = DISK_PARAMS_DEFAULTS.copy()
    for opt, arg in argv:
        if opt == "--type":
            disk["type"] = arg
        elif opt == "--size":
            disk["size"] = arg
        elif opt == "--sector-size-in-bytes":
            disk["SECTOR_SIZE_IN_BYTES"] = arg
        elif opt == "--write-protect-boundary":
            disk["WRITE_PROTECT_BOUNDARY_IN_KB"] = arg
        elif opt == "--grow-last-partition":
            disk["GROW_LAST_PARTITION_TO_FILL_DISK"] = "true"
        elif opt == "--align-partitions":
            disk["ALIGN_PARTITIONS_TO_PERFORMANCE_BOUNDARY"] = "true"
            disk["PERFORMANCE_BOUNDARY_IN_KB"] = str(int(arg) // 1024)
    return disk


def to_bool(arg: str) -> str:
    """Normalise a boolean option value to ``"true"`` or ``"false"``.

    :param arg: Option value; ``1``, ``y``, ``yes`` and ``true`` in any case are true.
    :returns: ``"true"`` or ``"false"``.

    Example: ``to_bool("Yes")`` returns ``"true"``.
    """
    return "true" if arg.strip().lower() in ("1", "y", "yes", "true") else "false"


def partition_options(
    argv: list[tuple[str, str]],
    image_map: Mapping[str, str] | None = None,
) -> tuple[str, PartitionEntry]:
    """Translate parsed ``--partition`` options into ``(phys_part, entry)``.

    ``image_map`` (if provided) overrides the entry's ``filename`` when the
    partition name matches a key. The override is applied after all options
    have been processed, so it always wins over an explicit ``--filename``.

    :param argv: ``(option, value)`` pairs from :func:`getopt.gnu_getopt`.
    :param image_map: Partition name to image filename overrides.
    :returns: The LUN or physical partition as a string, and the partition entry.
    :raises ValueError: If a size, attribute, priority or retry value is malformed.

    Example: ``partition_options([("--lun", "1"), ("--name", "xbl_a")])[0]`` returns ``"1"``.
    """
    if image_map is None:
        image_map = {}
    entry: PartitionEntry = PARTITION_ENTRY_DEFAULTS.copy()
    phys_part: str = "0"
    # Intentional: --attributes first so a named flag always wins.
    for opt, arg in argv:
        if opt == "--attributes":
            attribute_bits = int(arg, 16)
            entry["bootable"] = "true" if attribute_bits & (1 << 2) else "false"
            entry["readonly"] = "true" if attribute_bits & (1 << 60) else "false"
    for opt, arg in argv:
        if opt in ("--lun", "--phys-part"):
            phys_part = arg
        elif opt == "--name":
            entry["label"] = arg
        elif opt == "--size":
            entry["size_in_kb"] = str(partition_size_in_kb(arg))
        elif opt == "--type-guid":
            entry["type"] = arg
        elif opt == "--bootable":
            entry["bootable"] = to_bool(arg)
        elif opt == "--readonly":
            entry["readonly"] = to_bool(arg)
        elif opt == "--priority":
            entry["priority"] = str(int(arg) & 0x03)
        elif opt == "--tries-remaining":
            entry["triesremaining"] = str(int(arg) & 0x07)
        elif opt == "--active":
            entry["active"] = to_bool(arg)
        elif opt == "--successful":
            entry["successful"] = to_bool(arg)
        elif opt == "--unbootable":
            entry["unbootable"] = to_bool(arg)
        elif opt == "--filename":
            entry["filename"] = arg
        elif opt == "--sparse":
            entry["sparse"] = to_bool(arg)
        elif opt == "--uniqueguid":
            entry["uniqueguid"] = arg
    if entry["label"] in image_map:
        entry["filename"] = image_map[entry["label"]]
    return phys_part, entry


# ---------------------------------------------------------------------------
# Line-level parsing
# ---------------------------------------------------------------------------


_DISK_LONG_OPTS = [
    "type=",
    "size=",
    "sector-size-in-bytes=",
    "write-protect-boundary=",
    "grow-last-partition",
    "align-partitions=",
]

_PARTITION_LONG_OPTS = [
    "lun=",
    "phys-part=",
    "name=",
    "size=",
    "type-guid=",
    "filename=",
    "attributes=",
    "bootable=",
    "readonly=",
    "priority=",
    "tries-remaining=",
    "active=",
    "successful=",
    "unbootable=",
    "sparse=",
    "uniqueguid=",
]


def parse_disk_line(line: str) -> DiskParams | None:
    """Parse a single ``--disk ...`` line; return None if the line isn't one.

    :param line: One stripped line from a ``.conf`` file.
    :returns: The disk settings, or ``None`` when the line is not a ``--disk`` line.
    :raises getopt.GetoptError: If the line contains an unknown option.

    Example: ``parse_disk_line("--disk --type=emmc --size=1024")["type"]`` returns ``"emmc"``.
    """
    opts_list = line.split(" ")
    if not opts_list or opts_list[0] != "--disk":
        return None
    options, _rem = getopt.gnu_getopt(opts_list[1:], "", _DISK_LONG_OPTS)
    return disk_options(options)


def parse_partition_lines(
    lines: list[str],
    image_map: Mapping[str, str] | None = None,
) -> PartitionsByLun:
    """Parse a list of ``--partition ...`` lines, grouped by LUN/phys-part.

    :param lines: Stripped lines; lines that are not ``--partition`` lines are skipped.
    :param image_map: Partition name to image filename overrides.
    :returns: Partition entries grouped by LUN or physical partition.
    :raises getopt.GetoptError: If a line contains an unknown option.

    Example: ``parse_partition_lines(["--partition --name=efi --size=4KB"])["0"][0]["label"]``
    returns ``"efi"``.
    """
    if image_map is None:
        image_map = {}
    partitions: PartitionsByLun = {}
    for line in lines:
        opts_list = line.split(" ")
        if not opts_list or opts_list[0] != "--partition":
            continue
        options, _rem = getopt.gnu_getopt(opts_list[1:], "", _PARTITION_LONG_OPTS)
        phys_part, entry = partition_options(options, image_map)
        partitions.setdefault(phys_part, []).append(entry)
    return partitions


# ---------------------------------------------------------------------------
# File-level parsing
# ---------------------------------------------------------------------------


def read_conf(path: str) -> tuple[str, list[str]]:
    """Read ``path`` and return ``(disk_line, [partition_lines])``.

    Comments (``#``-prefixed) and blank lines are skipped. Multiple ``--disk``
    lines are an error. Lines that aren't ``--disk`` or ``--partition`` are
    printed as "Ignoring ..." for parity with the original behaviour.

    :param path: ``.conf`` file to read.
    :returns: The ``--disk`` line and the ``--partition`` lines in file order.
    :raises ConfParseError: If the file has no ``--disk`` line or more than one.

    Example: ``read_conf("platforms/qcs6490-rb3gen2/ufs/partitions.conf")[0]`` returns the
    ``--disk`` line.
    """
    disk_line: str | None = None
    partition_lines: list[str] = []
    with open(path) as f:
        for raw in f:
            if re.search(r"^\s*#", raw) or re.search(r"^\s*$", raw):
                continue
            line = raw.strip()
            if line.startswith("--disk"):
                if disk_line is not None:
                    raise ConfParseError(
                        "%s contains more than one --disk entries:\n%s\n%s"
                        % (path, disk_line, line)
                    )
                disk_line = line
            elif line.startswith("--partition"):
                partition_lines.append(line)
            else:
                print("Ignoring %s" % line)
    if disk_line is None:
        raise ConfParseError("%s contains no --disk entry" % path)
    return disk_line, partition_lines


def load(path: str, image_map: Mapping[str, str] | None = None) -> LoadedSpec:
    """Public entry point: read ``path`` and return a normalised ``LoadedSpec``.

    :param path: ``.conf`` file to read.
    :param image_map: Partition name to image filename overrides.
    :returns: The normalised disk settings and partitions.
    :raises ConfParseError: If the file has no ``--disk`` line or more than one.

    Example: ``load("platforms/apq8016-sbc/emmc/partitions.conf")["disk"]["type"]`` returns ``"emmc"``.
    """
    disk_line, partition_lines = read_conf(path)
    disk = parse_disk_line(disk_line)
    if disk is None:
        # Should be unreachable: read_conf guarantees disk_line starts with --disk.
        raise ConfParseError("%s: failed to parse --disk line" % path)
    partitions = parse_partition_lines(partition_lines, image_map)
    return {"disk": disk, "partitions": partitions}
