# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause

import os
import sys


def EnsureDirectoryExists(filename):
    """Create the parent directory of a file path when it does not exist.

    :param filename: Path whose directory component must exist.
    :type filename: str
    :raises OSError: If the directory cannot be created.

    Example: ``EnsureDirectoryExists("out/rawprogram0.xml")`` creates ``out/``.
    """
    dir = os.path.dirname(filename)
    try:
        os.stat(dir)
    except OSError:
        os.makedirs(dir)


def PrintBigWarning(sz, log_func=print):
    """Print a large WARNING banner followed by an optional message.

    :param sz: Message printed after the banner; an empty string prints only the banner.
    :type sz: str
    :param log_func: Function that receives each output line.
    :type log_func: collections.abc.Callable

    Example: ``PrintBigWarning("SECTOR_SIZE_IN_BYTES changed")``
    """
    log_func("\t                          _             ")
    log_func("\t                         (_)            ")
    log_func("\t__      ____ _ _ __ _ __  _ _ __   __ _ ")
    log_func("\t\\ \\ /\\ / / _` | '__| '_ \\| | '_ \\ / _` |")
    log_func("\t \\ V  V / (_| | |  | | | | | | | | (_| |")
    log_func("\t  \\_/\\_/ \\__,_|_|  |_| |_|_|_| |_|\\__, |")
    log_func("\t                                   __/ |")
    log_func("\t                                  |___/ \n")
    if len(sz) > 0:
        log_func(sz)


def PrintBigError(sz, log_func=print):
    """Print a large ERROR banner and exit when a message is supplied.

    :param sz: Error message; a non-empty message ends the program with status 1.
    :type sz: str
    :param log_func: Function that receives each output line.
    :type log_func: collections.abc.Callable
    :raises SystemExit: With status 1 when ``sz`` is not empty.

    Example: ``PrintBigError("ERROR: Could not find file")`` exits with status 1.
    """
    log_func("\t _________________ ___________ ")
    log_func("\t|  ___| ___ \\ ___ \\  _  | ___ \\")
    log_func("\t| |__ | |_/ / |_/ / | | | |_/ /")
    log_func("\t|  __||    /|    /| | | |    / ")
    log_func("\t| |___| |\\ \\| |\\ \\\\ \\_/ / |\\ \\ ")
    log_func("\t\\____/\\_| \\_\\_| \\_|\\___/\\_| \\_|\n")
    if len(sz) > 0:
        log_func(sz)
        sys.exit(1)


def reflect(data, nBits):
    """Reverse the order of the lowest ``nBits`` bits of an integer.

    :param data: Value whose bits are reflected.
    :type data: int
    :param nBits: Number of low-order bits to reflect.
    :type nBits: int
    :returns: The reflected value.
    :rtype: int

    Example: ``reflect(0x01, 8)`` returns ``0x80``.
    """
    reflection = 0x00000000
    for bit in range(nBits):
        if data & 0x01:
            reflection |= 1 << ((nBits - 1) - bit)
        data = data >> 1
    return reflection


def CalcCRC32(array, Len):
    """Calculate the IEEE CRC-32 used in GPT headers and partition arrays.

    :param array: Bytes, or a list of byte values, to checksum.
    :type array: bytes | list[int]
    :param Len: Number of leading bytes of ``array`` to include.
    :type Len: int
    :returns: The CRC-32 value, matching :func:`binascii.crc32`.
    :rtype: int

    Example: ``CalcCRC32(b"123456789", 9)`` returns ``0xCBF43926``.
    """
    k = 8  # length of unit (i.e. byte)
    MSB = 0
    gx = 0x04C11DB7  # IEEE 32bit polynomial
    regs = 0xFFFFFFFF  # init to all ones
    regsMask = 0xFFFFFFFF  # ensure only 32 bit answer

    for i in range(int(Len)):
        DataByte = array[i]
        DataByte = reflect(DataByte, 8)

        for _j in range(k):
            MSB = DataByte >> (k - 1)  ## get MSB
            MSB &= 1  ## ensure just 1 bit

            regsMSB = (regs >> 31) & 1

            regs = regs << 1  ## shift regs for CRC-CCITT

            if regsMSB ^ MSB:  ## MSB is a 1
                regs = regs ^ gx  ## XOR with generator poly

            regs = regs & regsMask  ## Mask off excess upper bits

            DataByte <<= 1  ## get to next bit

    regs = regs & regsMask
    ReflectedRegs = reflect(regs, 32) ^ 0xFFFFFFFF

    return ReflectedRegs
