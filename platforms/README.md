# Platforms

Partition layouts for each supported board, one folder per board and storage
device. `make all` builds every layout in place: `gen_partition` turns each
`partitions.conf`, or each storage of a [board file](boards/README.md), into
`partitions.xml`; `ptool` writes the GPT images and flashing XML files beside it;
and `gen_contents` completes each `contents.xml.in` template. Git ignores the
generated `.xml` and `.bin` files. The
[configuration reference](../docs/source/user/CONFIGURATION.md) describes the file
formats.

## Folders

- [boards/](boards/README.md) — Holds YAML board files that describe every storage device of a board in one file.
- [apq8016-sbc/](apq8016-sbc/README.md) — Holds the eMMC layout for the apq8016-sbc board.
- [apq8096-db820c/](apq8096-db820c/README.md) — Holds the UFS layout for the apq8096-db820c board.
- [eliza-evk/](eliza-evk/README.md) — Holds the eMMC layout for the eliza-evk board.
- [glymur-crd/](glymur-crd/README.md) — Receives the generated files for the glymur-crd board file and holds its SPI-NOR contents template.
- [iq-615-evk/](iq-615-evk/README.md) — Holds the eMMC and UFS layouts for the iq-615-evk board.
- [iq-8275-evk/](iq-8275-evk/README.md) — Holds the eMMC and UFS layouts for the iq-8275-evk board.
- [iq-9075-evk/](iq-9075-evk/README.md) — Holds the eMMC and UFS layouts for the iq-9075-evk board.
- [iq-x7181-evk/](iq-x7181-evk/README.md) — Holds the NVMe, SPI-NOR, and UFS layouts for the iq-x7181-evk board.
- [kaanapali-mtp/](kaanapali-mtp/README.md) — Holds the UFS layout for the kaanapali-mtp board.
- [nord-rrd/](nord-rrd/README.md) — Holds the SPI-NOR and UFS layouts for the nord-rrd board.
- [qcm6490-idp/](qcm6490-idp/README.md) — Holds the eMMC and UFS layouts for the qcm6490-idp board.
- [qcs615-ride/](qcs615-ride/README.md) — Holds the eMMC and UFS layouts for the qcs615-ride board.
- [qcs6490-rb3gen2/](qcs6490-rb3gen2/README.md) — Holds the UFS layout for the qcs6490-rb3gen2 board.
- [qcs6490-thundercomm-rubikpi3/](qcs6490-thundercomm-rubikpi3/README.md) — Holds the UFS layout for the qcs6490-thundercomm-rubikpi3 board.
- [qcs8275-monza/](qcs8275-monza/README.md) — Holds the eMMC layout for the qcs8275-monza board.
- [qcs8300-ride-sx/](qcs8300-ride-sx/README.md) — Holds the UFS layout for the qcs8300-ride-sx board.
- [qcs9100-ride-sx/](qcs9100-ride-sx/README.md) — Holds the UFS layout for the qcs9100-ride-sx board.
- [qrb2210-rb1/](qrb2210-rb1/README.md) — Holds the eMMC layout for the qrb2210-rb1 board.
- [qrb2210-rb1-abl/](qrb2210-rb1-abl/README.md) — Holds the eMMC layout for the qrb2210-rb1-abl board.
- [qrb2210-unoq/](qrb2210-unoq/README.md) — Holds the 16 GB eMMC and 16 GB eMMC (Arduino) layouts for the qrb2210-unoq board.
- [qrb2210-unoq-abl/](qrb2210-unoq-abl/README.md) — Holds the 16 GB eMMC and 16 GB eMMC (Arduino) layouts for the qrb2210-unoq-abl board.
- [qrb4210-rb2/](qrb4210-rb2/README.md) — Holds the eMMC layout for the qrb4210-rb2 board.
- [qrb5165-rb5/](qrb5165-rb5/README.md) — Holds the UFS layout for the qrb5165-rb5 board.
- [sdm845-db845c/](sdm845-db845c/README.md) — Holds the UFS layout for the sdm845-db845c board.
- [shikra-evk/](shikra-evk/README.md) — Holds the eMMC layout for the shikra-evk board.
- [sm8750-mtp/](sm8750-mtp/README.md) — Holds the UFS layout for the sm8750-mtp board.

## Files

- [README.md](README.md) — Describes this folder and indexes its contents.
