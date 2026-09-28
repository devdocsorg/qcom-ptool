# Generate partition files for a board

This tutorial turns the RB3 Gen 2 UFS layout into GPT images, the rawprogram and
patch files that flashing tools read, and a `contents.xml` build description.

## Prerequisites

- A checkout of this repository, which supplies the layouts under
  [platforms/](https://github.com/devdocsorg/qcom-ptool/tree/docs/repository-documentation/platforms).
- qcom-ptool installed as described under [Installation](https://github.com/devdocsorg/qcom-ptool/blob/docs/repository-documentation/README.md#installation);
  `qcom-ptool -V` prints its version.

## 1. Choose a layout and an output folder

Each `platforms/<board>/<storage>/` folder holds one storage layout. This tutorial
uses [platforms/qcs6490-rb3gen2/ufs](https://github.com/devdocsorg/qcom-ptool/tree/docs/repository-documentation/platforms/qcs6490-rb3gen2/ufs). From the
checkout root:

```sh
PTOOL_DIR=$PWD
mkdir -p ~/rb3gen2-ufs && cd ~/rb3gen2-ufs
```

## 2. Generate the partition XML

```sh
qcom-ptool gen_partition -i "$PTOOL_DIR/platforms/qcs6490-rb3gen2/ufs/partitions.conf" -o partitions.xml
```

The command prints `Generating UFS XML partitions.xml` and writes one
`physical_partition` element per UFS LUN.

## 3. Generate the GPT images and flashing XML

```sh
qcom-ptool ptool -x partitions.xml
```

For each LUN `N`, ptool writes `gpt_mainN.bin`, `gpt_backupN.bin`,
`gpt_bothN.bin`, `gpt_emptyN.bin`, `rawprogramN.xml`, `patchN.xml`,
`rawprogramN_BLANK_GPT.xml` and `rawprogramN_WIPE_PARTITIONS.xml`. It also writes
`wipe_rawprogram_PHY*.xml` and the `zeros_*.bin` files they use, and ends with
`NOTE: All Physical Partitions / LUNs were created`. Disk and partition GUIDs are
random unless `PTOOL_SEED` is set.

## 4. Generate contents.xml

```sh
qcom-ptool gen_contents -p partitions.xml -t "$PTOOL_DIR/platforms/qcs6490-rb3gen2/ufs/contents.xml.in" -o contents.xml
```

Add `-b <build-id>` to record a build ID. `contents.xml` lists each partition
image, GPT file, rawprogram file, and patch file for the `common` build.

## Expected result

`~/rb3gen2-ufs` holds `partitions.xml`, `contents.xml`, and the files from step 3.
A flashing tool reads `rawprogramN.xml` and `patchN.xml` together with the images
they name; flashing a board is outside this tutorial.

Boards under `platforms/boards/` are YAML files that describe every storage at
once; generate them with `qcom-ptool gen_partition --board <file> -C <folder>`. To
build every layout inside the checkout, run `make all`.
