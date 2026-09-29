# Unit tests

pytest runs these from the repository root with `make unit-test`; the
`[tool.pytest.ini_options]` table in [pyproject.toml](../../pyproject.toml) sets the
path and test folder.

## Folders

- [data/](data/README.md) — Holds the matching `.conf` and YAML fixtures for the format-parity tests.

## Files

- [README.md](README.md) — Describes this folder and indexes its contents.
- [\_\_init\_\_.py](__init__.py) — Makes the folder a package for pytest's module naming.
- [test_board.py](test_board.py) — Tests board-file composition: `extends`, `includes`, variant overlays, and validation.
- [test_cli.py](test_cli.py) — Tests the `qcom-ptool` command's version, help, and subcommand dispatch.
- [test_cli_board.py](test_cli_board.py) — Tests board mode of `gen_partition` and the `show` subcommand.
- [test_gen_partition.py](test_gen_partition.py) — Tests the `partitions.xml` that `gen_partition` writes.
- [test_gen_udev_rules.py](test_gen_udev_rules.py) — Tests the rules and errors of `gen_udev_rules`.
- [test_loaders_conf.py](test_loaders_conf.py) — Tests the `.conf` loader's size, option, and line parsing.
- [test_loaders_yaml.py](test_loaders_yaml.py) — Tests that YAML layouts load and emit the same result as the matching `.conf` files.
- [test_utils.py](test_utils.py) — Tests the CRC32, bit-reflection, and directory helpers.
