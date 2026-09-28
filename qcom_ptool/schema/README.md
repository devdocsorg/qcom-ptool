# Layout schemas

JSON schemas that validate YAML layouts; they are installed with the package.

## Files

- [`__init__.py`](__init__.py) — Makes the folder a package so the schemas can be installed with it.
- [board.schema.json](board.schema.json) — Validates board files, derived boards, and variant overlays.
- [include.schema.json](include.schema.json) — Validates shared partition lists pulled in with `includes`.
- [partitions.schema.json](partitions.schema.json) — Validates a fully resolved single-storage layout.
- [README.md](README.md) — Describes this folder and indexes its contents.
