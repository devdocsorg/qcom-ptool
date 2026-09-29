# qcom-ptool

qcom-ptool contains various device partitioning utilities like ptool.py, gen_partitions.py and various sample partition configuration files needed for Qualcomm SoCs. Qualcomm Linux currently supports two reference Linux based OSes (Yocto with [meta-qcom](https://github.com/qualcomm-linux/meta-qcom) and Debian with [qcom-deb-images](https://github.com/qualcomm-linux/qcom-deb-images)) which uses this tool to generate partition table layouts. The partition GUIDs, names and size budgets are picked to support boot flows as follows:

- (preferred) "edk2/UEFI": PBL => XBL => edk2/UEFI => high-level OS (Linux)
- (legacy) "U-Boot/UEFI": PBL => XBL => ABL => U-Boot/UEFI => high-level OS (Linux)

# Installation

The project is packaged as a standard Python distribution and installs a
single `qcom-ptool` command with subcommands for each utility:

```sh
pip install .
```

Once installed, the tool is invoked as:

```sh
qcom-ptool gen_partition -i platforms/<soc>/<variant>/partitions.conf -o partitions.xml
qcom-ptool gen_contents  -p partitions.xml -t contents.xml.in -o contents.xml
qcom-ptool gen_udev_rules -o 55-qcom-raw-partitions-noblkid.rules
qcom-ptool ptool         -x partitions.xml
qcom-ptool msp           -r rawprogram0.xml -d /dev/sdX -p patch0.xml
```

By default, the generator scans all `platforms/*/*/partitions.conf` files.
Repeatable `-i` options can select specific layouts. It skips known filesystem
partition names and emits exact `PARTNAME` rules for the others. Unknown names
retain normal blkid probing. The rules use
`UDEV_DISABLE_PERSISTENT_STORAGE_BLKID_FLAG` on systemd v252 and newer.

Run `qcom-ptool <subcommand> -h` to see the options accepted by each
subcommand.

# Branches

| Branch | Purpose and status | Use | Contributions |
| --- | --- | --- | --- |
| `main` | Default and only branch, holding the tool and all partition layouts | Install and build from it | Accepted through the [contribution guide](docs/source/contributing/CONTRIBUTING.md) |

This table lists every current branch. [BRANCHES.md](BRANCHES.md) describes branch
maintenance.

# Documentation

Build the documentation site with `make -f docs/source/Makefile setup html` from
the repository root, then open `docs/site/index.html` directly in a browser. The
[documentation guide](docs/README.md) explains where its source lives.

- [Tutorial](docs/source/user/USAGE.md) — Generate one board's partition tables and flashing files.
- [Configuration reference](docs/source/user/CONFIGURATION.md) — Understand layout files, board files, and environment settings.
- [Function reference](docs/source/contributing/README.md#function-reference) — Browse the documented functions of every source file.
- [Development setup](docs/source/contributing/DEVELOPMENT.md) — Install the tools, run the checks, and build the documentation.

# Development

The [development setup](docs/source/contributing/DEVELOPMENT.md) lists the
dependencies, Makefile targets, and quick start for changing and checking the tool.

## Code contributions

See [CONTRIBUTING.md file](CONTRIBUTING.md) for instructions on how to send
code contributions to this project. You can also [report an issue on
GitHub](../../issues).

# Maintainer(s)

See [CODEOWNERS](.github/CODEOWNERS).

# License

This project is licensed under the [BSD-3-clause
License](https://spdx.org/licenses/BSD-3-Clause.html). See
[LICENSE](LICENSE) for the full license text.

# Repository layout

## Folders

- [.github/](.github/) — Holds [CODEOWNERS](.github/CODEOWNERS), the [CI workflows](.github/workflows/), the [issue](.github/ISSUE_TEMPLATE/) and [pull request](.github/PULL_REQUEST_TEMPLATE/pr_template.md) templates, and the documentation build scripts.
- [degpt/](degpt/README.md) — Contains a Rust tool that converts GPT images back into a ptool partition XML file.
- [docs/](docs/README.md) — Contains the documentation source and explains how to build the site.
- [platforms/](platforms/README.md) — Holds the partition layouts and contents templates for each supported board.
- [qcom_ptool/](qcom_ptool/README.md) — Contains the Python package behind the `qcom-ptool` command.
- [tests/](tests/README.md) — Holds the unit tests and the integration checks for generated files.

## Files

- [.env.example](.env.example) — Documents the environment settings the tool and Makefile read.
- [.gitignore](.gitignore) — Keeps generated partition files, Python caches, and the documentation build out of Git.
- [BRANCHES.md](BRANCHES.md) — Describes the purpose and maintenance of each long-lived branch.
- [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) — States participation standards and how to report conduct concerns.
- [CONTRIBUTING.md](CONTRIBUTING.md) — Points to the contribution guide and development setup.
- [LICENSE](LICENSE) — Contains the project's BSD-3-Clause licence text.
- [Makefile](Makefile) — Builds every platform's partition files and runs the lint, test, and integration checks.
- [NOTICE.md](NOTICE.md) — Retains the notices for adapted documentation tooling and templates.
- [README.md](README.md) — Introduces the project, its branches, documentation, and contents.
- [SECURITY.md](SECURITY.md) — Explains how to report a vulnerability privately.
- [pyproject.toml](pyproject.toml) — Declares the Python package, its dependencies, and the ruff, mypy, and pytest settings.
