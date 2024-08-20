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
from pathlib import Path
from re import Pattern
from re import compile as re_compile
from subprocess import PIPE, Popen
from threading import Timer

BASE_COMMAND_RUNTIME = "velocitas exec runtime-kanto"
BASE_COMMAND_DEPLOYMENT = "velocitas exec deployment-kanto"

regex_runtime_up: Pattern[str] = re_compile(r"✅.* Kanto is ready to use!")
regex_build: Pattern[str] = re_compile(r"✅.* Building VehicleApp...")
regex_deploy: Pattern[str] = re_compile(r"✅.* Deploying VehicleApp...")
regex_stop: Pattern[str] = re_compile(r"✅.* Stopping Kanto...")
DEFAULT_TIMEOUT_SEC: float = 120


def create_dummy_vspec_file():
    """Create an empty vspec json file in the project's cache directory
    plus the respective 'vspec_file_path' cache variable pointing to it.
    !!! Todo: Replace this workaround solution making assumptions about
              the cache location.
    """
    cache_paths = Path("~/.velocitas/projects").expanduser().rglob("cache.json")
    for cache_path in cache_paths:
        vspec_path = cache_path.parent / "dummy_vspec.json"
        with open(vspec_path, mode="w", encoding="utf-8") as dummy_vspec_file:
            dummy_vspec_file.write("{}\n")
        with open(cache_path, mode="r", encoding="utf-8") as cache_file:
            cache = json.load(cache_file)
        cache["vspec_file_path"] = str(vspec_path)
        with open(cache_path, mode="w", encoding="utf-8") as cache_file:
            json.dump(cache, cache_file)


def check_container_is_running(container_name: str) -> bool:
    """Return whether the container is running or not.

    Args:
        app_name (str): App name
    """
    return json.loads(
        subprocess.run(
            ["kanto-cm", "get", "-n", container_name], stdout=subprocess.PIPE
        ).stdout.decode("utf-8")
    )["state"]["running"]


def run_command_until_logs_match(
    command: str, regex_service: Pattern[str], timeout_sec=DEFAULT_TIMEOUT_SEC
) -> bool:
    proc: Popen[str] = Popen(
        command.split(" "), stdout=PIPE, bufsize=1, universal_newlines=True
    )
    timer: Timer = Timer(timeout_sec, proc.kill)
    timer.start()
    if not proc.stdout:
        return False
    for line in iter(proc.stdout.readline, b""):
        if proc.poll() is not None:
            print(f"Timeout reached after {timeout_sec} seconds, process killed!")
            timer.cancel()
            return False
        sys.stdout.write(line)
        if regex_service is not None and regex_service.search(line):
            timer.cancel()
            break
    return True


def wait_for_container_update():
    path = os.path.join(Path.cwd(), "logs/runtime_kanto/container-management.log")
    with open(path, mode="r", encoding="utf-8") as f:
        while True:
            line = f.readline()
            print(line)
            if line.find("finished containers update") != -1:
                f.close()
                break
            # if line is empty and string not found wait for more input
            if len(line) == 0:
                print("waiting")
                time.sleep(1)


def test_scripts_run_successfully():
    create_dummy_vspec_file()
    assert run_command_until_logs_match(f"{BASE_COMMAND_RUNTIME} up", regex_runtime_up)
    wait_for_container_update()
    assert check_container_is_running("mosquitto")
    assert check_container_is_running("databroker")
    # feedercan and seatservice are disabled for now
    # assert check_container_is_running("feedercan")
    # assert check_container_is_running("seatservice")
    assert run_command_until_logs_match(
        f"{BASE_COMMAND_DEPLOYMENT} build-vehicleapp", regex_build, 60 * 12
    )
    assert run_command_until_logs_match(
        f"{BASE_COMMAND_DEPLOYMENT} deploy-vehicleapp", regex_deploy
    )


def test_scripts_run_successfully_with_down():
    test_scripts_run_successfully()
    assert run_command_until_logs_match(f"{BASE_COMMAND_RUNTIME} down", regex_stop)
