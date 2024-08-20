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

# flake8: noqa: E402
import os
import sys
from pathlib import Path

import pytest

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))
from gen_desired_state import get_md5_from_file_content, is_uri


@pytest.mark.parametrize(
    "src",
    [
        f"{Path.cwd()}/LICENSE",
        "https://raw.githubusercontent.com/eclipse-velocitas/devenv-runtimes/main/LICENSE",
    ],
)
def test_get_md5_for_file(src):
    hash = get_md5_from_file_content(src)
    # generated with https://emn178.github.io/online-tools/md5_checksum.html
    assert hash == "86d3f3a95c324c9479bd8986968f4327"


def test_is_uri__true():
    assert is_uri("https://github.com/eclipse-velocitas")


def test_is_uri__false():
    assert not is_uri(f"{Path.cwd()}/LICENSE")
