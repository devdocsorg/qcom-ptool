# degpt source

The `degpt` program and the library it parses GPT images with.

## Folders

- [mygpt/](mygpt/README.md) — Parses GPT headers and partition entries.

## Files

- [README.md](README.md) — Describes this folder and indexes its contents.
- [lib.rs](lib.rs) — Exposes the `mygpt` module as the crate's library.
- [main.rs](main.rs) — Reads GPT images and writes the partition XML file.
- [mygpt.rs](mygpt.rs) — Declares the `header` and `partition` modules and re-exports their types.
