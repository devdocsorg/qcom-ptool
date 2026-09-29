# Copyright (c) 2026 DevDocs
# SPDX-License-Identifier: BSD-3-Clause
"""Find every function definition and check its native reference.

Usage: test_reference_coverage.py generate | check

docs/source/conf.py runs "generate" before Sphinx reads its sources: it fails
on source formats without a configured extractor, on functions without a
configured renderer, and on undocumented functions, then writes one reference
page per source file to docs/source/contributing/.generated/. The Makefile
runs "check" after the HTML build: it fails when a function has no rendered
reference entry.

Functions are found in tracked and staged files with parsers, independently of
the renderers; nothing is executed. Python's ast module reads Python files,
tree-sitter-rust reads Rust files, and tree-sitter-bash reads shell scripts,
workflow run steps, and Makefile recipes.
Adapting a repository means adding its source formats to discover() and a
renderer for each language that defines functions to RENDERERS.
"""
import ast
import functools
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import tree_sitter_bash
import tree_sitter_rust
import yaml
from docutils.nodes import make_id
from sphinx.ext.napoleon import Config, GoogleDocstring
from tree_sitter import Language, Parser

ROOT = Path(__file__).resolve().parents[1]
PAGES = ROOT / "docs/source/contributing/.generated"
SITE = ROOT / "docs/site/contributing/.generated"
SHELL = Parser(Language(tree_sitter_bash.language()))
RUST = Parser(Language(tree_sitter_rust.language()))
# Folders sphinx-autoapi reads, with the module-name prefix of their files:
# qcom_ptool is a package, tests holds the unit package, and .github holds
# top-level modules.
PYTHON_ROOTS = {"qcom_ptool": "qcom_ptool", "tests": "", ".github": ""}
# Formats verified to hold no function definitions: documentation, partition
# layouts and templates, schemas, board files, and package metadata.
PLAIN_SUFFIXES = (".md", ".txt", ".lock", ".conf", ".in", ".yaml", ".json", ".toml", ".list", ".sha256")
PLAIN_NAMES = ("LICENSE", "LICENCE", "CODEOWNERS", ".gitignore", ".env.example")


def page_name(path):
    """Return the generated page name for a repository-relative source path.

    Args:
        path (str): Source path, such as ``ci/build.sh``.

    Returns:
        str: The page name without a suffix, such as ``ci-build.sh``.

    Example:
        ``page_name("ci/build.sh")`` returns ``"ci-build.sh"``.
    """
    return path.replace("/", "-")


def page_title(path):
    """Return a page heading that shows a source path literally.

    Args:
        path (str): Source path, such as ``qcom_ptool/loaders/__init__.py``.

    Returns:
        str: A Markdown level-one heading with underscores and asterisks escaped,
        so Markdown does not read ``__init__`` as emphasis.

    Example:
        ``page_title("a/__init__.py")`` returns ``"# a/\\_\\_init\\_\\_.py\\n"``.
    """
    return "# " + re.sub(r"([_*])", r"\\\1", path) + "\n"


def shell_functions(path, where, text):
    """List the shell functions defined in a shell text.

    Args:
        path (str): Source path, used in reports.
        where (str): Location inside the file, such as a workflow step, or "".
        text (str): Shell code.

    Returns:
        list[dict]: One entry per function with its name, line, and comment block.

    Raises:
        ValueError: The shell parser cannot read the text.

    Example:
        ``shell_functions("ci/build.sh", "", "f() { :; }")`` finds ``f``.
    """
    tree = SHELL.parse(text.encode())
    if tree.root_node.has_error:
        raise ValueError(f"{path}{where}: the shell parser cannot read it")
    found, stack = [], [tree.root_node]
    while stack:
        node = stack.pop()
        if node.type == "function_definition":
            found.append((node.start_point[0], node.child_by_field_name("name").text.decode()))
        stack.extend(node.children)
    lines, functions = text.splitlines(), []
    for start, name in sorted(found):
        comments = []
        while start - len(comments) > 0 and lines[start - len(comments) - 1].lstrip().startswith("#"):
            comments.insert(0, lines[start - len(comments) - 1].strip())
        functions.append({"language": "shell", "path": path, "where": where, "name": name,
                          "line": start + 1, "doc": "\n".join(comments)})
    return functions


