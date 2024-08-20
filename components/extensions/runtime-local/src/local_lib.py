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
import time
from io import TextIOWrapper
from itertools import filterfalse
from re import Pattern, compile
from threading import Timer
from typing import List, Optional

from velocitas_lib import create_log_file
from velocitas_lib.services import Service


def get_container_runtime_executable() -> str:
    """Return the current container runtime executable. E.g. docker."""
    return "docker"


def run_service(service: Service) -> subprocess.Popen:
    """Run a single service.

    Args:
        service: The service.

    Returns:
       The Popen object representing the root process running the required service
    """
    log = create_log_file(service.id, "runtime_local")
    log.write(f"Starting {service.id!r}\n")

    env_vars = dict[str, Optional[str]]()
    env_vars.update(service.config.env_vars)
    patterns: List[Pattern[str]] = [
        compile(pattern) for pattern in service.config.startup_log_patterns
    ]

    port_forward_args = []
    for port_forward in service.config.port_forwards:
        port_forward_args.append("-p")
        port_forward_args.append(port_forward)

    mount_args = []
    for mount in service.config.mounts:
        mount_args.append("-v")
        mount_args.append(mount)

    env_forward_args = []
    for key, value in env_vars.items():
        env_forward_args.append("-e")
        if value:
            env_forward_args.append(f"{key}={value}")
        else:
            env_forward_args.append(f"{key}")

    docker_args = [
        get_container_runtime_executable(),
        "run",
        "--rm",
        "--init",
        "--name",
        service.id,
        *env_forward_args,
        *port_forward_args,
        *mount_args,
        "--network",
        "host",
        service.config.image,
        *service.config.args,
    ]

    return spawn_process(docker_args, log, patterns, startup_timeout_sec=60)


def spawn_process(
    args: List[str],
    log: TextIOWrapper,
    patterns: List[Pattern[str]],
    startup_timeout_sec: int,
) -> subprocess.Popen:
    """Spawn the process defined by the passed args.

    Args:
        args:
            The executable name to be spawned and its arguments
        log:
            Log file to receive the outputs (stdout + stderr) of the spawned process
        patterns:
            List of patterns, which match the lines in the log file to rate the
            process being started up successfully.
            All of the patterns need to match in any order.
            If the list is empty, startup will be rated successfully without
            doing any pattern matching.
        startup_timeout_sec:
            Timeout [in seconds] after which the spawned process gets killed,
            if not all patterns did match so far

    Returns:
       The created Popen object
    """
    with open(log.name, "r", encoding="utf-8") as monitor:
        log.write(" ".join(args) + "\n\n")
        log.flush()
        process = subprocess.Popen(
            args,
            start_new_session=True,
            stderr=subprocess.STDOUT,
            stdout=log,
        )

        timer: Timer = Timer(startup_timeout_sec, process.kill)
        timer.start()
        for line in iter(monitor.readline, b""):
            if not timer.is_alive():
                raise RuntimeError(
                    """Timeout reached after {startup_timeout_sec}
                    seconds, service killed!"""
                )
            if process.poll() is not None:
                raise RuntimeError("Service unexpectedly terminated")
            if line == "":
                time.sleep(0.1)
                continue
            patterns[:] = filterfalse(
                lambda pattern: pattern.search(line),
                patterns,
            )
            if len(patterns) == 0:
                timer.cancel()
                break

    return process


def stop_container(service_id, log=None):
    """Stop the container representing the specified service.

    Args:
        service_id: The service_id of the container to stop.
        log: Log stream to forward the outputs to.
    """
    subprocess.call(
        [get_container_runtime_executable(), "stop", service_id],
        stderr=subprocess.STDOUT,
        stdout=log,
    )


def stop_service(service: Service):
    """Stop the given service.

    Args:
        service (Service): The service to stop.
    """
    log = create_log_file(service.id, "runtime_local")
    log.write(f"Stopping {service.id!r}\n")
    stop_container(service.id, log)
