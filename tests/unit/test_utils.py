# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause

"""Unit tests for qcom_ptool.utils."""

import binascii
import pytest

from qcom_ptool.utils import CalcCRC32, EnsureDirectoryExists, reflect


class TestReflect:
    """Tests for ``reflect``, the bit-order reversal used by the CRC code."""
    def test_reflect_single_bit_8(self):
        """Check that reflecting 8 bits moves the lowest bit to the highest and back.

        Example:
            ``pytest "tests/unit/test_utils.py::TestReflect::test_reflect_single_bit_8"``
        """
        assert reflect(0b00000001, 8) == 0b10000000
        assert reflect(0b10000000, 8) == 0b00000001

    def test_reflect_is_involution(self):
        """Check that reflecting a value twice returns the original value.

        Example:
            ``pytest "tests/unit/test_utils.py::TestReflect::test_reflect_is_involution"``
        """
        # Reflecting twice must return the original value.
        for value in (0x00, 0x01, 0x5A, 0xA5, 0xFF, 0x12345678):
            nbits = 8 if value <= 0xFF else 32
            assert reflect(reflect(value, nbits), nbits) == value

    def test_reflect_32(self):
        """Check 32-bit reflection against known values.

        Example:
            ``pytest "tests/unit/test_utils.py::TestReflect::test_reflect_32"``
        """
        assert reflect(0x00000001, 32) == 0x80000000
        assert reflect(0x12345678, 32) == 0x1E6A2C48


class TestCalcCRC32:
    """CalcCRC32 implements standard CRC-32 (IEEE 802.3, reflected),
    so binascii.crc32 is used as an independent reference."""

    def test_known_check_value(self):
        """Check that ``CalcCRC32`` returns the canonical CRC-32 check value for "123456789".

        Example:
            ``pytest "tests/unit/test_utils.py::TestCalcCRC32::test_known_check_value"``
        """
        # "123456789" -> 0xCBF43926 is the canonical CRC-32 check value.
        data = b"123456789"
        assert CalcCRC32(data, len(data)) == 0xCBF43926

    @pytest.mark.parametrize(
        "data",
        [
            b"",
            b"\x00",
            b"\xff" * 16,
            bytes(range(256)),
            b"qcom-ptool",
        ],
        ids=["empty", "single-nul", "all-ones", "all-bytes", "ascii"],
    )
    def test_matches_binascii_crc32(self, data):
        """Check that ``CalcCRC32`` matches ``binascii.crc32`` for the parametrised data.

        Args:
            data (bytes): Input bytes supplied by the parametrisation.

        Example:
            ``pytest "tests/unit/test_utils.py::TestCalcCRC32::test_matches_binascii_crc32"``
        """
        assert CalcCRC32(data, len(data)) == binascii.crc32(data) & 0xFFFFFFFF

    def test_partial_length(self):
        """Check that only the first ``Len`` bytes contribute to the checksum.

        Example:
            ``pytest "tests/unit/test_utils.py::TestCalcCRC32::test_partial_length"``
        """
        # Only the first Len bytes participate in the checksum.
        data = b"123456789XXXX"
        assert CalcCRC32(data, 9) == 0xCBF43926

    def test_accepts_list_input(self):
        """Check that ``CalcCRC32`` accepts a list of byte values as well as ``bytes``.

        Example:
            ``pytest "tests/unit/test_utils.py::TestCalcCRC32::test_accepts_list_input"``
        """
        # GPT code paths pass mutable sequences, not only bytes.
        data = list(b"123456789")
        assert CalcCRC32(data, len(data)) == 0xCBF43926


class TestEnsureDirectoryExists:
    """Tests for ``EnsureDirectoryExists``, which creates a file's parent folders."""
    def test_creates_missing_parents(self, tmp_path):
        """Check that missing parent folders are created and the file itself is not.

        Args:
            tmp_path (pathlib.Path): Per-test temporary directory from pytest.

        Example:
            ``pytest "tests/unit/test_utils.py::TestEnsureDirectoryExists::test_creates_missing_parents"``
        """
        target = tmp_path / "a" / "b" / "c" / "file.bin"
        EnsureDirectoryExists(str(target))
        assert (tmp_path / "a" / "b" / "c").is_dir()
        assert not target.exists()  # only the directory is created

    def test_existing_directory_is_noop(self, tmp_path):
        """Check that calling it for an existing folder succeeds without error.

        Args:
            tmp_path (pathlib.Path): Per-test temporary directory from pytest.

        Example:
            ``pytest "tests/unit/test_utils.py::TestEnsureDirectoryExists::test_existing_directory_is_noop"``
        """
        target = tmp_path / "file.bin"
        EnsureDirectoryExists(str(target))
        EnsureDirectoryExists(str(target))  # second call must not raise
        assert tmp_path.is_dir()
