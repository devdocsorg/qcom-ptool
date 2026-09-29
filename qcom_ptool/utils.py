# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause

import os
import sys


def EnsureDirectoryExists(filename):
    """Create the directory that will hold a file, if it does not exist yet.

    Args:
        filename (str): Path of a file; its parent directory is created with any
            missing ancestors.

    Raises:
        OSError: The directory cannot be created, for example because
            ``filename`` has no directory part.

    Example:
        ``EnsureDirectoryExists("out/ufs/rawprogram0.xml")`` creates ``out/ufs``.
    """
    dir = os.path.dirname(filename)
    try:
        os.stat(dir)
    except OSError:
        os.makedirs(dir)


def PrintBigWarning(sz, log_func=print):
    """Print an ASCII-art "warning" banner followed by a message.

    Args:
        sz (str): Message printed after the banner; nothing is printed when empty.
        log_func (Callable[[str], object]): Function that writes each line; defaults to ``print``.

    Example:
        ``PrintBigWarning("Partition table is larger than the disk")``
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
    """Print an ASCII-art "error" banner and, when a message is given, exit.

    Args:
        sz (str): Message printed after the banner; when non-empty the process
            exits with status 1 after printing it.
        log_func (Callable[[str], object]): Function that writes each line; defaults to ``print``.

    Raises:
        SystemExit: ``sz`` is not empty.

    Example:
        ``PrintBigError("Unknown partition type")`` prints the banner and exits with status 1.
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
    """Reverse the order of the low ``nBits`` bits of an integer.

    Args:
        data (int): Value whose bits are reflected.
        nBits (int): Number of low-order bits to reflect.

    Returns:
        int: The reflected value.

    Example:
        ``reflect(0x01, 8)`` returns ``0x80``.
    """
    reflection = 0x00000000
    for bit in range(nBits):
        if data & 0x01:
            reflection |= 1 << ((nBits - 1) - bit)
        data = data >> 1
    return reflection


def CalcCRC32(array, Len):
    """Compute the IEEE 802.3 CRC-32 of the first bytes of an array, as used in GPT headers.

    Args:
        array (bytes | list[int]): Bytes to checksum.
        Len (int): Number of leading bytes of ``array`` to include.

    Returns:
        int: The 32-bit CRC.

    Example:
        ``CalcCRC32(b"123456789", 9)`` returns ``0xCBF43926``.
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
