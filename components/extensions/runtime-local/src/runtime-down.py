# Copyright (c) 2024 Contributors to the Eclipse Foundation
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

from local_lib import stop_service
from velocitas_lib.services import get_services
from yaspin import yaspin


def runtime_down():
    """Stop the local runtime."""

    print("Hint: Log files can be found in your workspace's logs directory")
    with yaspin(text="Stopping local runtime...", color="cyan") as spinner:
        for service in get_services():
            try:
                spinner.text = f"Stopping {service.id}..."
                stop_service(service)
                spinner.write(f"> {service.id} stopped")
            except Exception as error:
                spinner.write(error.args)
                spinner.fail("💥")
                print(f"Stopping {service.id} failed")

        spinner.text = "Stopped local runtime!"
        spinner.ok("✅")


if __name__ == "__main__":
    runtime_down()
