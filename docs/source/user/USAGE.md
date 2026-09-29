# Generate a board's partition files

This tutorial installs qcom-ptool and generates the partition tables and flashing
files for one board: the UFS storage of `qcs6490-rb3gen2`.

## Prerequisites

- A checkout of this repository, which provides the layouts under `platforms/`.
- Python 3.8 or newer with the `venv` module.

## 1. Install the tool

From the repository root:

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install .
qcom-ptool --version
```

The last command prints `qcom-ptool 1.0.0`.

## 2. Write the partition table description

```sh
mkdir -p build/tutorial
qcom-ptool gen_partition -i platforms/qcs6490-rb3gen2/ufs/partitions.conf -o build/tutorial/partitions.xml
```

It prints `Generating UFS XML build/tutorial/partitions.xml`. The file lists the partitions
of each UFS LUN.

## 3. Generate the GPT images and flashing files

```sh
cd build/tutorial
qcom-ptool ptool -x partitions.xml
```

For each LUN `N` (0 to 5 for this board), `ptool` writes the GPT images
`gpt_mainN.bin`, `gpt_backupN.bin`, `gpt_bothN.bin`, and `gpt_emptyN.bin`, the
flashing files `rawprogramN.xml` and `patchN.xml`, and the erase files
`rawprogramN_BLANK_GPT.xml`, `rawprogramN_WIPE_PARTITIONS.xml`, and
`wipe_rawprogram_PHY*.xml`, plus `zeros_*.bin` fill images. Each run uses new
random disk GUIDs unless `PTOOL_SEED` is set.

## 4. Complete the contents file

```sh
qcom-ptool gen_contents -p partitions.xml -t ../../platforms/qcs6490-rb3gen2/ufs/contents.xml.in -o contents.xml
```

It prints the storage type, the partition images, and the build names, then
writes `contents.xml`, which lists every partition image, GPT image, rawprogram
file, and patch file for flashing tools.

## Expected result

`build/tutorial/`, which Git ignores, holds `partitions.xml`, `contents.xml`, and the GPT, rawprogram, patch, and
zero-fill files above. Flashing them with the board's boot images is outside this
repository. To generate every board in place under `platforms/`, run `make all`
from the repository root; the
[configuration reference](CONFIGURATION.md) explains the layout files and settings.
