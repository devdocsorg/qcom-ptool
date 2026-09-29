# qcom_ptool package

The Python package installed by `pip install .`. [cli.py](cli.py) provides the
`qcom-ptool` command and runs each subcommand's module as a script. The
[function reference](../docs/source/contributing/README.md#function-reference)
documents every function.

## Folders

- [data/](data/README.md) — Holds the udev rule template and the list of filesystem partition names that `gen_udev_rules` reads.
- [loaders/](loaders/README.md) — Reads `.conf` and single-storage YAML partition layouts into one internal form.
- [schema/](schema/README.md) — Holds the JSON Schemas that validate YAML layouts, board files, and shared fragments.

## Files

- [README.md](README.md) — Describes this folder and indexes its contents.
- [\_\_init\_\_.py](__init__.py) — Marks the package and sets its version.
- [board.py](board.py) — Resolves YAML board files, with their base boards, fragments, and variant overlays, into per-storage layouts.
- [cli.py](cli.py) — Implements the `qcom-ptool` command and dispatches to the subcommands.
- [gen_contents.py](gen_contents.py) — Implements `gen_contents`, which completes a `contents.xml` template from a `partitions.xml` file.
- [gen_partition.py](gen_partition.py) — Implements `gen_partition`, which writes `partitions.xml` from a layout or board file.
- [gen_udev_rules.py](gen_udev_rules.py) — Implements `gen_udev_rules`, which writes udev rules that skip filesystem probing on raw partitions.
- [msp.py](msp.py) — Implements `msp`, which programs rawprogram and patch files onto a storage device or into an image file.
- [ptool.py](ptool.py) — Implements `ptool`, which writes the GPT images and rawprogram, patch, and wipe XML files from `partitions.xml`.
- [show.py](show.py) — Implements `show`, which prints a board file's fully resolved layout as YAML.
- [spec.py](spec.py) — Defines the internal layout form and the default disk and partition values that every loader shares.
- [utils.py](utils.py) — Provides the CRC32, directory, and warning helpers that `ptool` and `msp` share.
