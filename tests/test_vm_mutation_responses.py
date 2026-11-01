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
"""Tests for preserving Azure VM mutation response fields."""

from importlib import import_module
from types import SimpleNamespace

import pytest


ACTIONS = [
    ("start_vm", "StartVmParams", "Successfully started VM"),
    ("stop_vm", "StopVmParams", "Successfully stopped VM"),
    ("deallocate_vm", "DeallocateVmParams", "Successfully deallocated VM"),
    ("generalize_vm", "GeneralizeVmParams", "Successfully generalized the vm"),
    ("redeploy_vm", "RedeployVmParams", "Successfully redeployed the vm"),
]


@pytest.mark.parametrize("action_name,params_class_name,success_message", ACTIONS)
@pytest.mark.parametrize(
    "response",
    [
        pytest.param(
            {
                "id": "/subscriptions/sub/vms/vm",
                "status": "Succeeded",
                "customVendorField": "retained",
            },
            id="nonempty-response",
        ),
        pytest.param({}, id="empty-response"),
    ],
)
def test_vm_mutation_outputs_preserve_response_fields(
    monkeypatch, action_name, params_class_name, success_message, response
):
    action_module = import_module(f"src.actions.{action_name}")
    monkeypatch.setattr(
        action_module,
        "make_azure_request",
        lambda *args, **kwargs: response,
    )
    params = getattr(action_module, params_class_name)(
        resource_group_name="rg",
        vm_name="vm",
    )
    soar_messages = []
    soar_summaries = []
    soar = SimpleNamespace(
        set_message=soar_messages.append,
        set_summary=soar_summaries.append,
    )
    asset = SimpleNamespace(subscription_id="sub")

    result = getattr(action_module, action_name).__wrapped__(params, soar, asset)

    output = result.model_dump()
    assert output["resource_group_name"] == "rg"
    assert output["vm_name"] == "vm"
    assert soar_messages == [f"Status: {success_message}"]
    assert soar_summaries[0].status == success_message
    if response:
        assert output["id"] == response["id"]
        assert output["status"] == response["status"]
        assert output["customVendorField"] == "retained"
    else:
        assert "id" not in output
        assert "status" not in output
