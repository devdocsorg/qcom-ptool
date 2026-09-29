# Package data

Files that `gen_udev_rules` reads; the package installs them with the code.

## Files

- [README.md](README.md) — Describes this folder and indexes its contents.
- [\_\_init\_\_.py](__init__.py) — Makes the folder a package so its files install as package data.
- [55-qcom-raw-partitions-noblkid.rules.in](55-qcom-raw-partitions-noblkid.rules.in) — Provides the udev rules template whose placeholder receives one rule per raw partition name.
- [filesystem-partition-names.list](filesystem-partition-names.list) — Lists the partition names that hold filesystems and so keep normal probing.
