"""
Deterministic Analysis Service (v2)
Reads a Python project directory and reports:
- Number of files
- Number of classes
- Number of methods/functions
- Cloud-specific dependencies detected via:
  Layer 1: Python import analysis (AST-based)
  Layer 2: Dependency manifest scanning (requirements.txt, Pipfile, pyproject.toml)
  Layer 3: Infrastructure/config file scanning (serverless.yml, Dockerfile, .env, *.json)
  Layer 4: String literal scanning (cloud URLs, ARNs, SDK patterns in source code)

This is the deterministic layer that Claude Code calls
for reliable, repeatable analysis. Each detection layer
functions as an architectural fitness function (Ford et al. 2017)
for dependency elimination.
"""

import ast
import os
import re
import sys
import json


# --- Cloud detection rules ---

# Layer 1: Python import indicators
IMPORT_INDICATORS = {
    "boto3": "AWS SDK",
    "botocore": "AWS SDK (low-level)",
    "moto": "AWS Mock (test dependency)",
    "aws_cdk": "AWS CDK",
    "aws_lambda_powertools": "AWS Lambda Powertools",
    "google.cloud": "Google Cloud SDK",
    "azure": "Azure SDK",
    "azure.storage": "Azure Storage",
    "azure.cosmos": "Azure CosmosDB",
}

# Layer 2: Dependency manifest packages
PACKAGE_INDICATORS = {
    "boto3": "AWS SDK",
    "botocore": "AWS SDK (low-level)",
    "moto": "AWS Mock (test dependency)",
    "aws-cdk-lib": "AWS CDK",
    "aws-lambda-powertools": "AWS Lambda Powertools",
    "awscli": "AWS CLI",
    "google-cloud-storage": "Google Cloud Storage",
    "google-cloud-firestore": "Google Cloud Firestore",
    "azure-storage-blob": "Azure Blob Storage",
    "azure-cosmos": "Azure CosmosDB",
    "azure-functions": "Azure Functions",
}

# Layer 3: Config/infra file indicators (substring match on file content)
CONFIG_INDICATORS = {
    "provider:\n  name: aws": "AWS Serverless Framework",
    "provider:\n  name: gcp": "GCP Serverless Framework",
    "provider:\n  name: azure": "Azure Serverless Framework",
    "AWS::DynamoDB": "AWS DynamoDB (CloudFormation)",
    "AWS::Lambda": "AWS Lambda (CloudFormation)",
    "AWS::S3": "AWS S3 (CloudFormation)",
    "arn:aws:": "AWS ARN reference",
    "amazonaws.com": "AWS endpoint URL",
    "DYNAMODB_TABLE": "DynamoDB table reference",
    "LOCALSTACK_HOSTNAME": "LocalStack (AWS emulation)",
}

# Layer 4: String literal / source patterns (regex)
SOURCE_PATTERNS = [
    (re.compile(r'arn:aws:[a-z0-9\-]+:[a-z0-9\-]*:\d*:'), "AWS ARN"),
    (re.compile(r'\.amazonaws\.com'), "AWS endpoint URL"),
    (re.compile(r'dynamodb\.(?:Table|resource|client)'), "DynamoDB SDK call"),
    (re.compile(r'boto3\.(client|resource|Session)'), "AWS SDK call"),
    (re.compile(r's3\.(?:Bucket|Object|upload_file|download_file)'), "S3 SDK call"),
    (re.compile(r'sqs\.(?:send_message|receive_message|Queue)'), "SQS SDK call"),
    (re.compile(r'LOCALSTACK_HOSTNAME'), "LocalStack reference"),
    (re.compile(r'storage\.googleapis\.com'), "Google Cloud Storage URL"),
    (re.compile(r'\.blob\.core\.windows\.net'), "Azure Blob Storage URL"),
]

# Config file extensions to scan
CONFIG_EXTENSIONS = {
    ".yml", ".yaml", ".json", ".env", ".cfg", ".ini", ".toml",
    ".tf", ".hcl",  # Terraform
}

# Config filenames (exact match, case-insensitive)
CONFIG_FILENAMES = {
    "dockerfile", "docker-compose.yml", "docker-compose.yaml",
    "serverless.yml", "serverless.yaml",
    "template.yaml", "template.yml",  # AWS SAM
    "pipfile", "pyproject.toml",
}


def scan_requirements(filepath):
    """Layer 2: Scan a requirements.txt / Pipfile for cloud packages."""
    deps = []
    try:
        with open(filepath, "r") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                # Extract package name (before any version specifier)
                pkg = re.split(r'[>=<!\[\];]', line)[0].strip().lower()
                for indicator, service in PACKAGE_INDICATORS.items():
                    if pkg == indicator.lower():
                        deps.append({
                            "file": os.path.basename(filepath),
                            "line": line_num,
                            "package": line.strip(),
                            "service": service,
                            "layer": "dependency_manifest",
                        })
    except (FileNotFoundError, UnicodeDecodeError):
        pass
    return deps


