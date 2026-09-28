# Integration checks

Scripts that `make integration` and `make check-checksums` run on the generated platform files.

## Files

- [check-checksums](check-checksums) — Compares the generated files with the checksum manifest.
- [check-missing-files](check-missing-files) — Reports files named in generated XML that ptool should have written but did not, and unknown names.
- [checksums.sha256](checksums.sha256) — Lists the expected checksums of the generated files, built with `PTOOL_SEED=qcom-ptool-ci`.
- [README.md](README.md) — Describes this folder and indexes its contents.
