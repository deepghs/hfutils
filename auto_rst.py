"""
This module provides functionality to extract public members (classes, functions, variables) from Python source code
and generate reStructuredText (RST) documentation files for Sphinx.

The module uses AST (Abstract Syntax Tree) parsing to analyze Python code and identify public members,
then generates RST files with appropriate Sphinx directives for documentation generation.
"""

import argparse
import ast
import os
import pathlib
import re
from io import StringIO
from typing import List, Dict, Any

from natsort import natsorted


_RST_SYMBOLS_RE = re.compile(r"([!-\-/:-@\[-`{-~])")


def _escape_rst(text: str) -> str:
    """Escape RST text without making Sphinx a test-time import requirement."""
    try:
        from sphinx.util.rst import escape
    except ModuleNotFoundError as err:
        # ``sphinx`` is a documentation-only dependency; its absence must not
        # prevent the source-level RST generator regression tests from running.
        if err.name != "sphinx":
            raise
        escaped = _RST_SYMBOLS_RE.sub(r"\\\1", text)
        return re.sub(r"^\.", r"\.", escaped)
    return escape(text)


_RST_MEMBER_TITLE_MIN_WIDTH = 53


def normalize_rst_document(text: str) -> str:
    """
    Normalize generated reStructuredText document endings.

    The generator intentionally keeps exactly one final newline for non-empty
    documents while removing blank lines at the end. This keeps regenerated
    API documentation stable and prevents ``make rst_auto`` from creating
    trailing-empty-line churn.

    :param text: Raw generated RST text.
    :type text: str
    :return: Normalized RST text.
    :rtype: str

    Example::

        >>> normalize_rst_document("Title\\n=====\\n\\n\\n")
        'Title\\n=====\\n'
        >>> normalize_rst_document("")
        ''
    """
    stripped = text.rstrip()
    if stripped:
        return f"{stripped}\n"
    return ""


def rst_to_text(text: str) -> str:
    """
    Escape text for use in reStructuredText format.

    :param text: The text to escape.
    :type text: str

    :return: The escaped text safe for RST.
    :rtype: str
    """
    return _escape_rst(text)


