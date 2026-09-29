# Configuration reference

qcom-ptool reads partition layouts, board files, command-line options, and three
environment or make variables. Nothing loads a `.env` file:
[.env.example](https://github.com/devdocsorg/qcom-ptool/blob/docs/repository-documentation/.env.example)
lists the variables to export.

## Environment and make variables

| Name | Purpose | Type and default | Safe example |
| --- | --- | --- | --- |
| `PTOOL_SEED` | Seeds the random disk and partition GUIDs that `ptool` writes, so repeated builds produce identical files. CI and the checksum manifest use `qcom-ptool-ci`. | String; unset gives new random GUIDs each run. | `qcom-ptool-ci` |
| `QCOM_PTOOL` | Command that the root Makefile's rules run. The GPT rule runs it from each layout folder, so give an absolute path. | Command; default `qcom-ptool` on `PATH`. | `/usr/local/bin/qcom-ptool` |
| `BUILD_ID` | Build identifier that the root Makefile passes to `gen_contents -b`, which writes it to every `<build_id>` element of `contents.xml`. | String; unset leaves the elements empty. | `0001` |

A make variable given on the command line, such as `make all BUILD_ID=0001`,
overrides the environment.

## Partition layouts

Each `platforms/<board>/<storage>/partitions.conf` describes one storage device:
lines starting with `#` are comments, one `--disk` line sets the device options,
and each `--partition` line adds a partition in table order. `gen_partition -i`
also reads a single-storage YAML file, and board files use the same fields; the
YAML key is given where it differs. [partitions.schema.json](https://github.com/devdocsorg/qcom-ptool/blob/docs/repository-documentation/qcom_ptool/schema/partitions.schema.json)
defines the YAML form. Each board's values are its layout choices, and the
comments at the top of each file list the required options.

| Disk option (YAML key) | Purpose | Type and default | Example |
| --- | --- | --- | --- |
| `--type` | Storage class. `emmc`, `nvme`, `spinor`, and `ufs` produce XML; `nand` is accepted but produces none. | String; required. | `--type=ufs` |
| `--size` | Device size in bytes; not written to `partitions.xml`. | Integer; required in YAML, optional in `.conf`. | `--size=137438953472` |
| `--sector-size-in-bytes` (`sector-size`) | Sector size in bytes. | Integer; default 512. | `--sector-size-in-bytes=4096` |
| `--write-protect-boundary` | Write-protect boundary in KB. | Integer; default 65536. | `--write-protect-boundary=0` |
| `--grow-last-partition` | Grows the last partition to fill the device. | Flag in `.conf`, boolean in YAML; default off. | `--grow-last-partition` |
| `--align-partitions` | Performance alignment boundary in bytes, written to the XML in KB. | Integer; default alignment on at 4 KB. | `--align-partitions=4096` |

| Partition option (YAML key) | Purpose | Type and default | Example |
| --- | --- | --- | --- |
| `--lun` or `--phys-part` | Physical partition (UFS LUN) that holds the partition. | Integer; default 0. | `--lun=1` |
| `--name` | GPT partition name. | String; required. | `--name=efi` |
| `--size` | Partition size: bytes, or a number with a `K`, `M`, or `G` suffix and optional `B`. | String; required. | `--size=524288KB` |
| `--type-guid` | Partition type GUID. | GUID; required in YAML, default all zeros in `.conf`. | `--type-guid=C12A7328-F81F-11D2-BA4B-00A0C93EC93B` |
| `--filename` | Image that the rawprogram XML programs into the partition. `gen_partition -m name=image,...` overrides it by name. | String; default empty, programming nothing. | `--filename=efi.bin` |
| `--attributes` | GPT attribute bits in hexadecimal; bit 2 sets bootable and bit 60 read-only. | Hex string; unset. | `--attributes=1000000000000004` |
| `--bootable`, `--readonly` | Legacy BIOS bootable flag (bit 2) and read-only flag (bit 60); they override `--attributes`. | Boolean; defaults false and true. | `--readonly=false` |
| `--priority`, `--tries-remaining` | A/B slot priority (0 to 3) and retry count (0 to 7). | Integer; unset. | `--priority=3` |
| `--active`, `--successful`, `--unbootable` | A/B slot flags. | Boolean; default false. | `--active=true` |
| `--sparse` | Marks the image as a sparse image. | Boolean; default false. | `--sparse=true` |
| `--uniqueguid` (`unique-guid`) | Fixed unique partition GUID. | GUID; unset gives a random GUID. | `--uniqueguid=6A2E1C38-A1B6-4B0F-9F2B-1E3C5D7F9A0B` |

In `.conf` files, `true`, `yes`, `y`, and `1` mean true for a boolean, and any
other value means false. YAML uses `true` and `false`.

## Board files

A board file under `platforms/boards/` describes all storage devices of a board;
the root Makefile builds each storage into `platforms/<board>/<id>/`.
[board.schema.json](https://github.com/devdocsorg/qcom-ptool/blob/docs/repository-documentation/qcom_ptool/schema/board.schema.json)
validates it, and each resolved storage must then satisfy `partitions.schema.json`.

| Key | Purpose | Type and default | Example |
| --- | --- | --- | --- |
| `platform.name` | Board name. | String; optional. | `glymur-crd` |
| `extends` | Base board to inherit, relative to `platforms/`; storages merge by `id` and partitions by `name`. | String; optional. | `boards/glymur-crd.yaml` |
| `storage[].id` | Storage identifier and output folder name. | String; required. | `nvme` |
| `storage[].includes` | Shared partition fragments, relative to `platforms/`, added before the storage's own partitions; [include.schema.json](https://github.com/devdocsorg/qcom-ptool/blob/docs/repository-documentation/qcom_ptool/schema/include.schema.json) validates them. | List of paths; optional. | `[_common/boot.yaml]` |
| `storage[]` disk keys and `partitions` | Device options and partition list, as in the tables above. | As above. | `sector-size: 4096` |

`gen_partition --board` and `show --board` accept `--hlos <name>` and
`--boot-fw <name>`, which apply the overlays
`platforms/variants/hlos/<name>.yaml` and `platforms/variants/boot-fw/<name>.yaml`
last, and `--root <dir>`, which sets the folder these paths resolve against
(default: the folder above `boards/`, or the board file's own folder elsewhere).
The repository has no fragments or overlays yet.

## Contents templates

`contents.xml.in` is a board's `contents.xml` template. `gen_contents` adds a
`<build_id>` to every build and, in the `common` build, replaces the
`download_file`, `partition_file`, and `partition_patch_file` entries with one
entry per partition image, GPT image, rawprogram file, and patch file. The storage
type comes from the `chipid` element whose `flavor` is `default`.

## udev rules

`gen_udev_rules -o <file>` fills the placeholder in
[55-qcom-raw-partitions-noblkid.rules.in](https://github.com/devdocsorg/qcom-ptool/blob/docs/repository-documentation/qcom_ptool/data/55-qcom-raw-partitions-noblkid.rules.in)
with a rule for each partition name in the layouts, except the names in
[filesystem-partition-names.list](https://github.com/devdocsorg/qcom-ptool/blob/docs/repository-documentation/qcom_ptool/data/filesystem-partition-names.list).
Both files explain their lines in comments. Repeated `-i <layout>` options replace
the default, which reads every `platforms/*/*/partitions.conf`.

## Project files

[pyproject.toml](https://github.com/devdocsorg/qcom-ptool/blob/docs/repository-documentation/pyproject.toml)
follows the [pyproject specification](https://packaging.python.org/en/latest/specifications/pyproject-toml/);
its tool tables use the [setuptools](https://setuptools.pypa.io/en/latest/userguide/pyproject_config.html),
[ruff](https://docs.astral.sh/ruff/settings/), [mypy](https://mypy.readthedocs.io/en/stable/config_file.html),
and [pytest](https://docs.pytest.org/en/stable/reference/reference.html#ini-options-ref) settings.

| Setting | Value and purpose |
| --- | --- |
| `[build-system]` | Builds with `setuptools>=64` through `setuptools.build_meta`. |
| `[project]` metadata | Package `qcom-ptool`, version `1.0.0`, its description, `README.md` as the long description, and the `BSD-3-Clause` licence in `LICENSE`. |
| `requires-python`, `dependencies` | Python 3.8 or newer; `PyYAML>=5.1` and `jsonschema>=3.2` load and validate YAML layouts. |
| `optional-dependencies.test` | `pytest`, installed with `pip install .[test]`. |
| `project.scripts` | Installs the `qcom-ptool` command from `qcom_ptool.cli:main`. |
| `[tool.setuptools]` tables | Packages `qcom_ptool` and its subpackages, with the schema `*.json` and data `*.in` and `*.list` files. |
| `[tool.ruff]`, `[tool.ruff.lint]`, `[tool.ruff.lint.isort]` | Lints for Python 3.8 at 120 columns with the listed rule sets; inline comments explain each rule set and ignored rule; `qcom_ptool` sorts as first-party. |
| `[tool.mypy]` and its override | Type-checks for Python 3.9, warns on `Any` returns, allows functions without annotations but checks their bodies except in the legacy `msp` and `ptool` modules, skips unused-section warnings, and ignores missing third-party stubs. |
| `[tool.pytest.ini_options]` | Runs `tests/unit` from the repository root without an installed package; its comment explains why. |

[degpt/Cargo.toml](https://github.com/devdocsorg/qcom-ptool/blob/docs/repository-documentation/degpt/Cargo.toml)
declares the `degpt` crate, version 0.1.0 on the 2021 edition, with the `gpt` 3.1
and `uuid` 1.8 dependencies; `Cargo.lock` pins their resolved versions.

## Continuous integration

- [build.yml](https://github.com/devdocsorg/qcom-ptool/blob/docs/repository-documentation/.github/workflows/build.yml) runs on every pull request and on pushes to `main`: it lints, runs the unit tests, builds every platform with `PTOOL_SEED=qcom-ptool-ci`, checks the generated files and the checksum manifest, and builds degpt.
- [quic-organization-repolinter.yml](https://github.com/devdocsorg/qcom-ptool/blob/docs/repository-documentation/.github/workflows/quic-organization-repolinter.yml) runs on every push and pull request and checks the repository's required files and licence headers against a local `repolint.json` or, without one, the quic organisation's ruleset.
- [documentation.yml](https://github.com/devdocsorg/qcom-ptool/blob/docs/repository-documentation/.github/workflows/documentation.yml) runs on every pull request and on pushes to `main`, and runs the documentation `setup` and `check` targets.

## Repository files

[CODEOWNERS](https://github.com/devdocsorg/qcom-ptool/blob/docs/repository-documentation/.github/CODEOWNERS)
explains its default reviewers in a comment. The root
[.gitignore](https://github.com/devdocsorg/qcom-ptool/blob/docs/repository-documentation/.gitignore)
ignores generated `.xml` and `.bin` files under `platforms/`, Python caches and
environments, packaging output, and the documentation build; `degpt/.gitignore`
ignores Cargo's `target/` folder.
