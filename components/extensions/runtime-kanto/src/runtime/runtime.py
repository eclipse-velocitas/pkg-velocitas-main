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

import json
import os
import subprocess
import sys
import time
from io import TextIOWrapper
from pathlib import Path

from velocitas_lib import (
    get_app_manifest,
    get_cache_data,
    get_package_path,
    get_script_path,
    get_workspace_dir,
    require_env,
)
from yaspin.core import Yaspin

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "app_deployment"))
from deploy_vehicleapp import remove_vehicleapp  # noqa: E402


def remove_container(log_output: TextIOWrapper):
    """Uninstall the runtime.

    Args:
        log_output (TextIOWrapper | int): Logfile to write or DEVNULL by default.
    """
    log_output.write("Removing databroker container\n")
    subprocess.call(
        ["kanto-cm", "remove", "-f", "-n", "databroker"],
        stdout=log_output,
        stderr=log_output,
    )
    log_output.write("Removing mosquitto container\n")
    subprocess.call(
        ["kanto-cm", "remove", "-f", "-n", "mosquitto"],
        stdout=log_output,
        stderr=log_output,
    )
    log_output.write("Removing feedercan container\n")
    subprocess.call(
        ["kanto-cm", "remove", "-f", "-n", "feedercan"],
        stdout=log_output,
        stderr=log_output,
    )
    log_output.write("Removing seatservice container\n")
    subprocess.call(
        ["kanto-cm", "remove", "-f", "-n", "seatservice"],
        stdout=log_output,
        stderr=log_output,
    )
    log_output.write("Removing mockservice container\n")
    subprocess.call(
        ["kanto-cm", "remove", "-f", "-n", "mockservice"],
        stdout=log_output,
        stderr=log_output,
    )
    app_name = get_app_manifest()["name"].lower()
    log_output.write(f"Removing {app_name} container\n")
    remove_vehicleapp(app_name, log_output)


def adapt_feedercan_deployment_file():
    """Update the feedercan config with the correct mount path."""

    file_path = os.path.join(get_script_path(), "deployment", "feedercan.json")
    if not os.path.isfile(file_path):
        return

    with open(
        file_path,
        "r+",
        encoding="utf-8",
    ) as f:
        data = json.load(f)
        data["image"]["name"] = require_env("feederCanImage")
        data["mount_points"][0]["source"] = os.path.join(
            get_package_path(), "config", "feedercan"
        )
        f.seek(0)
        json.dump(data, f, indent=4)


def adapt_mockservice_deployment_file():
    """Update the mockservice config with the correct mount path."""

    file_path = os.path.join(get_script_path(), "deployment", "mockservice.json")
    if not os.path.isfile(file_path):
        return

    with open(
        file_path,
        "r+",
        encoding="utf-8",
    ) as f:
        data = json.load(f)
        source = os.path.join(get_package_path(), "mock.py")
        # use mock.py from repo root if available
        if os.path.isfile(os.path.join(get_workspace_dir(), "mock.py")):
            source = os.path.join(get_workspace_dir(), "mock.py")

        data["image"]["name"] = require_env("mockServiceImage")
        data["mount_points"][0]["source"] = source
        f.seek(0)
        json.dump(data, f, indent=4)


def adapt_databroker_deployment_file():
    """Update the databroker config with the correct mount path."""

    file_path = os.path.join(get_script_path(), "deployment", "databroker.json")
    if not os.path.isfile(file_path):
        return

    with open(
        file_path,
        "r+",
        encoding="utf-8",
    ) as f:
        data = json.load(f)
        cache = get_cache_data()
        data["image"]["name"] = require_env("vehicleDatabrokerImage")
        data["mount_points"][0]["source"] = cache["vspec_file_path"]
        f.seek(0)
        json.dump(data, f, indent=4)


def adapt_mosquitto_deployment_file():
    """Update the databroker config with the correct mount path."""

    file_path = os.path.join(get_script_path(), "deployment", "mosquitto.json")
    if not os.path.isfile(file_path):
        return

    with open(
        file_path,
        "r+",
        encoding="utf-8",
    ) as f:
        data = json.load(f)
        data["image"]["name"] = require_env("mqttBrokerImage")
        f.seek(0)
        json.dump(data, f, indent=4)


def undeploy_runtime(spinner: Yaspin, log_output: TextIOWrapper):
    """Undeploy/remove the runtime and display the progress
    using the given spinner.

    Args:
        spinner (Yaspin): The progress spinner to update.
        log_output (TextIOWrapper | int): Logfile to write or DEVNULL by default.
    """
    status = "> Undeploying runtime... "
    remove_container(log_output)
    status = status + "uninstalled!"
    spinner.write(status)


def is_kanto_running(log_output: TextIOWrapper) -> bool:
    """Check if Kanto is already running.

    Args:
        log_output (TextIOWrapper | int): Logfile to write or DEVNULL by default.
    """
    if Path("/run/container-management/container-management.sock").exists():
        adapt_socket(log_output)
    else:
        return False

    try:
        subprocess.check_call(
            [
                "kanto-cm",
                "sysinfo",
                "--timeout",
                "1",
            ],
            stdout=log_output,
            stderr=log_output,
        )
    except Exception:
        return False

    return True


def adapt_socket(log_output: TextIOWrapper):
    """Adapt the access rights for the Kanto socket.

    Args:
        log_output (TextIOWrapper | int): Logfile to write or DEVNULL by default.
    """

    subprocess.call(
        [
            "sudo",
            "chmod",
            "a+rw",
            "/run/container-management/container-management.sock",
        ],
        stdout=log_output,
        stderr=log_output,
    )


def start_kanto(spinner: Yaspin, log_output: TextIOWrapper):
    """Starting the Kanto process in background

    Args:
        spinner (Yaspin): The progress spinner to update.
        log_output (TextIOWrapper | int): Logfile to write or DEVNULL by default.
    """
    adapt_feedercan_deployment_file()
    adapt_mockservice_deployment_file()
    adapt_databroker_deployment_file()
    adapt_mosquitto_deployment_file()
    log_output.write("Starting Kanto runtime\n")
    kanto = subprocess.Popen(
        [
            "sudo",
            "container-management",
            "--cfg-file",
            f"{get_script_path()}/config.json",
            "--deployment-ctr-dir",
            f"{get_script_path()}/deployment",
            "--log-file",
            f"{get_workspace_dir()}/logs/runtime_kanto/container-management.log",
        ],
        start_new_session=True,
        stderr=log_output,
        stdout=log_output,
    )

    socket = Path("/run/container-management/container-management.sock")
    while not socket.exists():
        print("waiting")
        time.sleep(1)

    adapt_socket(log_output)

    # sleep a bit to properly get the errors
    time.sleep(0.1)
    if kanto.poll() == 1:
        spinner.text = "Starting Kanto failed!"
        spinner.fail("💥")
        stop_kanto(log_output)
        return

    spinner.text = "Kanto is ready to use!"
    spinner.ok("✅")


def stop_kanto(log_output: TextIOWrapper):
    """Stopping the Kanto process.

    Args:
        log_output (TextIOWrapper | int): Logfile to write or DEVNULL by default.
    """
    log_output.write("Stopping Kanto runtime\n")
    subprocess.check_call(
        [
            "sudo",
            "pkill",
            "-1",
            "-f",
            "container-management",
        ],
        stdout=log_output,
        stderr=log_output,
    )