class PublicMemberExtractor(ast.NodeVisitor):
    """
    Extract public members (classes, functions, variables) from Python code.

    This class uses AST node visiting to traverse Python code and identify
    public classes, functions, and variables, excluding private and protected
    members. Same-module protected mixin bases remain available as inheritance
    sources for public subclasses.

    :param class_index: Top-level classes keyed by name, defaults to ``None``.
    :type class_index: Dict[str, ast.ClassDef], optional

    Example::

        >>> tree = ast.parse('class Visible:\\n    def run(self):\\n        pass\\n')
        >>> extractor = PublicMemberExtractor({'Visible': tree.body[0]})
        >>> extractor.visit(tree)
        >>> extractor.public_classes[0]['name']
        'Visible'
    """

    def __init__(self, class_index=None):
        """
        Initialize the PublicMemberExtractor.

        Sets up empty lists to store extracted public classes, functions, and
        variables, plus the same-module class index used for inheritance.

        :param class_index: Top-level classes keyed by name, defaults to
            ``None``.
        :type class_index: Dict[str, ast.ClassDef], optional
        :return: ``None``.
        :rtype: None

        Example::

            >>> extractor = PublicMemberExtractor()
            >>> extractor.public_classes
            []
        """
        self.public_classes = []
        self.public_functions = []
        self.public_variables = []
        self.class_index = dict(class_index or {})

    @classmethod
    def is_private(cls, name: str) -> bool:
        """
        Determine if a name represents a private member (starts with double underscore).

        :param name: The member name to check.
        :type name: str

        :return: True if the name is private, False otherwise.
        :rtype: bool
        """
        return name.startswith("__") and not (
            name.startswith("__") and name.endswith("__")
        )

    @classmethod
    def is_protected(cls, name: str) -> bool:
        """
        Determine if a name represents a protected member (starts with single underscore).

        :param name: The member name to check.
        :type name: str

        :return: True if the name is protected, False otherwise.
        :rtype: bool
        """
        return name.startswith("_") and not name.startswith("__")

    @classmethod
    def is_magic_method(cls, name: str) -> bool:
        """
        Determine if a name represents a magic method (starts and ends with double underscore).

        :param name: The member name to check.
        :type name: str

        :return: True if the name is a magic method, False otherwise.
        :rtype: bool
        """
        return name.startswith("__") and name.endswith("__") and len(name) > 4

    @classmethod
    def is_public_or_magic(cls, name: str) -> bool:
        """
        Determine if a name represents a public member or magic method.

        :param name: The member name to check.
        :type name: str

        :return: True if the name is public or a magic method, False otherwise.
        :rtype: bool
        """
        return (
            not cls.is_private(name)
            and not cls.is_protected(name)
            or cls.is_magic_method(name)
        )

    def extract_class_members(
        self, node: ast.ClassDef, inherited_from=()
    ) -> Dict[str, Any]:
        """
        Extract public members and magic methods from a class definition.

        :param node: The class definition AST node.
        :type node: ast.ClassDef
        :param inherited_from: Same-module base names already visited while
            resolving this inheritance chain, defaults to ``()``.
        :type inherited_from: Tuple[str, ...], optional
        :return: Dictionary containing 'methods' and 'attributes' lists. Direct
            members precede inherited members and override them by name.
        :rtype: Dict[str, Any]

        Example::

            >>> tree = ast.parse('class Item:\\n    value = 1\\n    def run(self):\\n        pass\\n')
            >>> extractor = PublicMemberExtractor({'Item': tree.body[0]})
            >>> members = extractor.extract_class_members(tree.body[0])
            >>> [item['name'] for item in members['methods']]
            ['run']
            >>> [item['name'] for item in members['attributes']]
            ['value']
        """
        methods = []
        attributes = []

        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                if self.is_public_or_magic(item.name):
                    method_info = {
                        "name": item.name,
                        "type": "method",
                        "args": self.extract_function_args(item),
                        "decorators": [
                            self.get_decorator_name(dec) for dec in item.decorator_list
                        ],
                        "docstring": ast.get_docstring(item),
                        "lineno": item.lineno,
                        "is_magic": self.is_magic_method(item.name),
                    }
                    methods.append(method_info)

            elif isinstance(item, ast.Assign):
                # Extract class variables
                for target in item.targets:
                    if isinstance(target, ast.Name) and self.is_public_or_magic(
                        target.id
                    ):
                        attr_info = {
                            "name": target.id,
                            "type": "class_variable",
                            "lineno": item.lineno,
                            "value": self.get_node_source(item.value)
                            if hasattr(item, "value")
                            else None,
                        }
                        attributes.append(attr_info)

            elif isinstance(item, ast.AnnAssign):
                # Extract annotated class variables
                if isinstance(item.target, ast.Name) and self.is_public_or_magic(
                    item.target.id
                ):
                    attr_info = {
                        "name": item.target.id,
                        "type": "annotated_variable",
                        "annotation": self.get_node_source(item.annotation),
                        "lineno": item.lineno,
                        "value": self.get_node_source(item.value)
                        if item.value
                        else None,
                    }
                    attributes.append(attr_info)

        method_names = {item["name"] for item in methods}
        attribute_names = {item["name"] for item in attributes}
        visited = set(inherited_from)
        visited.add(node.name)
        for base in node.bases:
            base_name = self.get_node_source(base)
            base_node = self.class_index.get(base_name)
            if (
                base_node is None
                or base_name in visited
                or not self.is_protected(base_name)
                or not base_name.endswith("Mixin")
            ):
                continue
            inherited = self.extract_class_members(base_node, tuple(visited))
            for method in inherited["methods"]:
                if method["name"] not in method_names:
                    methods.append(method)
                    method_names.add(method["name"])
            for attribute in inherited["attributes"]:
                if attribute["name"] not in attribute_names:
                    attributes.append(attribute)
                    attribute_names.add(attribute["name"])

        return {"methods": methods, "attributes": attributes}

    def extract_function_args(self, node: ast.FunctionDef) -> List[str]:
        """
        Extract function parameter names.

        :param node: The function definition AST node.
        :type node: ast.FunctionDef

        :return: List of parameter names including *args and **kwargs.
        :rtype: List[str]
        """
        args = []

        # Regular parameters
        for arg in node.args.args:
            args.append(arg.arg)

        # *args
        if node.args.vararg:
            args.append(f"*{node.args.vararg.arg}")

        # **kwargs
        if node.args.kwarg:
            args.append(f"**{node.args.kwarg.arg}")

        return args

    def get_decorator_name(self, decorator) -> str:
        """
        Get the name of a decorator.

        :param decorator: The decorator AST node.

        :return: String representation of the decorator name.
        :rtype: str
        """
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Attribute):
            return f"{self.get_node_source(decorator.value)}.{decorator.attr}"
        else:
            return self.get_node_source(decorator)

    def get_node_source(self, node) -> str:
        """
        Get the source code representation of an AST node.

        :param node: The AST node to convert to source code.

        :return: String representation of the node's source code.
        :rtype: str
        """
        try:
            if isinstance(node, ast.Name):
                return node.id
            elif isinstance(node, ast.Constant):
                return repr(node.value)
            elif isinstance(node, ast.Attribute):
                return f"{self.get_node_source(node.value)}.{node.attr}"
            elif isinstance(node, ast.List):
                elements = [self.get_node_source(elt) for elt in node.elts]
                return f"[{', '.join(elements)}]"
            elif isinstance(node, ast.Dict):
                pairs = []
                for k, v in zip(node.keys, node.values):
                    key = self.get_node_source(k) if k else None
                    value = self.get_node_source(v)
                    pairs.append(f"{key}: {value}" if key else f"**{value}")
                return f"{{{', '.join(pairs)}}}"
            else:
                # For complex expressions, return type information
                return f"<{type(node).__name__}>"
        except (AttributeError, TypeError, ValueError):
            # AttributeError: an unexpected AST node shape is missing a field
            # accessed by one of the branches above.
            # TypeError/ValueError: defensive fallback for malformed AST-like
            # values passed into this best-effort source formatter.
            return "<unknown>"

    def visit_ClassDef(self, node: ast.ClassDef):
        """
        Visit a class definition node.

        :param node: The class definition AST node.
        :type node: ast.ClassDef
        """
        if self.is_public_or_magic(node.name):
            # Only process top-level public classes
            class_info = {
                "name": node.name,
                "type": "class",
                "bases": [self.get_node_source(base) for base in node.bases],
                "decorators": [
                    self.get_decorator_name(dec) for dec in node.decorator_list
                ],
                "docstring": ast.get_docstring(node),
                "lineno": node.lineno,
                "members": self.extract_class_members(node),
            }
            self.public_classes.append(class_info)

        # Don't recursively visit nested classes

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """
        Visit a function definition node.

        :param node: The function definition AST node.
        :type node: ast.FunctionDef
        """
        if self.is_public_or_magic(node.name):
            # Only process top-level public functions
            func_info = {
                "name": node.name,
                "type": "function",
                "args": self.extract_function_args(node),
                "decorators": [
                    self.get_decorator_name(dec) for dec in node.decorator_list
                ],
                "docstring": ast.get_docstring(node),
                "lineno": node.lineno,
                "returns": self.get_node_source(node.returns) if node.returns else None,
            }
            self.public_functions.append(func_info)

        # self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign):
        """
        Visit an assignment statement (variable definition).

        :param node: The assignment AST node.
        :type node: ast.Assign
        """
        # Only process top-level variables
        for target in node.targets:
            if isinstance(target, ast.Name) and self.is_public_or_magic(target.id):
                var_info = {
                    "name": target.id,
                    "type": "variable",
                    "lineno": node.lineno,
                    "value": self.get_node_source(node.value),
                }
                self.public_variables.append(var_info)

        # self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign):
        """
        Visit an annotated assignment statement.

        :param node: The annotated assignment AST node.
        :type node: ast.AnnAssign
        """
        if isinstance(node.target, ast.Name) and self.is_public_or_magic(
            node.target.id
        ):
            var_info = {
                "name": node.target.id,
                "type": "annotated_variable",
                "annotation": self.get_node_source(node.annotation),
                "lineno": node.lineno,
                "value": self.get_node_source(node.value) if node.value else None,
            }
            self.public_variables.append(var_info)

        # self.generic_visit(node)


