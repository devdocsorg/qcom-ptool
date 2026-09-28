# kaanapali-mtp UFS storage

Layout for the UFS storage of the `kaanapali-mtp` board. `make` writes the generated files next to it, and Git ignores them. The [configuration reference](../../../docs/source/user/CONFIGURATION.md) describes the formats.

## Files

- [contents.xml.in](contents.xml.in) — Is the template that `gen_contents` turns into `contents.xml`.
- [partitions.conf](partitions.conf) — Defines the disk and its partitions in the `.conf` layout format.
- [README.md](README.md) — Describes this folder and indexes its contents.
