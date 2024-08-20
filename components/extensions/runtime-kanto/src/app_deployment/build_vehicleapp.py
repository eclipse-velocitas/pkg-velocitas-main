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

from velocitas_lib import create_log_file
from velocitas_lib.docker import build_vehicleapp_image
from yaspin import yaspin


def build_vehicleapp():
    """Build VehicleApp docker image and display the progress using a spinner."""

    print("Hint: Log files can be found in your workspace's logs directory")
    log_output = create_log_file("build-vapp", "runtime_kanto")
    with yaspin(text="Building VehicleApp...", color="cyan") as spinner:
        try:
            status = "> Building VehicleApp image"
            spinner.write(status)

            build_vehicleapp_image(log_output)

            spinner.ok("✅")
        except Exception as err:
            log_output.write(str(err))
            spinner.fail("💥")


if __name__ == "__main__":
    build_vehicleapp()
