# degpt

A Rust tool that reads GPT images, such as the `gpt_both<N>.bin` files `ptool`
writes, prints their headers and entries, and writes a matching ptool partition
XML file. It assumes 4096-byte sectors. CI builds it with `cargo build`.

```sh
cd degpt
cargo run -- partitions.xml gpt_both0.bin
```

## Folders

- [src/](src/README.md) — Holds the program and its GPT parsing library.

## Files

- [README.md](README.md) — Describes this folder and indexes its contents.
- [.gitignore](.gitignore) — Keeps Cargo's `target/` build folder out of Git.
- [Cargo.lock](Cargo.lock) — Pins the resolved dependency versions.
- [Cargo.toml](Cargo.toml) — Declares the crate and its `gpt` and `uuid` dependencies.
- [LICENCE](LICENCE) — Contains the MIT licence that covers this folder.
