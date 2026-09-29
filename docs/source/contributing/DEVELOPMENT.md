# Set up your development environment

This walkthrough prepares a checkout, runs the tool's checks, and builds this
documentation.

## Prerequisites

Git, GNU Make, and Python 3.8 or newer for the tool; this walkthrough was tested
with Git 2.55, GNU Make 4.4.1, and Python 3.12. The documentation also needs
[uv](https://docs.astral.sh/uv/getting-started/installation/) 0.12.3, the version
CI pins, which installs Python 3.12 for it; [rustup](https://rustup.rs/), tested
with 1.29; and Chromium for the offline check, tested with 151, or the browser
that `make -f docs/source/Makefile browser` installs. Installing dependencies needs
network access; reading the built site does not.

## Clone the proposal

```sh
git clone -b docs/repository-documentation https://github.com/devdocsorg/qcom-ptool.git
cd qcom-ptool
```

This branch holds the documentation tooling. The
[contribution guide](CONTRIBUTING.md) explains where to send changes.

## Dependencies

At runtime the tool targets Python 3.8+ and depends on two third-party
libraries, `PyYAML` and `jsonschema`, used to load and validate the YAML
partition source. Both are declared in `pyproject.toml` and pulled in
automatically by `pip install .`.

For development, `make lint` invokes `ruff` and `mypy` and `make unit-test`
runs the `pytest` suite under `tests/unit/`. On Debian/Ubuntu, install
them as follows (ruff is not packaged in apt on all releases/architectures,
so we install it from snap):

```sh
sudo snap install ruff
sudo apt install mypy python3-pytest
```

## Makefile targets

| Target        | Description                                                |
|---------------|------------------------------------------------------------|
| `all`         | Generate partition XML and GPT binaries for all platforms  |
| `lint`        | Run ruff (linter) and mypy (type checker) on the package   |
| `unit-test`   | Run the pytest suite under `tests/unit/`                   |
| `integration` | Build all platforms and verify generated files are present |
| `check`       | Run `lint`, `unit-test`, and `integration`                 |
| `install`     | Install the package (`pip install .`)                      |
| `clean`       | Remove generated XML and binary files from platforms/      |

The Makefile invokes `qcom-ptool` from `PATH`. Install the package (or
`pip install -e .` from the repo root) before running `make all`.

### Quick start

```sh
# install the tool
pip install -e .

# install linters and test runner (Debian/Ubuntu)
sudo snap install ruff
sudo apt install mypy python3-pytest

# run linters and unit tests
make lint
make unit-test

# build all platforms and run tests
make check
```

Expected result: `make lint` reports `All checks passed!` and `Success: no issues
found`, `make unit-test` reports no failures, and `make check` exits with status 0
after writing each platform's files under `platforms/`. Before pushing, also run
the commands in the [contribution guide](CONTRIBUTING.md), which set `PTOOL_SEED`
for the checksum check.

## Build the documentation

```sh
make -f docs/source/Makefile setup
make -f docs/source/Makefile check
```

`setup` creates `.docs-venv/` from `docs/source/requirements.lock` and installs the
nightly Rust toolchain named in the
[documentation Makefile](https://github.com/devdocsorg/qcom-ptool/blob/docs/repository-documentation/docs/source/Makefile).
`check` builds `docs/site/` with warnings treated as errors, prints
`Reference coverage: ... documented and rendered.`, and opens a copy of the site
in headless Chromium with networking disabled to check links, anchors, and search.
Without a system `chromium`, run `make -f docs/source/Makefile browser` first.
Open `docs/site/index.html` directly in a browser; Git ignores the site.

## Document functions

[test_reference_coverage.py](https://github.com/devdocsorg/qcom-ptool/blob/docs/repository-documentation/.github/test_reference_coverage.py)
finds every function in the Python, Rust, and shell sources, Makefile recipes, and
workflow steps, and the build fails when one lacks its documentation or its
reference entry:

- Python: a Google-style docstring with an `Args:` entry and type for each
  parameter, a typed `Returns:` or `Yields:` entry when it returns a value, and an
  `Example:` section. sphinx-autoapi renders it without importing the module.
- Rust: a `///` comment with a summary, an `# Arguments` item per parameter,
  `# Returns` or `# Errors` when it returns a value, and `# Examples`, extracted
  with rustdoc's JSON output.

After an intentional documentation-tool update, regenerate the lock with
`uv pip compile --python-version 3.12 docs/source/requirements.txt -o docs/source/requirements.lock`,
run `setup`, and rebuild before committing the requirements and lock.
