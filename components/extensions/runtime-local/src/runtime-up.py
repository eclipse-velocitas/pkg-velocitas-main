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

import signal
import subprocess
import time
from typing import Dict

from local_lib import run_service, stop_container, stop_service
from velocitas_lib import get_log_file_name
from velocitas_lib.services import get_services
from yaspin import yaspin

spawned_processes: Dict[str, subprocess.Popen] = {}


def run_services() -> None:
    """Run all required services."""

    print("Hint: Log files can be found in your workspace's logs directory")
    with yaspin(text="Starting runtime...", color="cyan") as spinner:
        try:
            for service in get_services():
                stop_service(service)
                spinner.text = f"Starting {service.id}..."
                spawned_processes[service.id] = run_service(service)
                spinner.write(f"> {service.id} running")
            spinner.text = "Runtime is ready to use!"
            spinner.ok("✅")
        except RuntimeError as error:
            spinner.write(error.args)
            spinner.fail("💥")
            terminate_spawned_processes()
            print(f"Starting {service.id} failed")
            with open(
                get_log_file_name(service.id, "runtime_local"),
                mode="r",
                encoding="utf-8",
            ) as log:
                print(f">>>> Start log of {service.id} >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                print(log.read(), end="")
                print(f"<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< End log of {service.id} <<<<")


def wait_while_processes_are_running():
    while len(spawned_processes) > 0:
        time.sleep(1)
        for name, process in spawned_processes.items():
            poll_result = process.poll()

            if isinstance(poll_result, int):
                print(f"Process terminated: {name!r} result: {poll_result}")
                del spawned_processes[name]
                break


def terminate_spawned_processes():
    with yaspin(text="Stopping runtime...", color="cyan") as spinner:
        while len(spawned_processes) > 0:
            (service_id, process) = spawned_processes.popitem()
            process.terminate()
            stop_container(service_id, subprocess.DEVNULL)
            spinner.write(
                f"> {[process.args][0]!r} (service_id={service_id!r}) terminated"
            )
        spinner.ok("✅")


def handler(_signum, _frame):  # noqa: U101 unused arguments
    terminate_spawned_processes()


if __name__ == "__main__":
    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)
    run_services()
    wait_while_processes_are_running()
