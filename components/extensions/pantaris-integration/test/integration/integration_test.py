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


def test_output():
    file_path = os.path.dirname(__file__)
    file = f"{file_path}/sampleapp_manifest_v1.json"
    subprocess.run(
        [
            "velocitas",
            "exec",
            "pantaris-integration",
            "generate-desired-state",
            "-s",
            "ghcr.io/eclipse-velocitas/vehicle-app-python-template/sampleapp:v1",
            "-o",
            file_path,
        ]
    )
    assert os.path.isfile(file)
    with open(file) as f:
        data = json.load(f)
        assert data == {
            "name": "SampleApp",
            "source": "ghcr.io/eclipse-velocitas/vehicle-app-python-template/sampleapp:v1",  # noqa E501
            "type": "container",
            "requires": [
                "vss-source-default:v4.0",
                "data-broker-grpc:v1",
                "mqtt:v5",
            ],
            "provides": ["sampleapp:v1"],
        }
