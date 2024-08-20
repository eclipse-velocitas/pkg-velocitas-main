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
import sys
from pathlib import Path
from re import Pattern
from re import compile as re_compile
from subprocess import PIPE, Popen
from threading import Timer


def create_dummy_vspec_file():
    """Create an empty vspec json file in the project's cache directory
    plus the respective 'vspec_file_path' cache variable pointing to it.
    !!! Todo: Replace this workaround solution making assumptions about
              the cache location.
    """
    cache_paths = Path("~/.velocitas/projects").expanduser().rglob("cache.json")
    for cache_path in cache_paths:
        vspec_path = cache_path.parent / "dummy_vspec.json"
        with open(vspec_path, "w", encoding="utf-8") as dummy_vspec_file:
            dummy_vspec_file.write("{}\n")
        with open(cache_path, mode="r", encoding="utf-8") as cache_file:
            cache = json.load(cache_file)
        cache["vspec_file_path"] = str(vspec_path)
        with open(cache_path, mode="w", encoding="utf-8") as cache_file:
            json.dump(cache, cache_file)


command: str = "velocitas exec runtime-local"
regex_runtime_up: Pattern[str] = re_compile(r"✅.* Runtime is ready to use!")
regex_mqtt: Pattern[str] = re_compile(r"✅.* Starting service mqtt")
regex_vdb: Pattern[str] = re_compile(r"✅.* Starting service vehicledatabroker")
regex_seatservice: Pattern[str] = re_compile(r"✅.* Starting service seatservice")
regex_feedercan: Pattern[str] = re_compile(r"✅.* Starting service feedercan")
regex_mockservice: Pattern[str] = re_compile(r"✅.* Starting service mockservice")
DEFAULT_TIMEOUT_SEC: float = 180


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
            return False
        sys.stdout.write(line)
        if regex_service is not None and regex_service.search(line):
            timer.cancel()
            break
    return True


def test_scripts_run_successfully():
    create_dummy_vspec_file()
    assert run_command_until_logs_match(f"{command} up", regex_runtime_up)


def test_run_sevices_separately_successfully():
    create_dummy_vspec_file()
    assert run_command_until_logs_match(
        f"{command} run-service mqtt-broker", regex_mqtt
    )
    assert run_command_until_logs_match(
        f"{command} run-service vehicledatabroker", regex_vdb
    )
    assert run_command_until_logs_match(
        f"{command} run-service mockservice", regex_mockservice
    )
