# Tests

`make unit-test` runs the pytest suite, and `make integration` and
`make check-checksums` build every platform and check the generated files. The
[development setup](../docs/source/contributing/DEVELOPMENT.md) explains when to
run them.

## Folders

- [integration/](integration/README.md) — Holds the scripts and checksum manifest that check the files `make all` generates.
- [unit/](unit/README.md) — Holds the pytest unit tests for the `qcom_ptool` package.

## Files

- [README.md](README.md) — Describes this folder and indexes its contents.
