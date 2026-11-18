# Copyright (c) 2026 Splunk Inc.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# https://www.apache.org/licenses/LICENSE-2.0
"""Response-contract tests based on Microsoft's Run Command API examples.

2017-03-30 documents status/times and properties.output; 2025-04-01 documents
value[]. Fixture messages are deliberately JSON text to ensure no type conversion.
"""

from copy import deepcopy
from importlib import import_module
from types import SimpleNamespace

import pytest

from src.actions.list_virtual_networks import AddressspaceOutput
from src.command_output import CommandResponseOutput

ROW = {
    "code": "ComponentStatus/StdOut/succeeded",
    "level": "Info",
    "displayStatus": "Provisioning succeeded",
    "message": '{"answer": 42}',
}
OPERATION = {
    "status": "Succeeded",
    "name": "operation-id",
    "startTime": "2026-11-08T00:00:00Z",
    "endTime": "2026-11-08T00:00:01Z",
    "properties": {"output": [ROW]},
}
URL = "https://management.azure.com/subscriptions/sub/operations/op?api-version=2017-03-30"


@pytest.mark.parametrize("response", [OPERATION, {"value": [ROW]}, {}, [ROW], []])
@pytest.mark.parametrize("action", ["run_command", "get_results"])
def test_action_output_and_schema_match_vendor_response(monkeypatch, response, action):
    module = import_module(f"src.actions.{action}")
    incoming = deepcopy(response)
    if action == "run_command":
        monkeypatch.setattr(
            module, "make_async_request", lambda *a, **k: (incoming, None)
        )
        params = module.RunCommandParams(
            resource_group_name="rg", vm_name="vm", command_id="cmd"
        )
    else:
        monkeypatch.setattr(module, "make_absolute_request", lambda *a, **k: incoming)
        params = module.GetResultsParams(results_url=URL)
    soar = SimpleNamespace(
        set_summary=lambda value: None, set_message=lambda value: None
    )
    result = getattr(module, action).__wrapped__(
        params, soar, SimpleNamespace(subscription_id="sub")
    )
    expected = (
        {"properties": {"output": response}} if isinstance(response, list) else response
    )
    assert result.model_dump()["results"] == expected
    assert incoming == response
    # model_validate bypasses permissive __init__'s error suppression.
    CommandResponseOutput.model_validate(expected)
    paths = {f["data_path"] for f in type(result)._to_json_schema()}
    assert "action_result.data.*.results.properties.output.*.message" in paths
    assert "action_result.data.*.results.value.*.message" in paths
    assert "action_result.data.*.displayStatus" not in paths


def test_address_prefix_list_validates_and_generates_item_path():
    prefixes = ["10.0.0.0/16", "10.1.0.0/16"]
    result = AddressspaceOutput.model_validate({"addressPrefixes": prefixes})
    assert result.model_dump()["addressPrefixes"] == prefixes
    schema = list(AddressspaceOutput._to_json_schema())
    assert schema[0]["data_path"] == "action_result.data.*.addressPrefixes.*"
    assert schema[0]["data_type"] == "string"
