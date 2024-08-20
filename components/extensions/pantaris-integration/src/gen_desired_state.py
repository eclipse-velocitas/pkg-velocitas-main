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
import hashlib
import json
import os
import re
import tempfile
from typing import Any, Dict, List, Optional

import velocitas_lib
import velocitas_lib.services

from velocitas_lib import get_workspace_dir

VSS_SOURCE_DEFAULT_ID = "vss-source-default"
VSS_SOURCE_CUSTOM_ID = "vss-source-custom"
DATABROKER_ID = "data-broker-grpc"
GRPC_INTERFACE_ID = "grpc-interface"

VELOCITAS_IF_VSI = "vehicle-signal-interface"
VELOCITAS_IF_PUBSUB = "pubsub"
VELOCITAS_IF_GRPC = "grpc-interface"


def is_uri(path: str) -> bool:
    """Check if the provided path is a URI.

    Args:
        path (str): The path to check.

    Returns:
        bool: True if the path is a URI. False otherwise.
    """
    return re.match(r"(\w+)\:\/\/(\w+)", path) is not None


def parse_vehicle_signal_interface(config: Dict[str, Any]) -> List[str]:
    """Parse the vehicle signal interface config.

    Args:
        config (Dict[str, Any]): The json-config of the interface,
        as defined in the appManifest.json.

    Returns:
        List[str]: A list of requirements defined by the config.
    """
    requirements = []
    src = str(config["src"])
    vss_release_prefix = (
        "https://github.com/COVESA/vehicle_signal_specification/releases/download/"
    )
    version = ""
    if vss_release_prefix in src:
        version = src.removeprefix(vss_release_prefix).split("/")[0]
        requirements.append(f"{VSS_SOURCE_DEFAULT_ID}:{version}")
    else:
        version = get_md5_from_file_content(
            os.path.join(get_workspace_dir(), os.path.normpath(src))
        )
        requirements.append(f"{VSS_SOURCE_CUSTOM_ID}:{version}")

    requirements.append(f"{DATABROKER_ID}:v1")

    datapoints = config["datapoints"]["required"]
    for datapoint in datapoints:
        path = str(datapoint["path"]).lower().replace(".", "-")
        access = datapoint["access"]
        requirements.append(f"vss-{access}-{path}:{version}")

    return requirements


def parse_grpc_interface(config: Dict[str, Any]) -> str:
    """Parse the grpc interface config.

    Args:
        config (Dict[str, Any]): The json-config of the interface,
        as defined in the appManifest.json.

    Returns:
        str: The requirement with md5-hash of the proto-file as version.
    """
    src = str(config["src"])

    return f"{GRPC_INTERFACE_ID}:{get_md5_from_file_content(src)}"


def get_md5_from_file_content(src: str) -> str:
    """Get the md5-hash of the contents of a file defined by a source.

    Args:
        src (str): The source of the file. Can either be a local file-path or an URI

    Returns:
        str: The md5-hash of the file.
    """
    file_path = src
    if is_uri(src):
        file_path = os.path.join(tempfile.TemporaryDirectory().name, "tmp")
        velocitas_lib.download_file(src, file_path)

    md5 = hashlib.md5(usedforsecurity=False)
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            md5.update(chunk)

    return md5.hexdigest()


def parse_interfaces(interfaces: List[Dict[str, Any]]) -> List[str]:
    """Parse the defined interfaces.

    Args:
        interfaces (List[Dict[str, Any]])): The json-array of interfaces,
        as defined in the appManifest.json.

    Returns:
        List[str]: A list of requirements defined by the interface definitions.
    """
    requirements = []
    for interface in interfaces:
        interface_type = interface["type"]
        if interface_type == VELOCITAS_IF_VSI:
            requirements += parse_vehicle_signal_interface(interface["config"])
        elif interface_type == VELOCITAS_IF_PUBSUB:
            requirements.append("mqtt:v5")
        elif interface_type == VELOCITAS_IF_GRPC:
            requirements.append(parse_grpc_interface(interface["config"]))

    return requirements


def main(source: str, output_file_path: Optional[str] = None):
    imageName = source.split(":")[0].split("/")[-1]
    version = source.split(":")[1]

    app_manifest = velocitas_lib.get_app_manifest()
    appName = app_manifest["name"]
    interfaces = app_manifest["interfaces"]

    requirements = []
    requirements += parse_interfaces(interfaces)

    if output_file_path is None:
        output_file_path = velocitas_lib.get_workspace_dir()
    output_file_path = f"{output_file_path}/{appName.lower()}_manifest_{version}.json"

    data = {
        "name": appName,
        "source": source,
        "type": "container",
        "requires": requirements,
        "provides": [f"{imageName}:{version}"],
    }
    with open(
        output_file_path,
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(data, f)


if __name__ == "__main__":
    os.environ["mockFilePath"] = "mock.py"
    parser = argparse.ArgumentParser("generate-desired-state")
    parser.add_argument(
        "-o",
        "--output-file-path",
        type=str,
        required=False,
        help="Path to the folder where the manifest should be placed.",
    )
    parser.add_argument(
        "-s",
        "--source",
        type=str,
        required=True,
        help="The URL of the image including the tag.",
    )
    args = parser.parse_args()
    main(args.source, args.output_file_path)
