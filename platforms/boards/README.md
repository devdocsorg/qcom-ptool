# Board files

Each YAML file describes one board and all of its storage devices. The root
Makefile builds every storage it declares into `platforms/<board>/<storage id>/`,
and skips any `partitions.conf` at those paths.

## Files

- [README.md](README.md) — Describes this folder and indexes its contents.
- [glymur-crd.yaml](glymur-crd.yaml) — Defines the glymur-crd board's NVMe and SPI-NOR partition tables.