def python_functions(path, text):
    """List the functions and methods defined in a Python file.

    Args:
        path (str): Source path, used in reports.
        text (str): Python source.

    Returns:
        list[dict]: One entry per function with its qualified name, line,
        docstring, parameter names, whether it returns a value, and whether it
        is nested in another function. Nested functions are included.

    Example:
        ``python_functions("tool.py", "def f():\\n    pass\\n")`` finds ``f``.
    """
    functions, stack = [], [(ast.parse(text, path), "", False)]
    while stack:
        node, prefix, in_function = stack.pop()
        for child in ast.iter_child_nodes(node):
            is_function = isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
            if is_function:
                arguments = child.args
                names = [a.arg for a in arguments.posonlyargs + arguments.args + arguments.kwonlyargs]
                names += [a.arg for a in (arguments.vararg, arguments.kwarg) if a]
                if isinstance(node, ast.ClassDef) and names and names[0] in ("self", "cls"):
                    names = names[1:]
                own = [n for n in ast.walk(child) if n is not child]
                nested = {id(n) for f in own if isinstance(f, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda))
                          for n in ast.walk(f)}
                returns = any(isinstance(n, ast.Return) and n.value is not None
                              and not (isinstance(n.value, ast.Constant) and n.value.value is None)
                              and id(n) not in nested for n in own)
                yields = any(isinstance(n, (ast.Yield, ast.YieldFrom)) and id(n) not in nested for n in own)
                functions.append({"language": "python", "path": path, "where": "", "name": prefix + child.name,
                                  "line": child.lineno, "doc": ast.get_docstring(child) or "",
                                  "params": names, "returns": returns or yields, "nested": in_function,
                                  "signature": ast.unparse(child.args)})
            name = prefix + child.name + "." if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef,
                                                                     ast.ClassDef)) else prefix
            stack.append((child, name, in_function or is_function))
    return sorted(functions, key=lambda function: function["line"])


def rust_functions(path, text):
    """List the functions and methods defined in a Rust file.

    Args:
        path (str): Source path, used in reports.
        text (str): Rust source.

    Returns:
        list[dict]: One entry per function with its name (``Type::method`` for
        methods), first and last line, outer doc comment, parameter names,
        whether it declares a return type, and its signature.

    Raises:
        ValueError: The Rust parser cannot read the text.

    Example:
        ``rust_functions("src/lib.rs", "fn f() {}")`` finds ``f``.
    """
    source = text.encode()
    tree = RUST.parse(source)
    if tree.root_node.has_error:
        raise ValueError(f"{path}: the Rust parser cannot read it")
    functions, stack = [], [(tree.root_node, None)]
    while stack:
        node, impl = stack.pop()
        if node.type == "function_item":
            body = node.child_by_field_name("body")
            signature = source[node.start_byte:body.start_byte if body else node.end_byte].decode().strip()
            name = node.child_by_field_name("name").text.decode()
            if impl is not None:
                impl_body = impl.child_by_field_name("body")
                signature = source[impl.start_byte:impl_body.start_byte].decode().strip() + "\n" + signature
                name = impl.child_by_field_name("type").text.decode() + "::" + name
            comments, sibling = [], node.prev_named_sibling
            while sibling is not None and sibling.type in ("attribute_item", "line_comment", "block_comment"):
                if sibling.type != "attribute_item":
                    if sibling.child_by_field_name("outer") is None:
                        break
                    comments.insert(0, sibling.child_by_field_name("doc").text.decode().rstrip("\n"))
                sibling = sibling.prev_named_sibling
            parameters = node.child_by_field_name("parameters")
            params = [p.child_by_field_name("pattern").text.decode() for p in parameters.named_children
                      if p.type == "parameter"]
            functions.append({"language": "rust", "path": path, "where": "", "name": name,
                              "line": node.start_point[0] + 1, "end": node.end_point[0] + 1,
                              "doc": "\n".join(line[1:] if line.startswith(" ") else line for line in comments),
                              "params": params, "returns": node.child_by_field_name("return_type") is not None,
                              "signature": signature})
        for child in node.children:
            stack.append((child, node if node.type == "impl_item" else impl if node.type == "declaration_list" else None))
    return sorted(functions, key=lambda function: function["line"])


