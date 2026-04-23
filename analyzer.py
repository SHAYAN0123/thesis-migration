"""
Deterministic Analysis Service
Reads a Python project directory and reports:
- Number of files
- Number of classes
- Number of methods/functions
- Cloud-specific dependencies (boto3, AWS SDK calls)
- Imports used

This is the deterministic layer that Claude Code calls
for reliable, repeatable analysis.
"""

import ast
import os
import sys
import json


def analyze_directory(path):
    """Analyze all Python files in a directory."""
    results = {
        "path": path,
        "total_files": 0,
        "python_files": 0,
        "classes": [],
        "functions": [],
        "imports": [],
        "cloud_dependencies": [],
        "files": [],
    }

    cloud_indicators = {
        "boto3": "AWS SDK",
        "botocore": "AWS SDK (low-level)",
        "dynamodb": "AWS DynamoDB",
        "s3": "AWS S3",
        "sqs": "AWS SQS",
        "lambda": "AWS Lambda",
        "cloudformation": "AWS CloudFormation",
        "aws": "AWS (general)",
    }

    for root, dirs, files in os.walk(path):
        # Skip hidden dirs and __pycache__
        dirs[:] = [d for d in dirs if not d.startswith(".") and d != "__pycache__"]

        for filename in files:
            results["total_files"] += 1
            if not filename.endswith(".py"):
                continue

            results["python_files"] += 1
            filepath = os.path.join(root, filename)
            relative_path = os.path.relpath(filepath, path)

            file_info = {
                "path": relative_path,
                "classes": [],
                "functions": [],
                "imports": [],
                "cloud_dependencies": [],
            }

            try:
                with open(filepath, "r") as f:
                    source = f.read()
                tree = ast.parse(source)

                for node in ast.walk(tree):
                    # Classes
                    if isinstance(node, ast.ClassDef):
                        methods = [
                            n.name
                            for n in node.body
                            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                        ]
                        class_info = {"name": node.name, "methods": methods}
                        file_info["classes"].append(class_info)
                        results["classes"].append(
                            {"file": relative_path, **class_info}
                        )

                    # Top-level functions
                    elif isinstance(node, ast.FunctionDef) or isinstance(
                        node, ast.AsyncFunctionDef
                    ):
                        # Only top-level (not methods inside classes)
                        if hasattr(node, "col_offset") and node.col_offset == 0:
                            file_info["functions"].append(node.name)
                            results["functions"].append(
                                {"file": relative_path, "name": node.name}
                            )

                    # Imports
                    elif isinstance(node, ast.Import):
                        for alias in node.names:
                            file_info["imports"].append(alias.name)
                            results["imports"].append(
                                {"file": relative_path, "module": alias.name}
                            )

                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            file_info["imports"].append(node.module)
                            results["imports"].append(
                                {"file": relative_path, "module": node.module}
                            )

                # Check for cloud dependencies
                for imp in file_info["imports"]:
                    for indicator, service in cloud_indicators.items():
                        if indicator in imp.lower():
                            dep = {
                                "file": relative_path,
                                "import": imp,
                                "service": service,
                            }
                            file_info["cloud_dependencies"].append(dep)
                            results["cloud_dependencies"].append(dep)

            except (SyntaxError, FileNotFoundError) as e:
                file_info["error"] = str(e)

            results["files"].append(file_info)

    return results


def print_summary(results):
    """Print a human-readable summary."""
    print(f"\n{'='*60}")
    print(f"  ANALYSIS: {results['path']}")
    print(f"{'='*60}")
    print(f"  Total files:    {results['total_files']}")
    print(f"  Python files:   {results['python_files']}")
    print(f"  Classes:        {len(results['classes'])}")
    print(f"  Functions:      {len(results['functions'])}")
    print(f"  Imports:        {len(results['imports'])}")
    print(f"  Cloud deps:     {len(results['cloud_dependencies'])}")
    print(f"{'='*60}")

    if results["cloud_dependencies"]:
        print(f"\n  CLOUD DEPENDENCIES (lock-in points):")
        for dep in results["cloud_dependencies"]:
            print(f"    - {dep['file']}: {dep['import']} ({dep['service']})")

    if results["functions"]:
        print(f"\n  FUNCTIONS:")
        for fn in results["functions"]:
            print(f"    - {fn['file']}: {fn['name']}()")

    if results["classes"]:
        print(f"\n  CLASSES:")
        for cls in results["classes"]:
            methods = ", ".join(cls["methods"]) if cls["methods"] else "none"
            print(f"    - {cls['file']}: {cls['name']} [{methods}]")

    print()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyzer.py <directory> [--json]")
        sys.exit(1)

    target = sys.argv[1]
    use_json = "--json" in sys.argv

    if not os.path.isdir(target):
        print(f"Error: {target} is not a directory")
        sys.exit(1)

    results = analyze_directory(target)

    if use_json:
        print(json.dumps(results, indent=2))
    else:
        print_summary(results)