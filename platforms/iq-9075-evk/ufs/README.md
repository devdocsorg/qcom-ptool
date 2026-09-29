# iq-9075-evk UFS layout

`make all` generates this storage's partition tables and flashing files here from the files below.

## Files

- [README.md](README.md) — Describes this folder and indexes its contents.
- [contents.xml.in](contents.xml.in) — Provides the `contents.xml` template that `gen_contents` completes with the partition, GPT, rawprogram, and patch file names.
- [partitions.conf](partitions.conf) — Lists the disk options and partitions that `gen_partition` turns into `partitions.xml`.
