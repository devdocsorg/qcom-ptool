# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause
"""
CLI tests for board-mode ``gen_partition`` and the ``show`` subcommand.
"""

from __future__ import annotations

import textwrap

import pytest

from qcom_ptool import gen_partition, show

GUID_A = "C12A7328-F81F-11D2-BA4B-00A0C93EC93B"
GUID_B = "B921B045-1DF0-41C3-AF44-4C6F280D3FAE"

_BOARD = """
    platform: {name: demo}
    storage:
      - id: nvme0
        type: nvme
        size: 68719476736
        sector-size: 512
        write-protect-boundary: 65536
        grow-last-partition: true
        partitions:
          - name: efi
            size: "524288KB"
            type-guid: "%s"
            filename: efi.bin
      - id: spinor0
        type: spinor
        size: 67108864
        sector-size: 4096
        write-protect-boundary: 0
        partitions:
          - name: cdt
            size: "4KB"
            type-guid: "%s"
            filename: cdt.bin
""" % (GUID_A, GUID_B)


def _board(tmp_path) -> str:
    """Write the demo board file below a temporary ``platforms/boards`` directory.

    :param tmp_path: Temporary directory for test files.
    :type tmp_path: pathlib.Path
    :returns: Path of the board file.

    Example: ``_board(tmp_path)``
    """
    root = tmp_path / "platforms"
    (root / "boards").mkdir(parents=True)
    path = root / "boards" / "demo.yaml"
    path.write_text(textwrap.dedent(_BOARD))
    return str(path)


def test_board_mode_emits_one_xml_per_storage(tmp_path):
    """Check that ``--board`` writes one XML file per storage.

    :param tmp_path: Temporary directory for test files.
    :type tmp_path: pathlib.Path

    Example: ``pytest tests/unit/test_cli_board.py::test_board_mode_emits_one_xml_per_storage``
    """
    board = _board(tmp_path)
    nvme = tmp_path / "nvme.xml"
    spinor = tmp_path / "spinor.xml"
    rc = gen_partition.main(
        ["gen_partition", "--board", board, "-o", str(nvme), "-o", str(spinor)]
    )
    assert rc == 0
    assert 'label="efi"' in nvme.read_text()
    assert 'label="cdt"' in spinor.read_text()


def test_board_mode_output_count_mismatch_returns_1(tmp_path):
    """Check that ``--board`` returns 1 when the output count differs from the storage count.

    :param tmp_path: Temporary directory for test files.
    :type tmp_path: pathlib.Path

    Example: ``pytest tests/unit/test_cli_board.py::test_board_mode_output_count_mismatch_returns_1``
    """
    board = _board(tmp_path)
    rc = gen_partition.main(
        ["gen_partition", "--board", board, "-o", str(tmp_path / "only.xml")]
    )
    assert rc == 1


def test_requires_exactly_one_source(tmp_path):
    """Check that ``-i`` and ``--board`` together are rejected.

    :param tmp_path: Temporary directory for test files.
    :type tmp_path: pathlib.Path

    Example: ``pytest tests/unit/test_cli_board.py::test_requires_exactly_one_source``
    """
    board = _board(tmp_path)
    # both -i and --board -> usage() exits.
    with pytest.raises(SystemExit):
        gen_partition.main(
            ["gen_partition", "-i", "x.conf", "--board", board, "-o", "out.xml"]
        )


def test_legacy_single_storage_still_works(tmp_path):
    """Check that ``-i`` with a single-storage YAML file still writes XML.

    :param tmp_path: Temporary directory for test files.
    :type tmp_path: pathlib.Path

    Example: ``pytest tests/unit/test_cli_board.py::test_legacy_single_storage_still_works``
    """
    src = tmp_path / "single.yaml"
    src.write_text(
        textwrap.dedent(
            """
            disk:
              type: nvme
              size: 68719476736
            partitions:
              - name: efi
                size: "524288KB"
                type-guid: "%s"
                filename: efi.bin
            """ % GUID_A
        )
    )
    out = tmp_path / "out.xml"
    rc = gen_partition.main(["gen_partition", "-i", str(src), "-o", str(out)])
    assert rc == 0
    assert 'label="efi"' in out.read_text()


def test_show_prints_resolved_spec(tmp_path, capsys):
    """Check that ``show`` prints every resolved storage.

    :param tmp_path: Temporary directory for test files.
    :type tmp_path: pathlib.Path
    :param capsys: Captures standard output.
    :type capsys: pytest.CaptureFixture[str]

    Example: ``pytest tests/unit/test_cli_board.py::test_show_prints_resolved_spec``
    """
    board = _board(tmp_path)
    rc = show.main(["show", "--board", board])
    assert rc == 0
    out = capsys.readouterr().out
    assert "nvme0" in out
    assert "spinor0" in out
    assert "cdt" in out


def test_show_applies_variants(tmp_path, capsys):
    """Check that ``show --hlos`` applies the variant overlay.

    :param tmp_path: Temporary directory for test files.
    :type tmp_path: pathlib.Path
    :param capsys: Captures standard output.
    :type capsys: pytest.CaptureFixture[str]

    Example: ``pytest tests/unit/test_cli_board.py::test_show_applies_variants``
    """
    root = tmp_path / "platforms"
    (root / "boards").mkdir(parents=True)
    (root / "variants" / "hlos").mkdir(parents=True)
    (root / "boards" / "demo.yaml").write_text(textwrap.dedent(_BOARD))
    (root / "variants" / "hlos" / "debian.yaml").write_text(
        textwrap.dedent(
            """
            storage:
              - id: nvme0
                partitions:
                  - name: efi
                    filename: efi-debian.bin
            """
        )
    )
    rc = show.main(
        ["show", "--board", str(root / "boards" / "demo.yaml"), "--hlos", "debian"]
    )
    assert rc == 0
    assert "efi-debian.bin" in capsys.readouterr().out


def test_show_requires_board():
    """Check that ``show`` without ``--board`` exits.

    Example: ``pytest tests/unit/test_cli_board.py::test_show_requires_board``
    """
    with pytest.raises(SystemExit):
        show.main(["show"])
