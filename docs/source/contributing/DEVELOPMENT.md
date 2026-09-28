# Set up your development environment

This walkthrough prepares a checkout, runs the project checks, and builds and
checks the documentation site and function reference.

## Prerequisites

- Git and GNU Make.
- Python and the linters and test runner listed under
  [Dependencies](https://github.com/devdocsorg/qcom-ptool/blob/docs/repository-documentation/README.md#dependencies).
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (CI uses 0.12.3).
  It installs Python 3.12 for the documentation tools.
- A Rust toolchain with `cargo` (tested with 1.94.0). It builds `degpt` and the
  pinned `sphinx-rustdocgen` extractor.
- Chromium, or Playwright's browser from step 2.
- Network access while installing. Reading the built site needs none.

## 1. Clone the review branch

```sh
git clone -b docs/repository-documentation https://github.com/devdocsorg/qcom-ptool.git
cd qcom-ptool
```

This branch carries the documentation tools. Once they are merged, clone
`https://github.com/qualcomm-linux/qcom-ptool.git` and use `main`. The
[contribution guide](CONTRIBUTING.md) says where changes go.

## 2. Install the documentation tools

```sh
make -f docs/source/Makefile setup
```

This recreates `.venv` from `docs/source/requirements.lock` and builds the matching
`sphinx-rustdocgen` into `.venv/bin`; it ends with
``Installed package `sphinx-rustdocgen v1.2.1` ``. Without system Chromium, also run
`make -f docs/source/Makefile browser`.

## 3. Install qcom-ptool and run the checks

Install the package and its development tools as described under
[Development](https://github.com/devdocsorg/qcom-ptool/blob/docs/repository-documentation/README.md#development), in an environment other than `.venv`,
which setup replaces. Then run the checks listed in
[Submitting a pull request](CONTRIBUTING.md#submitting-a-pull-request) in that
order. Each exits with status 0, and `check-checksums` prints nothing when every
artifact matches.

The last check, `make -f docs/source/Makefile check`, rebuilds `docs/site/` with
warnings treated as errors, runs `.github/test_reference_coverage.py`, opens a copy
of the site offline in headless Chromium, and rejects changed or untracked generated
output. It prints `Function reference coverage: 0 problems` and a JSON summary with
no network requests or browser errors. After changing any source, commit the source
and the regenerated `docs/site/` together, then rerun it. To rebuild without the
checks, run `make -f docs/source/Makefile html`.

Open `docs/site/index.html` directly in a browser to read the result.

## Document functions

The coverage check discovers functions from the source and requires, for each one:

- Python: a docstring with a one-sentence purpose, `:param:` for each parameter,
  `:type:` where there is no annotation, `:returns:` and `:rtype:` (or a return
  annotation) when a value is returned, `:raises:` where relevant, and an
  `Example:` line. AutoAPI renders it without importing the module.
- Rust: a `///` comment with the purpose, failure behaviour, and an `Example:`.
  sphinxcontrib-rust renders private items too.

Shell functions in scripts, workflow `run` steps, or Makefile recipes, and files in
other languages, fail the check until a native extractor is configured for them.

## Update the documentation tools

Change a pin in `docs/source/requirements.txt`, then regenerate the lock:

```sh
uv pip compile --python-version 3.12 docs/source/requirements.txt -o docs/source/requirements.lock
```

Keep the `sphinx-rustdocgen` version in `docs/source/Makefile` equal to
`sphinxcontrib-rust`. Run setup and check, and commit the source and site together.

## Update the repository map

The map at the end of the root README is generated from the shared
[Qualcomm repository map](https://github.com/devdocsorg/qualcomm-repository-map);
updating it needs access to that repository. Follow its
[maintenance procedure](https://github.com/devdocsorg/qualcomm-repository-map/blob/main/data/README.md)
and export the block with its `tools/map_build.py --export` command instead of
editing the block by hand.
