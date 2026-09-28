# Copyright (c) 2026 DevDocs
# SPDX-License-Identifier: BSD-3-Clause
"""Check that every function has native documentation and a rendered reference entry.

Run from the repository root after ``make -f docs/source/Makefile html``. Functions
are discovered from the sources, independently of the extractors: Python with
:mod:`ast`, Rust with tree-sitter, and shell code in scripts, workflow ``run``
values, and Makefile recipes with tree-sitter. Shell functions and unknown source
formats fail with a request to configure an extractor.
"""
import ast
import re
import subprocess
import sys
from pathlib import Path

import tree_sitter_bash
import tree_sitter_rust
import yaml
from tree_sitter import Language, Parser

SITE = Path("docs/site/contributing/.generated")
BASH = Parser(Language(tree_sitter_bash.language()))
RUST = Parser(Language(tree_sitter_rust.language()))
# Formats that hold data, templates, or prose rather than function definitions.
DATA_SUFFIXES = {".md", ".conf", ".in", ".yaml", ".yml", ".json", ".toml", ".lock", ".sha256",
                 ".list", ".txt", ".html", ".example"}
DATA_NAMES = {"LICENSE", "LICENCE", "CODEOWNERS", ".gitignore"}


def source_files():
    """Return the tracked and new, unignored files outside the generated site.

    :returns: Repository-relative paths.
    :rtype: list[str]

    Example: ``"qcom_ptool/ptool.py" in source_files()`` returns ``True``.
    """
    out = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"],
                         check=True, capture_output=True, text=True).stdout.split()
    return [p for p in out if not p.startswith(("docs/site/", "docs/source/contributing/.generated/"))]


def python_problems(path, text):
    """Report Python functions with incomplete docstrings or no rendered entry.

    A docstring needs a purpose sentence, ``:param`` and a type for each parameter,
    ``:returns:`` and a type when a value is returned, and an ``Example:``.
    Nested functions cannot be rendered, so only their docstrings are checked.

    :param path: Repository-relative source path.
    :type path: str
    :param text: Source code.
    :type text: str
    :returns: One message per problem.
    :rtype: list[str]

    Example: ``python_problems("x.py", "def f():\\n    pass\\n")`` reports a missing docstring.
    """
    page = SITE / (path.replace("/", "-") + ".html")
    html = page.read_text() if page.is_file() else ""
    problems, stack = [], [(ast.parse(text), "", False, False)]
    while stack:
        node, prefix, in_class, nested = stack.pop()
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.ClassDef):
                stack.append((child, prefix + child.name + ".", True, nested))
                continue
            if not isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                stack.append((child, prefix, in_class, nested))
                continue
            name = prefix + child.name
            where = f"{path}:{child.lineno} {name}"
            stack.append((child, name + ".", False, True))
            doc = ast.get_docstring(child) or ""
            if not doc.strip():
                problems.append(f"{where}: missing docstring")
                continue
            if doc.startswith((":", "Example:")):
                problems.append(f"{where}: missing purpose sentence")
            args = child.args
            params = [*args.posonlyargs, *args.args, *args.kwonlyargs]
            is_static = any(isinstance(d, ast.Name) and d.id == "staticmethod" for d in child.decorator_list)
            if in_class and params and not is_static:
                params = params[1:]
            params += [a for a in (args.vararg, args.kwarg) if a]
            for arg in params:
                if f":param {arg.arg}:" not in doc:
                    problems.append(f"{where}: missing :param {arg.arg}:")
                elif arg.annotation is None and f":type {arg.arg}:" not in doc:
                    problems.append(f"{where}: missing type for {arg.arg}")
            body = [n for stmt in child.body for n in ast.walk(stmt)]
            returns = any(isinstance(n, ast.Return) and n.value is not None
                          and not (isinstance(n.value, ast.Constant) and n.value.value is None) for n in body)
            if returns and ":returns:" not in doc:
                problems.append(f"{where}: missing :returns:")
            elif returns and child.returns is None and ":rtype:" not in doc:
                problems.append(f"{where}: missing :rtype:")
            if "Example:" not in doc:
                problems.append(f"{where}: missing Example:")
            if not nested and not re.search(rf'id="([\w.]+\.)?{re.escape(name)}"', html):
                problems.append(f"{where}: missing rendered entry in {page}")
    return problems


