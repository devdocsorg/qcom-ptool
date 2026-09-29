# Copyright (c) 2026 DevDocs
# SPDX-License-Identifier: BSD-3-Clause
"""Configure the qcom-ptool Markdown site for hosted and direct-file browsing."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
# Write the function reference pages before Sphinx reads the sources;
# undocumented or unsupported definitions stop the build.
if subprocess.run([sys.executable, str(ROOT / ".github/test_reference_coverage.py"), "generate"]).returncode:
    raise SystemExit(1)
# The coverage script names the folders whose Python sources autoapi reads.
sys.path.insert(0, str(ROOT / ".github"))
from test_reference_coverage import PYTHON_ROOTS  # noqa: E402

# Optional string; default 'Project name not set'.
project = "qcom-ptool"
# Optional list; default []. Render Markdown with MyST, and Python docstrings
# with sphinx-autoapi and napoleon (Google-style sections).
extensions = ["myst_parser", "autoapi.extension", "sphinx.ext.napoleon"]
# Required by autoapi; list of folders. Parse these sources without importing them.
autoapi_dirs = [str(ROOT / folder) for folder in PYTHON_ROOTS]
# Optional boolean; default True. The generated reference pages place each
# module with the autoapimodule directive instead of autoapi's own page tree.
autoapi_generate_api_docs = False
# Optional boolean; default True. No autoapi index page exists to add.
autoapi_add_toctree_entry = False
# Optional string; default 'index'. README owns the homepage content.
root_doc = "README"
# Optional integer; default 0. Preserve links to Markdown headings.
myst_heading_anchors = 4
# Optional boolean; default False. Reject unresolved cross-references.
nitpicky = True
# Optional list; default []. Signatures and docstrings name standard-library,
# third-party, and alias types and modules that have no page in this site.
nitpick_ignore_regex = [(r"py:.*", r".*")]
# Optional list; default []. Do not parse build templates as documentation.
exclude_patterns = [".templates/**"]
# Optional list; default []. Resolve the additional HTML template locally.
templates_path = [".templates"]
# Optional mapping; default {}. Generate an entry point without a second source index.
html_additional_pages = {"index": "index.html"}
# Optional boolean; default True. Avoid fetch() of local files for search excerpts.
html_show_search_summary = False
# Optional boolean; default True. Keep options such as --signoff and quotes
# literal instead of converting them to typographic dashes and quotes.
smartquotes = False
# Optional boolean; default True. Page sources stay in the repository, not the site.
html_copy_source = False
# Optional boolean; default True. No copyright holder is configured, so omit the empty notice.
html_show_copyright = False
