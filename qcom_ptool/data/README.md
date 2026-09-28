# Package data

Data files that `gen_udev_rules` reads; the [configuration reference](../../docs/source/user/CONFIGURATION.md#data-files) describes their formats.

## Files

- [55-qcom-raw-partitions-noblkid.rules.in](55-qcom-raw-partitions-noblkid.rules.in) — Is the udev rules template for raw partitions.
- [`__init__.py`](__init__.py) — Makes the folder a package so the files can be installed with it.
- [filesystem-partition-names.list](filesystem-partition-names.list) — Lists the partition names that hold filesystems.
- [README.md](README.md) — Describes this folder and indexes its contents.