def rust_problems(path, text):
    """Report Rust functions without a doc comment, an example, or a rendered entry.

    :param path: Repository-relative source path.
    :type path: str
    :param text: Source code.
    :type text: str
    :returns: One message per problem.
    :rtype: list[str]

    Example: ``rust_problems("degpt/src/lib.rs", "fn f() {}")`` reports a missing doc comment.
    """
    page = SITE / (path.replace("/", "-") + ".html")
    html = page.read_text() if page.is_file() else ""
    problems, found = [], {}
    stack = [RUST.parse(text.encode()).root_node]
    while stack:
        node = stack.pop()
        stack.extend(node.children)
        if node.type != "function_item":
            continue
        fn = node.child_by_field_name("name").text.decode()
        where = f"{path}:{node.start_point[0] + 1} {fn}"
        doc, sibling = [], node.prev_named_sibling
        while sibling is not None and sibling.type in ("line_comment", "block_comment", "attribute_item"):
            comment = sibling.text.decode()
            if comment.startswith(("///", "/**")):
                doc.append(comment)
            sibling = sibling.prev_named_sibling
        if not "".join(doc).strip("/* \n"):
            problems.append(f"{where}: missing doc comment")
        elif "Example" not in "".join(doc):
            problems.append(f"{where}: missing Example in doc comment")
        found[fn] = found.get(fn, 0) + 1
    for fn, count in found.items():
        if len(re.findall(rf'id="[\w-]+-{re.escape(fn)}"', html)) < count:
            problems.append(f"{path} {fn}: missing rendered entry in {page}")
    return problems


def shell_problems(where, code):
    """Report shell functions, which need a configured shdoc reference.

    :param where: Location shown in messages.
    :type where: str
    :param code: Shell code.
    :type code: str
    :returns: One message per function.
    :rtype: list[str]

    Example: ``shell_problems("run.sh", "f() { :; }")`` reports ``f``.
    """
    problems, stack = [], [BASH.parse(code.encode()).root_node]
    while stack:
        node = stack.pop()
        stack.extend(node.children)
        if node.type == "function_definition":
            fn = node.child_by_field_name("name").text.decode()
            problems.append(f"{where}: unsupported shell function {fn}; configure pinned shdoc "
                            "to document shell functions")
    return problems


def workflow_runs(value):
    """Collect every ``run`` string from a parsed workflow document.

    :param value: Parsed YAML value.
    :type value: object
    :returns: The shell scripts in document order.
    :rtype: list[str]

    Example: ``workflow_runs({"steps": [{"run": "make"}]})`` returns ``["make"]``.
    """
    if isinstance(value, dict):
        return [s for k, v in value.items() for s in ([v] if k == "run" and isinstance(v, str) else workflow_runs(v))]
    if isinstance(value, list):
        return [s for item in value for s in workflow_runs(item)]
    return []


def main():
    """Check every source file and print the problems found.

    :returns: 0 when every function is documented and rendered, otherwise 1.
    :rtype: int

    Example: ``make -f docs/source/Makefile check`` runs this function.
    """
    problems = []
    for path in source_files():
        file = Path(path)
        if not file.is_file():
            continue
        text = file.read_text(errors="replace")
        first = text.split("\n", 1)[0]
        if file.suffix == ".py" or (not file.suffix and re.match(r"#!.*python", first)):
            problems += python_problems(path, text)
        elif file.suffix == ".rs":
            problems += rust_problems(path, text)
        elif file.suffix in (".sh", ".bash") or (not file.suffix and re.match(r"#!.*\b(ba|da|z)?sh\b", first)):
            problems += shell_problems(path, text)
        elif path.startswith(".github/workflows/") and file.suffix in (".yml", ".yaml"):
            for number, script in enumerate(workflow_runs(yaml.safe_load(text)), 1):
                problems += shell_problems(f"{path} run {number}", script)
        elif file.name == "Makefile" or file.suffix == ".mk":
            recipes = "\n".join(line[1:] for line in text.splitlines() if line.startswith("\t"))
            problems += shell_problems(f"{path} recipes", recipes.replace("$$", "$"))
        elif file.suffix not in DATA_SUFFIXES and file.name not in DATA_NAMES:
            problems.append(f"{path}: unsupported source format; configure a native extractor "
                            "for its functions or list the format as data")
    for problem in problems:
        print(problem)
    print(f"Function reference coverage: {len(problems)} problems")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