def scan_config_file(filepath, relative_path):
    """Layer 3: Scan config/infra files for cloud indicators."""
    deps = []
    try:
        with open(filepath, "r") as f:
            content = f.read()
        for indicator, service in CONFIG_INDICATORS.items():
            if indicator in content:
                deps.append({
                    "file": relative_path,
                    "pattern": indicator,
                    "service": service,
                    "layer": "config_file",
                })
    except (FileNotFoundError, UnicodeDecodeError):
        pass
    return deps


def scan_source_strings(source, relative_path):
    """Layer 4: Scan Python source for cloud URLs, ARNs, SDK patterns."""
    deps = []
    for pattern, service in SOURCE_PATTERNS:
        matches = pattern.findall(source)
        if matches:
            deps.append({
                "file": relative_path,
                "pattern": pattern.pattern,
                "matches": len(matches),
                "service": service,
                "layer": "source_string",
            })
    return deps


def analyze_directory(path):
    """Analyze all files in a directory using all four detection layers."""
    results = {
        "path": path,
        "total_files": 0,
        "python_files": 0,
        "config_files_scanned": 0,
        "classes": [],
        "functions": [],
        "imports": [],
        "cloud_dependencies": [],
        "cloud_dependencies_by_layer": {
            "python_import": [],
            "dependency_manifest": [],
            "config_file": [],
            "source_string": [],
        },
        "files": [],
    }

    for root, dirs, files in os.walk(path):
        # Skip hidden dirs and __pycache__
        dirs[:] = [d for d in dirs if not d.startswith(".") and d != "__pycache__"]

        for filename in files:
            results["total_files"] += 1
            filepath = os.path.join(root, filename)
            relative_path = os.path.relpath(filepath, path)
            fname_lower = filename.lower()
            _, ext = os.path.splitext(fname_lower)

            # --- Layer 2: Dependency manifest scanning ---
            if fname_lower in ("requirements.txt", "requirements-dev.txt",
                               "requirements_dev.txt", "requirements.in"):
                manifest_deps = scan_requirements(filepath)
                for dep in manifest_deps:
                    dep["file"] = relative_path
                    results["cloud_dependencies"].append(dep)
                    results["cloud_dependencies_by_layer"]["dependency_manifest"].append(dep)

            # --- Layer 3: Config/infra file scanning ---
            if ext in CONFIG_EXTENSIONS or fname_lower in CONFIG_FILENAMES:
                results["config_files_scanned"] += 1
                config_deps = scan_config_file(filepath, relative_path)
                for dep in config_deps:
                    results["cloud_dependencies"].append(dep)
                    results["cloud_dependencies_by_layer"]["config_file"].append(dep)

            # Only do Python-specific analysis on .py files
            if not filename.endswith(".py"):
                continue

            results["python_files"] += 1

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

                # --- Layer 1: Python import analysis ---
                for imp in file_info["imports"]:
                    for indicator, service in IMPORT_INDICATORS.items():
                        if indicator in imp.lower():
                            dep = {
                                "file": relative_path,
                                "import": imp,
                                "service": service,
                                "layer": "python_import",
                            }
                            file_info["cloud_dependencies"].append(dep)
                            results["cloud_dependencies"].append(dep)
                            results["cloud_dependencies_by_layer"]["python_import"].append(dep)

                # --- Layer 4: String literal / source pattern scanning ---
                source_deps = scan_source_strings(source, relative_path)
                for dep in source_deps:
                    file_info["cloud_dependencies"].append(dep)
                    results["cloud_dependencies"].append(dep)
                    results["cloud_dependencies_by_layer"]["source_string"].append(dep)

            except (SyntaxError, FileNotFoundError) as e:
                file_info["error"] = str(e)

            results["files"].append(file_info)

    return results


def print_summary(results):
    """Print a human-readable summary."""
    print(f"\n{'='*60}")
    print(f"  ANALYSIS: {results['path']}")
    print(f"{'='*60}")
    print(f"  Total files:       {results['total_files']}")
    print(f"  Python files:      {results['python_files']}")
    print(f"  Config files:      {results.get('config_files_scanned', 0)}")
    print(f"  Classes:           {len(results['classes'])}")
    print(f"  Functions:         {len(results['functions'])}")
    print(f"  Imports:           {len(results['imports'])}")
    total_deps = len(results['cloud_dependencies'])
    print(f"  Cloud deps:        {total_deps}")
    print(f"{'='*60}")

    if total_deps > 0:
        by_layer = results.get("cloud_dependencies_by_layer", {})
        print(f"\n  CLOUD DEPENDENCIES BY DETECTION LAYER:")
        for layer_name, layer_deps in by_layer.items():
            if layer_deps:
                print(f"\n    [{layer_name.upper()}] ({len(layer_deps)} finding(s))")
                for dep in layer_deps:
                    if "import" in dep:
                        print(f"      - {dep['file']}: import {dep['import']} ({dep['service']})")
                    elif "package" in dep:
                        print(f"      - {dep['file']}: {dep['package']} ({dep['service']})")
                    elif "pattern" in dep:
                        detail = f"matches={dep['matches']}" if "matches" in dep else ""
                        print(f"      - {dep['file']}: {dep['service']} {detail}")
    else:
        print(f"\n  NO CLOUD DEPENDENCIES DETECTED (all 4 layers clean)")

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