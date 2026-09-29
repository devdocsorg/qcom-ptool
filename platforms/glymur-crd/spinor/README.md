# glymur-crd SPI-NOR layout

`make all` generates this storage's partition tables and flashing files here from [glymur-crd.yaml](../../boards/glymur-crd.yaml) and the template below.

## Files

- [README.md](README.md) — Describes this folder and indexes its contents.
- [contents.xml.in](contents.xml.in) — Provides the `contents.xml` template that `gen_contents` completes with the partition, GPT, rawprogram, and patch file names.
