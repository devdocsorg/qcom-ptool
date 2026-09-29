# Integration checks

Scripts that the root Makefile runs against the files `make all` writes under
`platforms/`.

## Files

- [README.md](README.md) — Describes this folder and indexes its contents.
- [check-checksums](check-checksums) — Compares the generated files with the checksum manifest; `make check-checksums` runs it.
- [check-missing-files](check-missing-files) — Reports GPT, zero-fill, rawprogram, and patch files that generated XML names but that are missing, and file names it does not recognise; `make integration` runs it.
- [checksums.sha256](checksums.sha256) — Records the SHA-256 of every generated file for `PTOOL_SEED=qcom-ptool-ci`; `make generate-checksums` rewrites it.