def discover():
    """Find every function in the tracked sources.

    Returns:
        tuple[list[dict], list[str]]: The functions found, and the problems that
        stop the build, such as a source format without an extractor.

    Example:
        ``functions, problems = discover()``
    """
    listed = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    functions, problems = [], []
    for path in sorted(set(filter(None, listed.split("\0")))):
        full = ROOT / path
        if path.startswith("docs/site/") or not full.is_file():
            continue  # Generated output derives from these sources; deleted files have no content.
        text = full.read_text(errors="replace")
        try:
            if full.suffix == ".sh" or re.match(r"#!.*\b(ba)?sh\b", text.split("\n", 1)[0]):
                functions += shell_functions(path, "", text)
            elif full.suffix == ".py":
                functions += python_functions(path, text)
            elif full.suffix == ".rs":
                functions += rust_functions(path, text)
            elif path.startswith(".github/workflows/") and full.suffix in (".yml", ".yaml"):
                workflow = yaml.safe_load(text) or {}
                default = ((workflow.get("defaults") or {}).get("run") or {}).get("shell", "bash")
                for job_id, job in (workflow.get("jobs") or {}).items():
                    shell = ((job.get("defaults") or {}).get("run") or {}).get("shell", default)
                    for number, step in enumerate(job.get("steps") or [], 1):
                        where = f" (job {job_id}, step {number})"
                        if "run" not in step:
                            continue
                        if not re.match(r"(ba)?sh\b", str(step.get("shell", shell))):
                            problems.append(f"{path}{where}: shell {step['shell']!r} has no configured extractor")
                            continue
                        # GitHub substitutes expressions before the shell runs.
                        run = re.sub(r"\$\{\{.*?\}\}", "GITHUB_EXPRESSION", str(step["run"]))
                        functions += shell_functions(path, where, run)
            elif full.name == "Makefile":
                # Each recipe line runs in the shell after make expands its automatic
                # variables, such as $@, to file names and turns $$ into $.
                recipes = [re.sub(r"\$[@<^*?+|%]", "MAKE_VARIABLE", line[1:].lstrip("@-+").replace("$$", "\0"))
                           .replace("\0", "$") for line in text.splitlines() if line.startswith("\t")]
                functions += shell_functions(path, " (recipes)", "\n".join(recipes))
            elif full.suffix == ".html" and "<script" not in text.lower():
                pass  # Templates without scripts define no functions.
            elif full.suffix not in PLAIN_SUFFIXES and full.name not in PLAIN_NAMES:
                problems.append(f"{path}: no function extractor is configured for this format; "
                                "add it to .github/test_reference_coverage.py")
        except (SyntaxError, ValueError) as error:
            problems.append(f"{path}: {error}")
    return functions, problems


def module_name(path):
    """Return the module name sphinx-autoapi gives a Python source file.

    Args:
        path (str): Repository-relative path of a Python file.

    Returns:
        str: The dotted module name, such as ``qcom_ptool.loaders.conf``.

    Raises:
        ValueError: The file is outside the folders listed in ``PYTHON_ROOTS``.

    Example:
        ``module_name("tests/unit/test_utils.py")`` returns ``"unit.test_utils"``.
    """
    parts = Path(path).with_suffix("").parts
    if parts[0] not in PYTHON_ROOTS:
        raise ValueError(f"{path}: sphinx-autoapi does not read this folder; add it to PYTHON_ROOTS "
                         "in .github/test_reference_coverage.py")
    parts = ((PYTHON_ROOTS[parts[0]],) if PYTHON_ROOTS[parts[0]] else ()) + parts[1:]
    return ".".join(parts[:-1] if parts[-1] == "__init__" else parts)


@functools.cache
def rustdoc_items(crate):
    """Return the functions rustdoc documents in one crate.

    Args:
        crate (pathlib.Path): Folder holding the crate's ``Cargo.toml``.

    Returns:
        dict: ``(source path, last line)`` mapped to the function's doc comment.

    Raises:
        ValueError: ``RUSTDOC_TOOLCHAIN`` is unset; the Makefile sets it.
        subprocess.CalledProcessError: cargo or rustdoc failed.

    Example:
        ``rustdoc_items(ROOT / "degpt")``
    """
    if not os.environ.get("RUSTDOC_TOOLCHAIN"):
        raise ValueError("RUSTDOC_TOOLCHAIN names no toolchain; build through make -f docs/source/Makefile")
    toolchain = "+" + os.environ["RUSTDOC_TOOLCHAIN"]
    manifest = str(crate / "Cargo.toml")
    metadata = json.loads(subprocess.run(
        ["cargo", toolchain, "metadata", "--locked", "--no-deps", "--format-version", "1",
         "--manifest-path", manifest], capture_output=True, text=True, check=True).stdout)
    found = {}
    for target in metadata["packages"][0]["targets"]:
        kind = "lib" if "lib" in target["kind"] else "bin" if "bin" in target["kind"] else None
        if kind is None:
            continue
        output = crate / "target/rustdoc-json" / f"{kind}-{target['name']}"
        selector = ["--lib"] if kind == "lib" else ["--bin", target["name"]]
        subprocess.run(["cargo", toolchain, "rustdoc", "--locked", "--quiet", "--manifest-path", manifest,
                        "--target-dir", str(output), *selector, "--", "-Z", "unstable-options",
                        "--output-format", "json", "--document-private-items"], check=True)
        data = json.loads((output / "doc" / (target["name"].replace("-", "_") + ".json")).read_text())
        for item in data["index"].values():
            if item["crate_id"] == 0 and "function" in item["inner"] and item["span"]:
                path = (crate / item["span"]["filename"]).relative_to(ROOT).as_posix()
                found[(path, item["span"]["end"][0])] = item["docs"] or ""
    return found


