import json
import os.path
import shutil
import subprocess
import urllib
import urllib.parse
from typing import Any, Dict, List

import yaml

TMP_DIR_PATH = ".tmp"


def get_repos_path() -> str:
    return os.path.join(TMP_DIR_PATH, "repos")


def checkout_velocitas_repo(repo_uri) -> str:
    os.makedirs(get_repos_path(), exist_ok=True)
    repo_name = get_repo_name(repo_uri)
    repo_path = os.path.join(get_repos_path(), repo_name)

    if not os.path.exists(repo_path):
        subprocess.check_call(["git", "clone", repo_uri], cwd=get_repos_path())
    else:
        subprocess.check_call(["git", "branch", "--set-upstream-to=origin/main", "main"], cwd=repo_path)
        subprocess.check_call(["git", "pull"], cwd=repo_path)

    return repo_path


def read_package_manifest(repo_path: str) -> Dict[str, Any]:
    with open(os.path.join(repo_path, "manifest.json"), encoding="utf-8") as file:
        return json.load(file)


def read_input_manifest() -> List[Dict[str, Any]]:
    with open("manifest_in.json", encoding="utf-8") as file:
        return json.load(file)


def get_repo_name(uri) -> str:
    repo_name = urllib.parse.urlparse(uri).path.split("/")[-1]
    return repo_name


def get_component_by_id(package_manifest, component_id: str) -> Dict[str, Any]:
    for component in package_manifest["components"]:
        if component["id"] == component_id:
            return component
    raise RuntimeError(f"No component with id {component_id!r} found!")


def handle_component(
    repo_path: str,
    input_component: Dict[str, Any],
    component: Dict[str, Any]
) -> Dict[str, Any]:
    base_path = ""

    if "basePath" in component:
        base_path = os.path.join(base_path, component["basePath"])
    else:
        base_path = os.path.join(base_path, input_component["basePath"])

    new_name = input_component["name"]
    if "rename" in input_component:
        new_name = input_component["rename"]

    if "newBasePath" not in input_component:
        new_path = os.path.join("components", "extensions", new_name)
    else:
        new_path = input_component["newBasePath"]

    print(f"* Base path: {base_path!r}")
    print(f"* New base path: {new_path!r}")

    if "noCopy" not in input_component:
        shutil.copytree(os.path.join(repo_path, base_path), new_path, dirs_exist_ok=True, ignore=shutil.ignore_patterns(".git", ".github", ".vscode", ".gitignore", "LICENSE", "manifest.json", "license_header.txt", "NOTICE.md", "SECURITY.md", "CODE_OF_CONDUCT.md",".pre-commit-config.yaml"))

    if "programs" in component:
        for programId in range(0, len(component["programs"])):
            for argId in range(0, len(component["programs"][programId]["args"])):
                component["programs"][programId]["args"][argId] = component["programs"][programId]["args"][argId].replace(base_path, "").replace("//", "/")

    returned_component: Dict[str, Any] = {
        "id": new_name,
        "basePath": new_path,
    }

    if "onPostInit" in component:
        returned_component["onPostInit"] = component["onPostInit"]

    if "files" in component:
        returned_component["files"] = component["files"]

    if "programs" in component:
        returned_component["programs"] = component["programs"]

    if "variables" in component:
        returned_component["variables"] = component["variables"]

    return returned_component


def handle_ci(
    repo_path: str,
    input_package: Dict[str, Any]
) -> None:
    if "workflows" in input_package:
        for workflow in input_package["workflows"]:
            from_workflow = os.path.join(repo_path, ".github", "workflows", workflow["from"])
            to_workflow = os.path.join(".github", "workflows", workflow["to"])

            target_dir = os.path.join(*to_workflow.split('/')[0:-1])
            os.makedirs(target_dir, exist_ok=True)
            shutil.copy(from_workflow, to_workflow)

            workflow = open(to_workflow).readlines()
            for i in range(0, len(workflow)):
                if workflow[i].startswith("name:"):
                    workflow[i] = f"{workflow[i].rstrip()}-{get_repo_name(input_package['uri'])}\n"

                if workflow[i].strip().startswith("group: ${{ github.ref }}"):
                    workflow[i] = f"{workflow[i].rstrip()}-{get_repo_name(input_package['uri'])}\n"
            open(to_workflow, mode="w").writelines(workflow)

    if "actions" in input_package:
        for action in input_package["actions"]:
            from_action = os.path.join(repo_path, ".github", "actions", action["from"])
            to_action = os.path.join(".github", "actions", action["to"])
            shutil.copytree(from_action, to_action, dirs_exist_ok=True)


def handle_manifest(manifest: Dict[str, Any]) -> None:
    with open("manifest.json", encoding="utf-8", mode="w") as file:
        json.dump(manifest, file, indent=4)


def main() -> None:
    input_data = read_input_manifest()
    new_manifest: Dict[str, Any] = {}
    new_manifest["components"] = []
    for package in input_data:
        package_uri = package["uri"]

        print(f"Processing PKG: {package_uri}")
        repo_path = checkout_velocitas_repo(package_uri)

        print("* Getting manifest data")
        package_manifest = read_package_manifest(repo_path)

        for input_component in package["components"]:
            print(f"Component name: {input_component['name']!r}")
            manifest_comp = get_component_by_id(
                package_manifest,
                input_component["name"]
            )
            new_manifest_entry = handle_component(repo_path, input_component, manifest_comp)
            new_manifest["components"].append(new_manifest_entry)

        handle_ci(repo_path, package)

    handle_manifest(new_manifest)


if __name__ == "__main__":
    main()
