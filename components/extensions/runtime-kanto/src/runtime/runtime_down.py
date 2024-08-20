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

from controlplane_kanto import reset_controlplane
from runtime import stop_kanto, undeploy_runtime
from velocitas_lib import create_log_file
from yaspin import yaspin


def runtime_down():
    """Stop the Kanto runtime."""

    print("Hint: Log files can be found in your workspace's logs directory")
    log_output = create_log_file("runtime-down", "runtime_kanto")
    with yaspin(text="Stopping Kanto...", color="cyan") as spinner:
        try:
            spinner.write("Removing containers...")
            undeploy_runtime(spinner, log_output)
            spinner.write("Stopping registry...")
            reset_controlplane(spinner, log_output)
            spinner.write("Stopping Kanto...")
            stop_kanto(log_output)
            spinner.ok("✅")
        except Exception as err:
            log_output.write(str(err))
            spinner.fail("💥")


if __name__ == "__main__":
    runtime_down()
