# Copyright (c) 2023-2024 Contributors to the Eclipse Foundation
#
# This program and the accompanying materials are made available under the
# terms of the Apache License, Version 2.0 which is available at
# https://www.apache.org/licenses/LICENSE-2.0.
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#
# SPDX-License-Identifier: Apache-2.0

import argparse
import json
import os
import shutil
import subprocess  # nosec B404
from pathlib import Path
from typing import Iterable, List


def get_project_creation_sdk_temp() -> Path:
    return os.path.join(Path(os.path.dirname(__file__)), "sdk_temp")


def clean_up_sdk_temp() -> None:
    if os.path.exists(get_project_creation_sdk_temp()):
        shutil.rmtree(get_project_creation_sdk_temp())


def verbose_copy(src, dst) -> object:
    print(f"Copying {src!r} to {dst!r}")
    return shutil.copy2(src, dst)


def clone_sdk(sdk_temp_dir: str) -> None:
    with open(f"{os.path.dirname(__file__)}/config.json") as f:
        config = json.load(f)
        repo_url = config["sdkUri"]
        repo_version = config["sdkVersion"]
        try:
            clean_up_sdk_temp()
            subprocess.check_call(
                [
                    "git",
                    "-c",
                    "advice.detachedHead=false",
                    "clone",
                    "--quiet",
                    "--depth",
                    "1",
                    "--branch",
                    repo_version,
                    repo_url,
                    sdk_temp_dir,
                ]
            )
            print(f"SDK cloned successfully!")
        except subprocess.CalledProcessError as e:
            print(f"Error cloning repository: {e}")


def copy_files(root_destination: str) -> None:
    with open(f"{os.path.dirname(__file__)}/config.json") as f:
        files = json.load(f)["files"]
        for file in files:
            destination = root_destination
            if ".project-creation/templates" in file:
                destination = os.path.join(
                    root_destination,
                    os.path.dirname(file.removeprefix(".project-creation/templates/")),
                )

            Path(destination).mkdir(parents=True, exist_ok=True)
            source = f"{get_project_creation_sdk_temp()}/{file}"
            verbose_copy(source, destination)


def _filter_hidden_files(_: str, dir_contents: List[str]) -> Iterable[str]:
    hidden_files = [".git"]
    return filter(lambda file: file in hidden_files, dir_contents)


def copy_project(source_path: str, destination_repo: str) -> None:
    app_path = os.path.join(destination_repo, "app")

    shutil.copytree(
        source_path,
        app_path,
        copy_function=verbose_copy,
        dirs_exist_ok=True,
        ignore=_filter_hidden_files,
    )

    readme_path = os.path.join(app_path, "README.md")
    if os.path.exists(readme_path):
        existing_readme_path = os.path.join(destination_repo, "README.md")
        if os.path.exists(existing_readme_path):
            os.remove(existing_readme_path)
        shutil.move(readme_path, destination_repo, copy_function=verbose_copy)


def replace_app_name(creation_name: str, destination_repo: str) -> None:
    app_path = os.path.join(destination_repo, "app")

    for root, dirs, files in os.walk(app_path):
        for file in files:
            file_path = os.path.join(root, file)
            with open(file_path, "r") as f:
                content = f.read()

            modified_content = content.replace("AppName", creation_name)

            with open(file_path, "w") as f:
                f.write(modified_content)
    print(f"Replaced 'AppName' with '{creation_name}' in all files.")


def compile_requirements(destination_repo: str) -> None:
    subprocess.check_call(  # nosec B603, B607
        ["pip", "install", "pip-tools"],
        cwd=os.path.join(destination_repo),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    subprocess.check_call(  # nosec B603, B607
        ["python", "-m", "piptools", "compile"],
        cwd=os.path.join(destination_repo),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def main():
    parser = argparse.ArgumentParser("run")
    parser.add_argument(
        "-d",
        "--destination",
        type=str,
        required=True,
        help="Path to the root of the repository.",
    )
    parser.add_argument(
        "-n",
        "--name",
        type=str,
        required=False,
        help="Name of the VApp.",
    )
    parser.add_argument(
        "-e",
        "--example",
        type=str,
        required=False,
        help="Copy the given example to the new repo.",
    )
    args = parser.parse_args()

    clone_sdk(get_project_creation_sdk_temp())

    copy_files(args.destination)

    examples_directory_path = os.path.join(get_project_creation_sdk_temp(), "examples")
    example_app = (
        os.path.join(examples_directory_path, args.example)
        if args.example
        else os.path.join(
            get_project_creation_sdk_temp(), ".project-creation", ".skeleton"
        )
    )

    copy_project(example_app, args.destination)

    # For now only when skeleton is created
    if not args.example:
        replace_app_name(args.name, args.destination)

    compile_requirements(args.destination)

    shutil.rmtree(get_project_creation_sdk_temp())


if __name__ == "__main__":
    main()
