# qcom_ptool

The Python package behind the `qcom-ptool` command. The [function reference](../docs/source/contributing/README.md#function-reference) is generated from its docstrings.

## Folders

- [data/](data/README.md) — Holds the udev rules template and the list of filesystem partition names.
- [loaders/](loaders/README.md) — Reads `.conf` and YAML layouts into one internal form.
- [schema/](schema/README.md) — Holds the JSON schemas for YAML layouts and board files.

## Files

- [`__init__.py`](__init__.py) — Defines the package version.
- [board.py](board.py) — Resolves YAML board files with their bases, includes, and variants.
- [cli.py](cli.py) — Implements the `qcom-ptool` command and dispatches its subcommands.
- [gen_contents.py](gen_contents.py) — Implements `gen_contents`, which writes `contents.xml` from a template.
- [gen_partition.py](gen_partition.py) — Implements `gen_partition`, which writes the partition XML from a layout or board.
- [gen_udev_rules.py](gen_udev_rules.py) — Implements `gen_udev_rules`, which writes udev rules for raw partitions.
- [msp.py](msp.py) — Implements `msp`, which programs the images in rawprogram and patch files onto a mass storage device.
- [ptool.py](ptool.py) — Implements `ptool`, which writes GPT images and rawprogram and patch files from partition XML.
- [README.md](README.md) — Describes this folder and indexes its contents.
- [show.py](show.py) — Implements `show`, which prints a board's resolved layout.
- [spec.py](spec.py) — Defines the internal layout form and its defaults.
- [utils.py](utils.py) — Provides CRC-32, directory, and banner helpers.
