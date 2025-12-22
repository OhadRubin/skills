#!/usr/bin/env python3
"""
Split large Python modules into packages.

Usage:
    python split_module.py parse <file.py>
    python split_module.py split <file.py> <groupings.json> <module> <Name1> <Name2> ...
"""

import argparse
import json
import subprocess
import sys
import shutil
from pathlib import Path


def run_ast_grep(pattern: str, file_path: str) -> list:
    result = subprocess.run(
        ["ast-grep", "--pattern", pattern, "--json", "-l", "python", file_path],
        capture_output=True,
        text=True,
    )
    if not result.stdout.strip():
        return []
    return json.loads(result.stdout)


def parse_definitions(file_path: str) -> list[dict]:
    """Extract all top-level definitions from a Python file."""
    definitions = []
    seen_classes = set()

    # Classes with single inheritance: class Foo(Bar):
    for r in run_ast_grep("class $NAME($PARENT):\n    $$$BODY", file_path):
        name = r["metaVariables"]["single"]["NAME"]["text"]
        parent = r["metaVariables"]["single"]["PARENT"]["text"]
        seen_classes.add(name)
        definitions.append({
            "name": name,
            "kind": "class",
            "start": r["range"]["start"]["line"],
            "end": r["range"]["end"]["line"],
            "parent": parent,
        })

    # Classes with multiple inheritance: class Foo(Bar, Baz, ...):
    for r in run_ast_grep("class $NAME($PARENT, $$$REST):\n    $$$BODY", file_path):
        name = r["metaVariables"]["single"]["NAME"]["text"]
        if name in seen_classes:
            continue
        parent = r["metaVariables"]["single"]["PARENT"]["text"]
        seen_classes.add(name)
        definitions.append({
            "name": name,
            "kind": "class",
            "start": r["range"]["start"]["line"],
            "end": r["range"]["end"]["line"],
            "parent": parent,
        })

    # Classes without inheritance: class Foo:
    for r in run_ast_grep("class $NAME:\n    $$$BODY", file_path):
        name = r["metaVariables"]["single"]["NAME"]["text"]
        if name in seen_classes:
            continue
        seen_classes.add(name)
        definitions.append({
            "name": name,
            "kind": "class",
            "start": r["range"]["start"]["line"],
            "end": r["range"]["end"]["line"],
            "parent": None,
        })
    
    # Functions with return type
    for r in run_ast_grep("def $NAME($$$ARGS) -> $RET:\n    $$$BODY", file_path):
        if r["range"]["start"]["column"] != 0:
            continue
        definitions.append({
            "name": r["metaVariables"]["single"]["NAME"]["text"],
            "kind": "function",
            "start": r["range"]["start"]["line"],
            "end": r["range"]["end"]["line"],
        })
    
    # Functions without return type
    seen = {d["name"] for d in definitions if d["kind"] == "function"}
    for r in run_ast_grep("def $NAME($$$ARGS):\n    $$$BODY", file_path):
        if r["range"]["start"]["column"] != 0:
            continue
        name = r["metaVariables"]["single"]["NAME"]["text"]
        if name in seen:
            continue
        definitions.append({
            "name": name,
            "kind": "function",
            "start": r["range"]["start"]["line"],
            "end": r["range"]["end"]["line"],
        })
    
    # Filter nested classes
    classes = [d for d in definitions if d["kind"] == "class"]
    nested = {
        c["name"] for c in classes
        for other in classes
        if other["name"] != c["name"] and other["start"] < c["start"] < other["end"]
    }
    definitions = [d for d in definitions if d["name"] not in nested]
    definitions.sort(key=lambda d: d["start"])
    
    return definitions


def cmd_parse(file_path: str):
    """Print definitions JSON to stdout."""
    print(json.dumps(parse_definitions(file_path), indent=2))


