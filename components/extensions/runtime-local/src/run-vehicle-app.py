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
import subprocess

from velocitas_lib.middleware import MiddlewareType, get_middleware_type
from velocitas_lib.services import get_service_port


def run_app(executable_path: str, args: list[str], envs: list[str]):
    program_args = [executable_path, *args]

    if get_middleware_type() == MiddlewareType.NATIVE:
        vdb_address = "grpc://127.0.0.1"
        vdb_port = get_service_port("vehicledatabroker")
        mqtt_address = "mqtt://127.0.0.1"
        mqtt_port = get_service_port("mqtt-broker")

        middleware_config = {
            "SDV_MIDDLEWARE_TYPE": "native",
            "SDV_VEHICLEDATABROKER_ADDRESS": f"{vdb_address}:{vdb_port}",
            "SDV_MQTT_ADDRESS": f"{mqtt_address}:{mqtt_port}",
        }
        if envs:
            middleware_config.update(
                {env.split("=")[0]: env.split("=")[1] for env in envs}
            )

        subprocess.check_call(program_args, env=middleware_config)
    else:
        raise NotImplementedError("Unsupported middleware type!")


if __name__ == "__main__":
    # The arguments we accept
    parser = argparse.ArgumentParser(description="Starts the app to debug.")
    # Add para to name package
    parser.add_argument(
        "executable_path", type=str, help="Path to the executable to be invoked."
    )
    parser.add_argument("app_args", nargs="*")
    parser.add_argument(
        "-e", "--env", help="Environment variable to pass to the app.", action="append"
    )

    args = parser.parse_args()
    run_app(args.executable_path, args.app_args, args.env)