class PythonAutoapi:
    """Render Python docstrings with sphinx-autoapi and napoleon.

    sphinx-autoapi parses the source without importing it: the legacy
    ``ptool``, ``msp``, and ``gen_contents`` modules run their command-line
    programs on import. Each page names the module's functions and methods
    explicitly, leaving out module variables. autoapi does not document
    functions nested in other functions, so their docstrings are converted with
    napoleon here.
    """

    def missing(self, function):
        """Return the required docstring parts a Python function lacks.

        Args:
            function (dict): A function found by ``python_functions``.

        Returns:
            list[str]: The missing parts; empty when the docstring is complete.

        Example:
            ``PythonAutoapi().missing({"doc": "", "params": [], "returns": False})``
            returns ``["docstring", "Example"]``.
        """
        doc = function["doc"]
        missing = [part for part, present in (("docstring", doc.strip()), ("Example", "Example" in doc))
                   if not present]
        missing += [f"Args entry with a type for {name}" for name in function["params"]
                    if not re.search(rf"^\s+\**{re.escape(name)} \(.+\):", doc, re.M)]
        if function["returns"] and not re.search(r"^(Returns|Yields):\n\s+[^\n]+: ", doc, re.M):
            missing.append("Returns or Yields entry with a type")
        return missing

    def page(self, path, functions):
        """Return the reference page for one Python file.

        Args:
            path (str): Source path of a module under ``PYTHON_ROOTS``.
            functions (list[dict]): The functions defined in it.

        Returns:
            str: A MyST page that renders the module docstring and each function
            with sphinx-autoapi, and nested functions with napoleon.

        Example:
            ``PythonAutoapi().page("qcom_ptool/utils.py", functions)``
        """
        module, entries, methods = module_name(path), [], {}
        for function in functions:
            owner, _, name = function["name"].rpartition(".")
            if function["nested"]:
                continue
            if not owner:
                entries.append(f".. autoapifunction:: {module}.{name}\n")
            elif owner not in methods:
                methods[owner] = [name]
                entries.append(owner)
            else:
                methods[owner].append(name)
        body = "\n".join(entry if entry.startswith("..") else
                         f".. autoapiclass:: {module}.{entry}\n   :members: {', '.join(methods[entry])}\n"
                         for entry in entries)
        page = f"{page_title(path)}\n```{{eval-rst}}\n.. autoapimodule:: {module}\n\n{body}```\n"
        for function in (f for f in functions if f["nested"]):
            lines = GoogleDocstring(function["doc"], Config(napoleon_use_param=True)).lines()
            text = "\n".join(f"   {line}" if line else "" for line in lines)
            page += (f"\n```{{eval-rst}}\n.. py:function:: {function['name']}({function['signature']})\n"
                     f"   :module: {module}\n\n{text}\n```\n")
        return page

    def rendered(self, function, html):
        """Return whether the built page holds the function's entry.

        Args:
            function (dict): A function found by ``python_functions``.
            html (str): The built reference page.

        Returns:
            bool: True when the page has an anchored entry for the function.

        Example:
            ``PythonAutoapi().rendered(function, html)``
        """
        return f'id="{module_name(function["path"])}.{function["name"]}"' in html


