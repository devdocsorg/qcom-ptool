# qrb2210-unoq 16 GB eMMC storage

Layout for the 16 GB eMMC storage of the `qrb2210-unoq` board. `make` writes the generated files next to it, and Git ignores them. It adds a `userdata` partition to the `emmc-16GB` layout. The [configuration reference](../../../docs/source/user/CONFIGURATION.md) describes the formats.

## Files

- [contents.xml.in](contents.xml.in) — Is the template that `gen_contents` turns into `contents.xml`.
- [partitions.conf](partitions.conf) — Defines the disk and its partitions in the `.conf` layout format.
- [README.md](README.md) — Describes this folder and indexes its contents.
