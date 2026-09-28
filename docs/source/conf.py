# Copyright (c) 2026 DevDocs
# SPDX-License-Identifier: BSD-3-Clause
"""Configure the qcom-ptool documentation site and its function reference.

Reference pages are generated below ``contributing/.generated`` on every build:
one page per Python source file that defines functions or classes, and one page per
Rust source file from the pages that sphinx-rustdocgen writes for each crate.
"""

import ast
import builtins
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SOURCE = Path(__file__).resolve().parent
ROOT = SOURCE.parents[1]
GENERATED = SOURCE / "contributing" / ".generated"
# Rust crate folders documented with sphinx-rustdocgen.
RUST_CRATES = ["degpt"]
# Repository pages that the generated reference links to.
BLOB = "https://github.com/devdocsorg/qcom-ptool/blob/docs/repository-documentation"
# autoapi_dirs entries and the module prefix each gives its files.
PYTHON_DIRS = {"qcom_ptool": "qcom_ptool.", "tests/unit": "unit.", ".github": ""}

# Optional string; default 'Project name not set'.
project = "qcom-ptool"
# Optional list; default []. MyST renders Markdown; AutoAPI and sphinxcontrib-rust
# read Python and Rust documentation comments without importing or building code.
extensions = ["myst_parser", "autoapi.extension", "sphinxcontrib_rust"]
# Optional list; default []. The generated Rust pages use ::: directive fences.
myst_enable_extensions = ["colon_fence"]
# Optional string; default 'index'. README owns the homepage content.
root_doc = "README"
# Optional integer; default 0. Preserve links to Markdown headings.
myst_heading_anchors = 4
# Optional boolean; default False. Reject unresolved cross-references.
nitpicky = True
# Optional list; default []. Standard-library, pytest, and Rust types have no
# local pages; references to this project's functions and classes must resolve.
nitpick_ignore_regex = [
    (r"py:.*", r"(%s)(\..*)?" % "|".join(sorted(sys.stdlib_module_names | set(dir(builtins))))),
    (r"py:.*", r"pytest\..*|Any|(qcom_ptool\.spec\.)?(DiskParams|PartitionEntry|PartitionsByLun)"),
    (r"rust:.*", r".*"),
]
# Optional list; default []. Do not parse build templates as documentation.
exclude_patterns = [".templates/**"]
# Optional list; default []. Resolve the additional HTML template locally.
templates_path = [".templates"]
# Optional mapping; default {}. Generate an entry point without a second source index.
html_additional_pages = {"index": "index.html"}
# Optional boolean; default True. Avoid fetch() of local files for search excerpts.
html_show_search_summary = False
# Optional boolean; default True. Page sources stay in the repository, not the site.
html_copy_source = False
# Optional boolean; default True. No copyright holder is configured, so omit the empty notice.
html_show_copyright = False
# Optional boolean; default True. Keep "--" in option names such as --signoff.
smartquotes = False

# Required list for AutoAPI. Source folders parsed statically.
autoapi_dirs = [str(ROOT / folder) for folder in PYTHON_DIRS]
# Optional boolean; default True. Pages below come from the generated stubs instead.
autoapi_generate_api_docs = False
# Optional boolean; default True. Docstrings add no second summary of each module.
autoapi_add_toctree_entry = False

# Optional string; default 'changed'. conf.py below runs the extractor itself so the
# Rust pages follow the one-page-per-source-file naming of the Python pages.
rust_generate_mode = "skip"
# Optional string; default found on PATH. Use the binary pinned by the Makefile.
rust_rustdocgen = str(ROOT / ".venv" / "bin" / "sphinx-rustdocgen")
# Optional boolean or list; default True. The Rust domain index repeats the pages
# without usable summaries.
html_domain_indices = ["py-modindex"]

shutil.rmtree(GENERATED, ignore_errors=True)
GENERATED.mkdir(parents=True)
tracked = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard", "*.py"],
                         cwd=ROOT, check=True, capture_output=True, text=True).stdout.split()
for path in tracked:
    folder = next((f for f in PYTHON_DIRS if path.startswith(f + "/")), None)
    tree = ast.parse((ROOT / path).read_text())
    if folder is None or not any(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                                 for node in ast.walk(tree)):
        continue
    module = (PYTHON_DIRS[folder] + path[len(folder) + 1:-3].replace("/", ".")).removesuffix(".__init__")
    # Render the functions and classes each file defines, not the names it imports.
    rst = [f".. autoapimodule:: {module}", ""]
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            rst += [f".. autoapifunction:: {module}.{node.name}", ""]
        elif isinstance(node, ast.ClassDef):
            rst += [f".. autoapiclass:: {module}.{node.name}", "   :members:", "   :private-members:", ""]
    (GENERATED / (path.replace("/", "-") + ".md")).write_text(
        f"# {path.replace('_', chr(92) + '_')}\n\n[Source]({BLOB}/{path})\n\n```{{eval-rst}}\n"
        + "\n".join(rst) + "```\n"
    )

# sphinx-rustdocgen writes one page per module, titled and linked by module; rename
# each to its source file and drop the module toctrees, which the glob replaces.
with tempfile.TemporaryDirectory() as rust_pages:
    for crate in RUST_CRATES:
        options = {"crate_name": crate, "crate_dir": str(ROOT / crate), "doc_dir": rust_pages, "format": "md",
                   "visibility": "pvt", "force": True, "strip_src": True}
        subprocess.run([rust_rustdocgen, json.dumps(options)], check=True)
        for page in sorted((Path(rust_pages) / crate).rglob("*.md")):
            module = page.relative_to(Path(rust_pages) / crate).with_suffix("")
            source = next(f"{crate}/src/{name}" for name in (f"{module}.rs", f"{module}/mod.rs")
                          if (ROOT / crate / "src" / name).is_file())
            text = re.sub(r":::\{rubric\} Modules\n:::\n:::\{toctree\}.*?\n:::\n", "", page.read_text(), flags=re.S)
            body = text.split("\n", 1)[1]
            (GENERATED / (source.replace("/", "-") + ".md")).write_text(
                f"# {source.replace('_', chr(92) + '_')}\n\n[Source]({BLOB}/{source})\n{body}")
