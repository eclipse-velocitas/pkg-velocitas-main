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

import subprocess
from io import TextIOWrapper

from velocitas_lib.docker import container_exists
from yaspin.core import Yaspin

K3D_REGISTRY_NAME = "k3d-registry"
KANTO_REGISTRY_NAME = "registry"


def registry_running(log_output: TextIOWrapper) -> bool:
    """Check if the Kanto registry is running.

    Args:
        log_output (TextIOWrapper | int): Logfile to write or DEVNULL by default.

    Returns:
        bool: True if the registry exists, False if not.
    """
    return "true" in str(
        subprocess.check_output(
            [
                "docker",
                "container",
                "inspect",
                "-f",
                "'{{.State.Running}}'",
                KANTO_REGISTRY_NAME,
            ],
            stderr=log_output,
        ),
        "utf-8",
    )


def create_and_start_registry(log_output: TextIOWrapper):
    """Create and start the Kanto registry.

    Args:
        log_output (TextIOWrapper | int): Logfile to write or DEVNULL by default.
    """
    log_output.write("Creating and starting Kanto registry container\n")
    subprocess.check_call(
        [
            "docker",
            "run",
            "-d",
            "-p",
            "12345:5000",
            "--name",
            KANTO_REGISTRY_NAME,
            "registry:2",
        ],
        stdout=log_output,
        stderr=log_output,
    )


def start_registry(log_output: TextIOWrapper):
    """Start the Kanto registry.

    Args:
        log_output (TextIOWrapper | int): Logfile to write or DEVNULL by default.
    """
    log_output.write("Starting Kanto registry container\n")
    subprocess.check_call(
        ["docker", "start", KANTO_REGISTRY_NAME],
        stdout=log_output,
        stderr=log_output,
    )


def stop_registry(log_output: TextIOWrapper):
    """Stop the Kanto registry.

    Args:
        log_output (TextIOWrapper | int): Logfile to write or DEVNULL by default.
    """
    log_output.write("Stopping Kanto registry container\n")
    subprocess.check_call(
        ["docker", "stop", KANTO_REGISTRY_NAME],
        stdout=log_output,
        stderr=log_output,
    )


def configure_controlplane(spinner: Yaspin, log_output: TextIOWrapper):
    """Configure the Kanto control plane and display the progress
    using the given spinner.

    Args:
        spinner (Yaspin): The progress spinner to update.
        log_output (TextIOWrapper | int): Logfile to write or DEVNULL by default.
    """
    if container_exists(K3D_REGISTRY_NAME, log_output):
        raise RuntimeError(
            "K3D runtime seems to be up. Please stop all other runtimes first."
        )

    status = "> Checking Kanto registry... "
    if not container_exists(KANTO_REGISTRY_NAME, log_output):
        spinner.write(status + "starting registry.")
        create_and_start_registry(log_output)
        spinner.write(status + "started.")
        log_output.write(status + "started.\n")
    else:
        spinner.write(status + "registry already exists.")
        if registry_running(log_output):
            spinner.write(status + "registry already started.")
            log_output.write(status + "registry already started.\n")
        else:
            spinner.write(status + "starting registry.")
            start_registry(log_output)
            spinner.write(status + "started.")
            log_output.write(status + "started.\n")


def reset_controlplane(spinner: Yaspin, log_output: TextIOWrapper):
    """Reset the Kanto control plane and display the progress
    using the given spinner.

    Args:
        spinner (Yaspin): The progress spinner to update.
        log_output (TextIOWrapper | int): Logfile to write or DEVNULL by default.
    """

    status = "> Stopping Kanto registry... "
    if container_exists(KANTO_REGISTRY_NAME, log_output):
        stop_registry(log_output)
        status = status + "stopped."
    else:
        status = status + "does not exist."
    spinner.write(status)
    log_output.write(status + "\n")
