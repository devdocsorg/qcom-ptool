# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause

"""Tests for qcom_ptool.gen_partition."""

import subprocess
import sys
import xml.etree.ElementTree as ET

import pytest

BASIC_CONF = """\
# comment lines and blank lines are ignored

--disk --type=emmc --size=16777216 --sector-size-in-bytes=512

--partition --name=cdt --size=2KB --type-guid=A19F205F-CCD8-4B6D-8F1E-2D9BC24CFFB1 --filename=cdt.bin
--partition --name=boot --size=64MB --type-guid=20117F86-E985-4357-B9EE-374BC1D8487D --attributes=0x0000000000000004
--partition --name=rootfs --size=1GB --type-guid=97D7B011-54DA-4835-B3C4-917AD6E73D74 --attributes=0x1000000000000000
"""


def run_gen_partition(tmp_path, conf_text, extra_args=()):
    """Write a ``partitions.conf`` and run ``python -m qcom_ptool.gen_partition`` on it.

    Args:
        tmp_path (pathlib.Path): Folder for the input and output files.
        conf_text (str): Contents of the ``partitions.conf`` to write.
        extra_args (Sequence[str]): Additional command-line arguments, such as ``-m``.

    Returns:
        tuple[subprocess.CompletedProcess[str], pathlib.Path]: The finished process
        and the path of the ``partitions.xml`` it was asked to write.

    Example:
        ``result, out = run_gen_partition(tmp_path, BASIC_CONF)``
    """
    conf = tmp_path / "partitions.conf"
    out = tmp_path / "partitions.xml"
    conf.write_text(conf_text, encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "qcom_ptool.gen_partition",
            "-i",
            str(conf),
            "-o",
            str(out),
            *extra_args,
        ],
        capture_output=True,
        text=True,
        timeout=10,
    )
    return result, out


@pytest.fixture(scope="module")
def basic_output(tmp_path_factory):
    """Generate the XML for ``BASIC_CONF`` once per module and parse it.

    Args:
        tmp_path_factory (pytest.TempPathFactory): Creates the module-scoped temporary folder.

    Returns:
        xml.etree.ElementTree.Element: Root ``configuration`` element of the generated XML.

    Example:
        ``def test_x(basic_output): assert basic_output.tag == "configuration"``
    """
    tmp_path = tmp_path_factory.mktemp("gen_partition")
    result, out = run_gen_partition(tmp_path, BASIC_CONF)
    assert result.returncode == 0, result.stdout + result.stderr
    return ET.parse(out).getroot()


def get_partitions(root):
    """Map each partition label in a generated XML tree to its element.

    Args:
        root (xml.etree.ElementTree.Element): Root ``configuration`` element.

    Returns:
        dict[str, xml.etree.ElementTree.Element]: Partition elements by ``label``.

    Example:
        ``get_partitions(basic_output)["cdt"].get("filename")`` returns ``"cdt.bin"``.
    """
    return {
        p.get("label"): p
        for phys in root.findall("physical_partition")
        for p in phys.findall("partition")
    }


def test_generates_configuration_root(basic_output):
    """Check that the output has a ``configuration`` root, parser instructions, and one physical partition.

    Args:
        basic_output (xml.etree.ElementTree.Element): Root of the XML generated from ``BASIC_CONF``.

    Example:
        ``pytest tests/unit/test_gen_partition.py::test_generates_configuration_root``
    """
    assert basic_output.tag == "configuration"
    assert basic_output.find("parser_instructions") is not None
    assert len(basic_output.findall("physical_partition")) == 1


def test_sector_size_in_parser_instructions(basic_output):
    """Check that the ``--sector-size-in-bytes`` value appears in the parser instructions.

    Args:
        basic_output (xml.etree.ElementTree.Element): Root of the XML generated from ``BASIC_CONF``.

    Example:
        ``pytest tests/unit/test_gen_partition.py::test_sector_size_in_parser_instructions``
    """
    text = basic_output.find("parser_instructions").text
    assert "SECTOR_SIZE_IN_BYTES=512" in text


@pytest.mark.parametrize(
    ("label", "expected_kb"),
    [("cdt", "2"), ("boot", str(64 * 1024)), ("rootfs", str(1024 * 1024))],
)
def test_size_suffix_parsing(basic_output, label, expected_kb):
    """Check that KB, MB, and GB size suffixes are converted to ``size_in_kb``.

    Args:
        basic_output (xml.etree.ElementTree.Element): Root of the XML generated from ``BASIC_CONF``.
        label (str): Partition label supplied by the parametrisation.
        expected_kb (str): Expected ``size_in_kb`` value for that partition.

    Example:
        ``pytest "tests/unit/test_gen_partition.py::test_size_suffix_parsing[cdt-2]"``
    """
    # KB / MB / GB suffixes must all normalize to size_in_kb.
    assert get_partitions(basic_output)[label].get("size_in_kb") == expected_kb


