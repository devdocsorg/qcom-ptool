# degpt

A Rust tool that writes a partition XML describing the partitions in existing GPT images with 4096-byte sectors. Build it with `cargo build` and run `target/debug/degpt partition.xml gpt_both0.bin`. The [function reference](../docs/source/contributing/README.md#function-reference) is generated from its doc comments.

## Folders

- [src/](src/README.md) — Holds the tool's source.

## Files

- [.gitignore](.gitignore) — Keeps the Cargo build output out of Git.
- [Cargo.lock](Cargo.lock) — Pins the crate's dependencies.
- [Cargo.toml](Cargo.toml) — Declares the crate and its dependencies.
- [LICENCE](LICENCE) — Contains the MIT licence that applies to this tool.
- [README.md](README.md) — Describes this folder and indexes its contents.
