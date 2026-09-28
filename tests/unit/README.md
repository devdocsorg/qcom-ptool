# Unit tests

The pytest suite that `make unit-test` runs. The [function reference](../../docs/source/contributing/README.md#function-reference) lists each test.

## Folders

- [data/](data/README.md) — Holds layout fixtures.

## Files

- [`__init__.py`](__init__.py) — Makes the tests a package.
- [README.md](README.md) — Describes this folder and indexes its contents.
- [test_board.py](test_board.py) — Tests the board resolver.
- [test_cli.py](test_cli.py) — Tests the `qcom-ptool` command dispatcher.
- [test_cli_board.py](test_cli_board.py) — Tests board mode of `gen_partition` and the `show` subcommand.
- [test_gen_partition.py](test_gen_partition.py) — Tests `gen_partition`.
- [test_gen_udev_rules.py](test_gen_udev_rules.py) — Tests `gen_udev_rules`.
- [test_loaders_conf.py](test_loaders_conf.py) — Tests the `.conf` loader.
- [test_loaders_yaml.py](test_loaders_yaml.py) — Tests the YAML loader.
- [test_utils.py](test_utils.py) — Tests the CRC-32 and directory helpers.
