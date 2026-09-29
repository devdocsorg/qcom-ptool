# Run from the repository root: make -f docs/source/Makefile <target>.
# setup installs only the pinned documentation toolchain: the locked Python
# packages in .docs-venv, apart from any environment used for the tool itself,
# and the nightly Rust toolchain whose rustdoc JSON output documents degpt.
# html removes stale generated pages, builds the complete site strictly, and
# fails unless every function has a documented, rendered reference entry.
# check rebuilds the site and checks it offline, including that direct-file
# search avoids fetch(). Readers build the site with: setup html.
.PHONY: setup html check browser

# rustdoc's JSON output format is available only on nightly toolchains.
export RUSTDOC_TOOLCHAIN = nightly-2026-09-15

setup:
	uv venv --python 3.12 --clear .docs-venv
	uv pip install --python .docs-venv/bin/python -r docs/source/requirements.lock
	rustup toolchain install $(RUSTDOC_TOOLCHAIN) --profile minimal

html:
	rm -rf docs/site docs/source/contributing/.generated
	.docs-venv/bin/sphinx-build -W --keep-going -E -a -b html -d docs/.doctrees docs/source docs/site
	.docs-venv/bin/python .github/finalise_site.py
	.docs-venv/bin/python .github/test_reference_coverage.py check

# Install a user-local browser only when system Chromium is unavailable.
browser:
	.docs-venv/bin/playwright install chromium

check: html
	.docs-venv/bin/python .github/check_offline.py docs/site partition
	test -f docs/site/index.html
	grep -q 'SHOW_SEARCH_SUMMARY: false' docs/site/_static/documentation_options.js