class Rustdoc:
    """Render Rust doc comments extracted by rustdoc's JSON output.

    rustdoc's JSON output needs the pinned nightly toolchain that the Makefile
    names in ``RUSTDOC_TOOLCHAIN`` and installs in ``setup``. Each crate's
    library and binary targets are documented with their private items, and
    every discovered function must appear in rustdoc's output.
    """

    def missing(self, function):
        """Return the required doc-comment sections a Rust function lacks.

        Args:
            function (dict): A function found by ``rust_functions``.

        Returns:
            list[str]: The missing sections; empty when the comment is complete.

        Example:
            ``Rustdoc().missing({"doc": "", "params": [], "returns": False})``
            returns ``["doc comment", "# Examples"]``.
        """
        doc = function["doc"]
        missing = [part for part, present in (("doc comment", doc.strip()), ("# Examples", "# Examples" in doc))
                   if not present]
        missing += [f"# Arguments entry for {name}" for name in function["params"]
                    if not re.search(rf"^\* `{re.escape(name)}`", doc, re.M)]
        if function["returns"] and not re.search(r"^# (Returns|Errors)$", doc, re.M):
            missing.append("# Returns or # Errors")
        return missing

    def page(self, path, functions):
        """Return the reference page for one Rust file.

        Args:
            path (str): Source path inside a Cargo crate.
            functions (list[dict]): The functions defined in it.

        Returns:
            str: A Markdown page with each function's signature and rustdoc text.

        Raises:
            ValueError: The file is outside a crate, or rustdoc omitted a function.

        Example:
            ``Rustdoc().page("degpt/src/main.rs", functions)``
        """
        crate = next((folder for folder in (ROOT / path).parents if (folder / "Cargo.toml").is_file()), None)
        if crate is None:
            raise ValueError(f"{path}: no Cargo.toml found above this file")
        items, page = rustdoc_items(crate), page_title(path)
        for function in functions:
            if (path, function["end"]) not in items:
                raise ValueError(f"{path}:{function['line']}: rustdoc did not document {function['name']}")
            text, fence = [], False
            for line in items[(path, function["end"])].splitlines():
                if line.startswith("```"):
                    fence = not fence
                    info = line[3:].strip()
                    # rustdoc treats unlabelled blocks and its test attributes as Rust.
                    if fence and all(tag in ("rust", "ignore", "no_run", "should_panic", "compile_fail")
                                     or tag.startswith("edition") for tag in filter(None, info.split(","))):
                        line = "```rust"
                elif fence and (line == "#" or line.startswith("# ")):
                    continue  # rustdoc hides these example lines.
                elif not fence and line.startswith("#"):
                    line = "##" + line
                text.append(line)
            page += f"\n## {function['name']}\n\n```rust\n{function['signature']}\n```\n\n" + "\n".join(text) + "\n"
        return page

    def rendered(self, function, html):
        """Return whether the built page holds the function's entry.

        Args:
            function (dict): A function found by ``rust_functions``.
            html (str): The built reference page.

        Returns:
            bool: True when the page has a section for the function.

        Example:
            ``Rustdoc().rendered({"name": "Header::fmt"}, '<section id="header-fmt">')`` returns ``True``.
        """
        return f'<section id="{make_id(function["name"])}">' in html


# Renderers by language. Each provides missing(function), page(path, functions),
# and rendered(function, html), as PythonAutoapi and Rustdoc do.
RENDERERS = {"python": PythonAutoapi(), "rust": Rustdoc()}


def main():
    """Generate the reference pages or check the rendered entries.

    Returns:
        None: Exits with a message when a problem is found.

    Example:
        ``python .github/test_reference_coverage.py check``
    """
    mode = sys.argv[1] if len(sys.argv) == 2 else ""
    if mode not in ("generate", "check"):
        raise SystemExit(__doc__)
    functions, problems = discover()
    for function in functions:
        location = f"{function['path']}:{function['line']}{function['where']}"
        renderer = RENDERERS.get(function["language"])
        if renderer is None:
            problems.append(f"{location}: {function['name']} is a {function['language']} function, and no "
                            f"{function['language']} renderer is configured; add one to RENDERERS")
        elif missing := renderer.missing(function):
            problems.append(f"{location}: {function['name']} is undocumented; missing {', '.join(missing)}")
    if not problems and mode == "generate":
        PAGES.mkdir(parents=True, exist_ok=True)
        for path in sorted({function["path"] for function in functions}):
            defined = [function for function in functions if function["path"] == path]
            try:
                page = RENDERERS[defined[0]["language"]].page(path, defined)
            except (ValueError, subprocess.CalledProcessError) as error:
                problems.append(str(error))
                continue
            # Generated pages follow the extractor's output, not the authored style rules.
            (PAGES / f"{page_name(path)}.md").write_text(f"<!-- markdownlint-disable-file -->\n{page}")
    elif not problems:
        for function in functions:
            built = SITE / f"{page_name(function['path'])}.html"
            content = built.read_text() if built.is_file() else ""
            if not RENDERERS[function["language"]].rendered(function, content):
                problems.append(f"{function['path']}:{function['line']}: {function['name']} has no complete "
                                f"rendered entry in {built.relative_to(ROOT)}")
    for problem in problems:
        print(f"reference coverage: {problem}", file=sys.stderr)
    if problems:
        raise SystemExit(f"Reference coverage failed with {len(problems)} problem(s).")
    print(f"Reference coverage: {len(functions)} function(s) documented"
          + (" and rendered." if mode == "check" else "; pages generated."))


if __name__ == "__main__":
    main()
