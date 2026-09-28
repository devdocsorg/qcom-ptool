# qcom-ptool documentation

qcom-ptool turns the partition layouts in this repository into GPT images and the
XML files that Qualcomm flashing tools read.

- [Generate partition files for a board](user/USAGE.md) walks through one layout.
- The [configuration reference](user/CONFIGURATION.md) describes the layout formats and build settings.
- [Development setup](contributing/DEVELOPMENT.md) installs the tools and runs the checks.
- The [contribution guide](contributing/CONTRIBUTING.md) explains how to submit changes.
- The [function reference](contributing/README.md#function-reference) is generated from the source comments.

```{toctree}
:hidden:

user/README
contributing/README
```

## Folders

- [user/](user/README.md) — Holds the tutorial and the configuration reference.
- [contributing/](contributing/README.md) — Holds the contribution guide, development setup, and function reference.
- [.templates/](https://github.com/devdocsorg/qcom-ptool/tree/docs/repository-documentation/docs/source/.templates) — Supplies the generated site's entry-point redirect.

## Files

- [Makefile](https://github.com/devdocsorg/qcom-ptool/blob/docs/repository-documentation/docs/source/Makefile) — Provides the shared local and CI setup, build, and check commands.
- [README.md](README.md) — Introduces the guides and supplies the site's homepage.
- [conf.py](https://github.com/devdocsorg/qcom-ptool/blob/docs/repository-documentation/docs/source/conf.py) — Configures Markdown rendering, the Python and Rust function reference, local navigation, and search.
- [requirements.txt](https://github.com/devdocsorg/qcom-ptool/blob/docs/repository-documentation/docs/source/requirements.txt) — Pins the documentation packages.
- [requirements.lock](https://github.com/devdocsorg/qcom-ptool/blob/docs/repository-documentation/docs/source/requirements.lock) — Locks direct and transitive documentation dependencies for reproducible builds.
