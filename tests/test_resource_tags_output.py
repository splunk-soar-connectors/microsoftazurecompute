# Copyright (c) 2026 Splunk Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Preserve arbitrary Azure tags without imposing example-specific keys."""

from importlib import import_module
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from soar_sdk.app import App
from src.resource_tags import ResourceTagsOutput

RESOURCE_OUTPUTS = [
    ("add_application_security_group", "AddApplicationGroupOutput"),
    ("add_network_security_group", "AddNetworkGroupOutput"),
    ("get_system_info", "GetSystemInfoOutput"),
    ("list_resource_groups", "ListResourceGroupsOutput"),
    ("list_security_groups", "ListSecurityGroupsOutput"),
    ("list_snapshots", "ListSnapshotsOutput"),
    ("list_virtual_networks", "ListVirtualNetworksOutput"),
    ("list_vms", "ListVmsOutput"),
    ("snapshot_vm", "SnapshotVmOutput"),
]


@pytest.mark.parametrize(
    "tags",
    [
        {},
        {"environment": "production", "owner": "security"},
        {"author": "existing", "company": "example", "type": "vm"},
        {
            "Cost Center": "42",
            "team/name": "security",
            "key.with.dots": "",
            "region": "東京",
        },
    ],
)
def test_tag_model_accepts_arbitrary_keys_without_warnings(monkeypatch, tags):
    warning = Mock()
    monkeypatch.setattr("soar_sdk.action_results.warning", warning)

    result = ResourceTagsOutput.model_validate(tags)

    assert result.model_dump(by_alias=True) == tags
    assert result.model_json_schema().get("required", []) == []
    assert result.model_json_schema()["additionalProperties"] is True
    warning.assert_not_called()


@pytest.mark.parametrize("module_name, output_name", RESOURCE_OUTPUTS)
@pytest.mark.parametrize(
    "tag_input", [{}, {"environment": "production"}, None, "omitted"]
)
def test_resource_serialization_preserves_tag_presence_and_contents(
    module_name, output_name, tag_input
):
    output_class = getattr(import_module(f"src.actions.{module_name}"), output_name)
    payload = {"id": "/subscriptions/sub/resource"}
    if tag_input != "omitted":
        payload["tags"] = tag_input
    output = output_class(**payload)
    results = []

    App._adapt_action_result(output, SimpleNamespace(add_result=results.append))

    assert results[0].get_data() == [payload]
    paths = {field["data_path"] for field in output_class._to_json_schema()}
    assert not any(".tags." in path for path in paths)
    assert "id" in results[0].get_data()[0]
