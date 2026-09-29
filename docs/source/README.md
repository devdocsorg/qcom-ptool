# qcom-ptool documentation

Start with the [tutorial](user/USAGE.md) to generate a board's partition files, or
follow the [development setup](contributing/DEVELOPMENT.md) to change the tool.

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
- [conf.py](https://github.com/devdocsorg/qcom-ptool/blob/docs/repository-documentation/docs/source/conf.py) — Configures Markdown rendering, the Python reference, local navigation, and search.
- [requirements.txt](https://github.com/devdocsorg/qcom-ptool/blob/docs/repository-documentation/docs/source/requirements.txt) — Pins the documentation packages.
- [requirements.lock](https://github.com/devdocsorg/qcom-ptool/blob/docs/repository-documentation/docs/source/requirements.lock) — Locks direct and transitive documentation dependencies for reproducible builds.