def cmd_write(file_path: str, groupings_path: str):
    """
    Write split files based on groupings JSON.
    
    Groupings format:
    {
        "base": ["ClassName", "func_name"],
        "groups": {
            "group_name": ["Class1", "Class2"]
        },
        "init_extras": ["factory_func"]
    }
    """
    source = Path(file_path)
    groupings = json.loads(Path(groupings_path).read_text())
    
    output_dir = source.parent / source.stem
    lines = source.read_text().splitlines(keepends=True)
    
    # Parse to get line ranges
    definitions = {d["name"]: d for d in parse_definitions(file_path)}
    
    def extract(name):
        if name not in definitions:
            return f"# WARNING: {name} not found\n"
        d = definitions[name]
        return "".join(lines[d["start"]:d["end"] + 1])
    
    def find_imports_end():
        last_import_line = 0
        # Find all "import x" statements
        for r in run_ast_grep("import $$$NAMES", file_path):
            end_line = r["range"]["end"]["line"]
            if end_line > last_import_line:
                last_import_line = end_line
        # Find all "from x import y" statements
        for r in run_ast_grep("from $MODULE import $$$NAMES", file_path):
            end_line = r["range"]["end"]["line"]
            if end_line > last_import_line:
                last_import_line = end_line
        return last_import_line + 1
    
    # Setup
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir()
    
    imports_section = "".join(lines[:find_imports_end()])
    
    # base.py
    base_content = imports_section + "\n"
    for name in groupings.get("base", []):
        base_content += "\n" + extract(name) + "\n"
    (output_dir / "base.py").write_text(base_content)
    print(f"Wrote {output_dir / 'base.py'}")
    
    # group files
    for group_name, members in groupings.get("groups", {}).items():
        content = f'"""Module for {group_name}."""\n\nfrom .base import *\n\n'
        for name in sorted(members, key=lambda n: definitions.get(n, {}).get("start", 0)):
            content += extract(name) + "\n\n"
        (output_dir / f"{group_name}.py").write_text(content)
        print(f"Wrote {output_dir / group_name}.py")
    
    # __init__.py
    init_content = f'"""{source.stem} package."""\n\nfrom .base import *\n'
    for group_name in groupings.get("groups", {}):
        init_content += f"from .{group_name} import *\n"
    for name in groupings.get("init_extras", []):
        init_content += "\n" + extract(name) + "\n"
    (output_dir / "__init__.py").write_text(init_content)
    print(f"Wrote {output_dir / '__init__.py'}")
    
    # Convert original to re-export stub
    module_import = f"{source.parent.name}.{source.stem}"
    source.write_text(f'"""Re-export for backwards compatibility."""\n\nfrom {module_import} import *\n')
    print(f"Updated {source} → re-export stub")


def get_backup_path(file_path: str) -> Path:
    """Get the backup file path for a source file."""
    source = Path(file_path)
    return source.parent / f".{source.name}.backup"


def cmd_backup(file_path: str):
    """Save a backup of the original file."""
    source = Path(file_path)
    backup = get_backup_path(file_path)
    shutil.copy2(source, backup)
    print(f"Backed up {source} → {backup}")


def cmd_rollback(file_path: str):
    """Restore original file from backup (or git) and remove package directory."""
    source = Path(file_path)
    output_dir = source.parent / source.stem
    backup = get_backup_path(file_path)

    # Try backup first, then git
    if backup.exists():
        shutil.copy2(backup, source)
        backup.unlink()
        print(f"Restored {source} from backup")
    else:
        result = subprocess.run(
            ["git", "checkout", str(source)],
            cwd=source.parent,
            capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"No backup found and git checkout failed: {result.stderr}", file=sys.stderr)
            sys.exit(1)
        print(f"Restored {source} from git")

    if output_dir.exists():
        shutil.rmtree(output_dir)
        print(f"Removed {output_dir}/")


def cmd_test_imports(module: str, *names: str):
    """Test that names can be imported from module."""
    import_stmt = f"from {module} import {', '.join(names)}"
    result = subprocess.run(
        [sys.executable, "-c", import_stmt],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"FAIL: {import_stmt}", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        sys.exit(1)
    print(f"OK: {import_stmt}")


def main():
    parser = argparse.ArgumentParser(description="Split Python modules into packages")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # parse command
    parse_cmd = subparsers.add_parser("parse", help="Parse and print definitions")
    parse_cmd.add_argument("file", help="Python file to parse")

    # split command
    split_cmd = subparsers.add_parser("split", help="Split file using groupings, test imports, rollback on failure")
    split_cmd.add_argument("file", help="Python file to split")
    split_cmd.add_argument("groupings", help="Path to groupings.json")
    split_cmd.add_argument("module", help="Module path for import test (e.g. package.module)")
    split_cmd.add_argument("names", nargs="+", help="Names to test importing")

    args = parser.parse_args()

    if args.command == "parse":
        cmd_parse(args.file)
    elif args.command == "split":
        cmd_backup(args.file)
        cmd_write(args.file, args.groupings)
        try:
            cmd_test_imports(args.module, *args.names)
        except SystemExit:
            cmd_rollback(args.file)
            raise
        else:
            # Success - clean up backup
            backup = get_backup_path(args.file)
            if backup.exists():
                backup.unlink()
                print(f"Removed backup {backup}")


if __name__ == "__main__":
    main()
