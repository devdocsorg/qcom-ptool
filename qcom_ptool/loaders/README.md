# Loaders

Each loader turns one layout format into the form defined in
[spec.py](../spec.py); `gen_partition -i` chooses the loader by file extension.

## Files

- [README.md](README.md) — Describes this folder and indexes its contents.
- [\_\_init\_\_.py](__init__.py) — Chooses the loader for a path's extension.
- [conf.py](conf.py) — Reads `--disk` and `--partition` line files such as `partitions.conf`.
- [yaml.py](yaml.py) — Reads and validates single-storage YAML layouts.
