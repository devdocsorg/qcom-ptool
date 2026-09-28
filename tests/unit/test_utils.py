# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause

"""Unit tests for qcom_ptool.utils."""

import binascii
import pytest

from qcom_ptool.utils import CalcCRC32, EnsureDirectoryExists, reflect


class TestReflect:
    def test_reflect_single_bit_8(self):
        """Check that one 8-bit value is reflected.

        Example: ``pytest tests/unit/test_utils.py::TestReflect::test_reflect_single_bit_8``
        """
        assert reflect(0b00000001, 8) == 0b10000000
        assert reflect(0b10000000, 8) == 0b00000001

    def test_reflect_is_involution(self):
        # Reflecting twice must return the original value.
        """Check that reflecting twice returns the original value.

        Example: ``pytest tests/unit/test_utils.py::TestReflect::test_reflect_is_involution``
        """
        for value in (0x00, 0x01, 0x5A, 0xA5, 0xFF, 0x12345678):
            nbits = 8 if value <= 0xFF else 32
            assert reflect(reflect(value, nbits), nbits) == value

    def test_reflect_32(self):
        """Check a 32-bit reflection.

        Example: ``pytest tests/unit/test_utils.py::TestReflect::test_reflect_32``
        """
        assert reflect(0x00000001, 32) == 0x80000000
        assert reflect(0x12345678, 32) == 0x1E6A2C48


class TestCalcCRC32:
    """CalcCRC32 implements standard CRC-32 (IEEE 802.3, reflected),
    so binascii.crc32 is used as an independent reference."""

    def test_known_check_value(self):
        # "123456789" -> 0xCBF43926 is the canonical CRC-32 check value.
        """Check the standard CRC-32 check value.

        Example: ``pytest tests/unit/test_utils.py::TestCalcCRC32::test_known_check_value``
        """
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
        """Check that the result matches ``binascii.crc32``.

        :param data: Bytes to checksum.
        :type data: bytes

        Example: ``pytest tests/unit/test_utils.py::TestCalcCRC32::test_matches_binascii_crc32``
        """
        assert CalcCRC32(data, len(data)) == binascii.crc32(data) & 0xFFFFFFFF

    def test_partial_length(self):
        # Only the first Len bytes participate in the checksum.
        """Check that only the requested length is checksummed.

        Example: ``pytest tests/unit/test_utils.py::TestCalcCRC32::test_partial_length``
        """
        data = b"123456789XXXX"
        assert CalcCRC32(data, 9) == 0xCBF43926

    def test_accepts_list_input(self):
        # GPT code paths pass mutable sequences, not only bytes.
        """Check that a list of byte values is accepted.

        Example: ``pytest tests/unit/test_utils.py::TestCalcCRC32::test_accepts_list_input``
        """
        data = list(b"123456789")
        assert CalcCRC32(data, len(data)) == 0xCBF43926


class TestEnsureDirectoryExists:
    def test_creates_missing_parents(self, tmp_path):
        """Check that missing parents are created.

        :param tmp_path: Temporary directory for test files.
        :type tmp_path: pathlib.Path

        Example: ``pytest tests/unit/test_utils.py::TestEnsureDirectoryExists::test_creates_missing_parents``
        """
        target = tmp_path / "a" / "b" / "c" / "file.bin"
        EnsureDirectoryExists(str(target))
        assert (tmp_path / "a" / "b" / "c").is_dir()
        assert not target.exists()  # only the directory is created

    def test_existing_directory_is_noop(self, tmp_path):
        """Check that an existing directory is left unchanged.

        :param tmp_path: Temporary directory for test files.
        :type tmp_path: pathlib.Path

        Example: ``pytest tests/unit/test_utils.py::TestEnsureDirectoryExists::test_existing_directory_is_noop``
        """
        target = tmp_path / "file.bin"
        EnsureDirectoryExists(str(target))
        EnsureDirectoryExists(str(target))  # second call must not raise
        assert tmp_path.is_dir()