def extract_public_members(source_code: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Extract public members from Python source code.

    :param source_code: Python source code string.
    :type source_code: str

    :return: Dictionary containing 'classes', 'functions', and 'variables' keys.
    :rtype: Dict[str, List[Dict[str, Any]]]

    Example::
        >>> code = "def public_func(): pass"
        >>> result = extract_public_members(code)
        >>> 'functions' in result
        True
    """
    tree = ast.parse(source_code)
    class_index = {
        node.name: node for node in tree.body if isinstance(node, ast.ClassDef)
    }
    extractor = PublicMemberExtractor(class_index)
    extractor.visit(tree)

    source_lines = source_code.splitlines()
    for variable in extractor.public_variables:
        metadata = []
        line_index = variable["lineno"] - 2
        while line_index >= 0:
            comment = source_lines[line_index].lstrip()
            if not comment.startswith("#:"):
                break
            metadata.append(comment[2:].strip())
            line_index -= 1
        variable["hide_value"] = ":meta hide-value:" in metadata

    return {
        "classes": extractor.public_classes,
        "functions": extractor.public_functions,
        "variables": extractor.public_variables,
    }


def extract_public_members_from_file(file_path: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Extract public members from a Python file.

    :param file_path: Path to the Python file.
    :type file_path: str

    :return: Dictionary containing 'classes', 'functions', and 'variables' keys.
    :rtype: Dict[str, List[Dict[str, Any]]]
    """
    with open(file_path, "r", encoding="utf-8") as f:
        source_code = f.read()
    return extract_public_members(source_code)


def print_extracted_members(f, members: Dict[str, List[Dict[str, Any]]]):
    """
    Print extracted member information in RST format.

    :param f: File object to write to.
    :param members: Dictionary containing extracted members.
    :type members: Dict[str, List[Dict[str, Any]]]
    """

    for var in members["variables"]:
        title = rst_to_text(var["name"])
        print(title, file=f)
        print("-" * max(_RST_MEMBER_TITLE_MIN_WIDTH, len(title)), file=f)
        print("", file=f)
        print(f".. autodata:: {var['name']}", file=f)
        if var.get("hide_value"):
            print("   :no-value:", file=f)
        print("", file=f)
        print("", file=f)

    for cls in members["classes"]:
        title = rst_to_text(cls["name"])
        print(title, file=f)
        print("-" * max(_RST_MEMBER_TITLE_MIN_WIDTH, len(title)), file=f)
        print("", file=f)
        print(f".. autoclass:: {cls['name']}", file=f)
        member_names = []
        for method in cls["members"]["methods"]:
            member_names.append(method["name"])
        for attr in cls["members"]["attributes"]:
            member_names.append(attr["name"])
        if member_names:
            print(f"    :members: {','.join(member_names)}", file=f)
        print("", file=f)
        print("", file=f)

    for func in members["functions"]:
        title = rst_to_text(func["name"])
        print(title, file=f)
        print("-" * max(_RST_MEMBER_TITLE_MIN_WIDTH, len(title)), file=f)
        print("", file=f)
        print(f".. autofunction:: {func['name']}", file=f)
        print("", file=f)
        print("", file=f)


def print_package_toctree(f, code_file: str):
    """
    Print the package-level toctree for an ``__init__.py`` module.

    :param f: File object to write to.
    :param code_file: Path to the ``__init__.py`` file of the package.
    :type code_file: str
    :return: ``None``.
    :rtype: None
    """
    code_rels = []
    for code_rel_file in os.listdir(os.path.dirname(code_file)):
        code_rel_base = os.path.splitext(code_rel_file)[0]
        code_abs_file = os.path.abspath(
            os.path.join(os.path.dirname(code_file), code_rel_file)
        )
        if (
            os.path.isfile(code_abs_file)
            and code_rel_file.endswith(".py")
            and not (code_rel_base.startswith("__") and code_rel_base.endswith("__"))
            and code_rel_file != "build_info.py"
            and not code_rel_base.startswith("_")
        ):
            code_rels.append(code_rel_base)
        elif os.path.isdir(code_abs_file) and os.path.exists(
            os.path.join(code_abs_file, "__init__.py")
        ):
            code_rels.append(f"{code_rel_base}/index")

    if code_rels:
        code_rels = natsorted(code_rels)
        print(".. toctree::", file=f)
        print("    :maxdepth: 3", file=f)
        print("", file=f)
        for code_rel_base in code_rels:
            print(f"    {code_rel_base}", file=f)
        print("", file=f)


def convert_code_to_rst(code_file: str, rst_file: str, lib_dir: str = "."):
    """
    Convert a Python code file to an RST documentation file.

    :param code_file: Path to the Python source code file.
    :type code_file: str
    :param rst_file: Path to the output RST file.
    :type rst_file: str
    :param lib_dir: Base library directory for calculating relative module paths. Defaults to '.'.
    :type lib_dir: str

    Example::

        >>> convert_code_to_rst('mymodule.py', 'docs/mymodule.rst', lib_dir='src')  # doctest: +SKIP
        # Generates RST documentation for mymodule.py
    """
    if os.path.dirname(rst_file):
        os.makedirs(os.path.dirname(rst_file), exist_ok=True)
    members = extract_public_members(pathlib.Path(code_file).read_text())

    with StringIO() as buffer:
        rel_file = os.path.relpath(os.path.abspath(code_file), os.path.abspath(lib_dir))
        rel_segs = os.path.splitext(rel_file)[0]
        module_name = rel_segs.replace("/", ".").replace("\\", ".")
        if module_name.split(".")[-1] == "__init__":
            module_name = ".".join(module_name.split(".")[:-1])

        module_base = os.path.splitext(os.path.basename(code_file))[0]
        is_private_module = module_base.startswith("_") and not (
            module_base.startswith("__") and module_base.endswith("__")
        )

        normalized_rel_file = rel_file.replace("\\", "/")
        is_root_package_index = (
            normalized_rel_file.endswith("/__init__.py")
            and normalized_rel_file.count("/") == 1
        )

        if is_private_module:
            # Sphinx recognizes this document metadata only before its title.
            print(":orphan:", file=buffer)
            print("", file=buffer)

        print(f"{rst_to_text(module_name)}", file=buffer)
        print("========================================================", file=buffer)
        print("", file=buffer)

        print(f".. currentmodule:: {module_name}", file=buffer)
        print("", file=buffer)
        print(f".. automodule:: {module_name}", file=buffer)
        print("", file=buffer)
        print("", file=buffer)

        if os.path.basename(code_file) == "__init__.py" and not is_root_package_index:
            print_package_toctree(buffer, code_file)

        print_extracted_members(buffer, members)
        pathlib.Path(rst_file).write_text(
            normalize_rst_document(buffer.getvalue()), encoding="utf-8"
        )


def main():
    """
    Main entry point for the command-line interface.

    Parses command-line arguments and converts a Python code file to RST documentation.
    """
    parser = argparse.ArgumentParser(
        description="Auto create rst docs for python code file"
    )
    parser.add_argument("-i", "--input", required=True, help="Input python code file")
    parser.add_argument("-o", "--output", required=True, help="Output rst doc file")
    args = parser.parse_args()

    convert_code_to_rst(code_file=args.input, rst_file=args.output, lib_dir=".")


if __name__ == "__main__":
    main()