def test_plain_size_is_interpreted_as_bytes(tmp_path):
    """Check that a size without a suffix is read as bytes.

    Args:
        tmp_path (pathlib.Path): Per-test temporary directory from pytest.

    Example:
        ``pytest tests/unit/test_gen_partition.py::test_plain_size_is_interpreted_as_bytes``
    """
    conf = """\
--disk --type=emmc --size=16777216
--partition --name=data --size=4096
"""
    result, out = run_gen_partition(tmp_path, conf)
    assert result.returncode == 0, result.stdout + result.stderr
    part = get_partitions(ET.parse(out).getroot())["data"]
    assert part.get("size_in_kb") == "4"


def test_attribute_bit2_sets_bootable(basic_output):
    """Check that attribute bit 2 marks a partition bootable and not read-only.

    Args:
        basic_output (xml.etree.ElementTree.Element): Root of the XML generated from ``BASIC_CONF``.

    Example:
        ``pytest tests/unit/test_gen_partition.py::test_attribute_bit2_sets_bootable``
    """
    parts = get_partitions(basic_output)
    assert parts["boot"].get("bootable") == "true"
    assert parts["boot"].get("readonly") == "false"


def test_attribute_bit60_sets_readonly(basic_output):
    """Check that attribute bit 60 marks a partition read-only and not bootable.

    Args:
        basic_output (xml.etree.ElementTree.Element): Root of the XML generated from ``BASIC_CONF``.

    Example:
        ``pytest tests/unit/test_gen_partition.py::test_attribute_bit60_sets_readonly``
    """
    parts = get_partitions(basic_output)
    assert parts["rootfs"].get("bootable") == "false"
    assert parts["rootfs"].get("readonly") == "true"


def test_filename_passthrough(basic_output):
    """Check that ``--filename`` is copied to the partition's ``filename`` attribute.

    Args:
        basic_output (xml.etree.ElementTree.Element): Root of the XML generated from ``BASIC_CONF``.

    Example:
        ``pytest tests/unit/test_gen_partition.py::test_filename_passthrough``
    """
    assert get_partitions(basic_output)["cdt"].get("filename") == "cdt.bin"


def test_partition_image_map_overrides_filename(tmp_path):
    """Check that the ``-m`` image map replaces the file names of the named partitions only.

    Args:
        tmp_path (pathlib.Path): Per-test temporary directory from pytest.

    Example:
        ``pytest tests/unit/test_gen_partition.py::test_partition_image_map_overrides_filename``
    """
    result, out = run_gen_partition(
        tmp_path, BASIC_CONF, extra_args=["-m", "cdt=other.bin,boot=boot.img"]
    )
    assert result.returncode == 0, result.stdout + result.stderr
    parts = get_partitions(ET.parse(out).getroot())
    assert parts["cdt"].get("filename") == "other.bin"
    assert parts["boot"].get("filename") == "boot.img"
    assert parts["rootfs"].get("filename") == ""


def test_multiple_luns_sorted(tmp_path):
    """Check that physical partitions are emitted in ascending LUN order.

    Args:
        tmp_path (pathlib.Path): Per-test temporary directory from pytest.

    Example:
        ``pytest tests/unit/test_gen_partition.py::test_multiple_luns_sorted``
    """
    conf = """\
--disk --type=ufs --size=16777216
--partition --lun=2 --name=late --size=1KB
--partition --lun=0 --name=early --size=1KB
"""
    result, out = run_gen_partition(tmp_path, conf)
    assert result.returncode == 0, result.stdout + result.stderr
    root = ET.parse(out).getroot()
    luns = root.findall("physical_partition")
    assert len(luns) == 2
    # physical partitions must be emitted in ascending LUN order
    assert luns[0].find("partition").get("label") == "early"
    assert luns[1].find("partition").get("label") == "late"


def test_duplicate_disk_entry_fails(tmp_path):
    """Check that a file with more than one ``--disk`` line fails with status 1.

    Args:
        tmp_path (pathlib.Path): Per-test temporary directory from pytest.

    Example:
        ``pytest tests/unit/test_gen_partition.py::test_duplicate_disk_entry_fails``
    """
    conf = "--disk --type=emmc --size=1\n--disk --type=emmc --size=2\n--partition --name=a --size=1KB\n"
    result, _ = run_gen_partition(tmp_path, conf)
    assert result.returncode == 1
    assert "more than one --disk" in result.stdout + result.stderr


def test_missing_arguments_shows_usage():
    """Check that running without arguments prints the usage and exits with status 1.

    Example:
        ``pytest tests/unit/test_gen_partition.py::test_missing_arguments_shows_usage``
    """
    result = subprocess.run(
        [sys.executable, "-m", "qcom_ptool.gen_partition"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 1
    assert "Usage" in result.stdout + result.stderr
