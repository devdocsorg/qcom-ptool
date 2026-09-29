# Schemas

JSON Schemas that the YAML loader and the board resolver apply; the package
installs them with the code. Their `description` fields explain each key.

## Files

- [README.md](README.md) — Describes this folder and indexes its contents.
- [\_\_init\_\_.py](__init__.py) — Makes the folder a package so the schemas install as package data.
- [board.schema.json](board.schema.json) — Validates board files, derived boards, and variant overlays.
- [include.schema.json](include.schema.json) — Validates shared partition fragments pulled in with `includes:`.
- [partitions.schema.json](partitions.schema.json) — Validates a single-storage YAML layout and each fully resolved board storage.
