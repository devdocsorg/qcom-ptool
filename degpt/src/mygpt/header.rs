// SPDX-License-Identifier: MIT
// Copyright (c) 2017 Quyzi
// Copyright (c) 2024 Linaro Ltd.

use std::error::Error;
use std::fmt;
use std::io::Cursor;

use gpt::header::parse_uuid;

/// Header describing a GPT disk.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct Header {
    /// GPT header magic signature, hardcoded to "EFI PART".
    pub signature: String, // Offset  0. "EFI PART", 45h 46h 49h 20h 50h 41h 52h 54h
    /// 00 00 01 00
    pub revision: u32, // Offset  8
    /// little endian
    pub header_size_le: u32, // Offset 12
    /// CRC32 of the header with crc32 section zeroed
    pub crc32: u32, // Offset 16
    /// must be 0
    pub reserved: u32, // Offset 20
    /// For main header, 1
    pub current_lba: u64, // Offset 24
    /// LBA for backup header
    pub backup_lba: u64, // Offset 32
    /// First usable LBA for partitions (primary table last LBA + 1)
    pub first_usable: u64, // Offset 40
    /// Last usable LBA (secondary partition table first LBA - 1)
    pub last_usable: u64, // Offset 48
    /// UUID of the disk
    pub disk_guid: uuid::Uuid, // Offset 56
    /// Starting LBA of partition entries
    pub part_start: u64, // Offset 72
    /// Number of partition entries
    pub num_parts: u32, // Offset 80
    /// Size of a partition entry, usually 128
    pub part_size: u32, // Offset 84
    /// CRC32 of the partition table
    pub crc32_parts: u32, // Offset 88
}

impl fmt::Display for Header {
    /// Write the disk GUID and the header and partition-table CRC32 values.
    ///
    /// # Arguments
    ///
    /// * `f` - Formatter that receives the three tab-separated lines.
    ///
    /// # Returns
    ///
    /// `Ok` when the text was written, or the formatter's error.
    ///
    /// # Examples
    ///
    /// ```
    /// use degpt::mygpt::Header;
    ///
    /// let header = Header::try_from(&[0u8; 92][..]).unwrap();
    /// assert!(header.to_string().starts_with("Disk:"));
    /// ```
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            f,
            "Disk:\t\t{}\nCRC32:\t\t{}\nTable CRC:\t{}",
            self.disk_guid, self.crc32, self.crc32_parts
        )
    }
}

impl TryFrom<&[u8]> for Header {
    type Error = Box<dyn Error>;

    /// Parse a GPT header from its little-endian on-disk bytes.
    ///
    /// # Arguments
    ///
    /// * `buf` - Header bytes, starting at the "EFI PART" signature; at least 92 bytes.
    ///
    /// # Errors
    ///
    /// Returns an error when the signature is not UTF-8 or the disk GUID cannot be
    /// read. A buffer shorter than 92 bytes panics.
    ///
    /// # Examples
    ///
    /// ```
    /// use degpt::mygpt::Header;
    ///
    /// let mut bytes = [0u8; 92];
    /// bytes[..8].copy_from_slice(b"EFI PART");
    /// bytes[80..84].copy_from_slice(&128u32.to_le_bytes());
    /// let header = Header::try_from(&bytes[..]).unwrap();
    /// assert_eq!(header.signature, "EFI PART");
    /// assert_eq!(header.num_parts, 128);
    /// ```
    fn try_from(buf: &[u8]) -> Result<Self, Self::Error> {
        Ok(Header {
            signature: String::from_utf8(buf[0..8].into())?,
            revision: u32::from_le_bytes(buf[8..12].try_into()?),
            header_size_le: u32::from_le_bytes(buf[12..16].try_into()?),
            crc32: u32::from_le_bytes(buf[16..20].try_into()?),
            reserved: u32::from_le_bytes(buf[20..24].try_into()?),
            current_lba: u64::from_le_bytes(buf[24..32].try_into()?),
            backup_lba: u64::from_le_bytes(buf[32..40].try_into()?),
            first_usable: u64::from_le_bytes(buf[40..48].try_into()?),
            last_usable: u64::from_le_bytes(buf[48..56].try_into()?),
            disk_guid: parse_uuid(&mut Cursor::new(&buf[56..72]))?,
            part_start: u64::from_le_bytes(buf[72..80].try_into()?),
            num_parts: u32::from_le_bytes(buf[80..84].try_into()?),
            part_size: u32::from_le_bytes(buf[84..88].try_into()?),
            crc32_parts: u32::from_le_bytes(buf[88..92].try_into()?),
        })
    }
}
