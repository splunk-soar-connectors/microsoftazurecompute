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
"""Regression coverage for Azure VM failure summaries."""

from importlib import import_module
from types import SimpleNamespace

import pytest
from soar_sdk.exceptions import ActionFailure


@pytest.mark.parametrize(
    (
        "action_module_name",
        "action_name",
        "params_class_name",
        "error_message",
        "expected_status",
    ),
    [
        (
            "src.actions.generalize_vm",
            "generalize_vm",
            "GeneralizeVmParams",
            "OperationNotAllowed: Please power off the vm before generalizing it",
            "Virtual machine must be powered off. Please power off the vm before generalizing it.",
        ),
        (
            "src.actions.redeploy_vm",
            "redeploy_vm",
            "RedeployVmParams",
            "The virtual machine was not found",
            "Virtual machine not found under resource",
        ),
        (
            "src.actions.redeploy_vm",
            "redeploy_vm",
            "RedeployVmParams",
            "The resource group could not be found",
            "Resource group could not be found",
        ),
    ],
)
def test_vm_action_failures_preserve_legacy_summary(
    monkeypatch,
    action_module_name,
    action_name,
    params_class_name,
    error_message,
    expected_status,
):
    action_module = import_module(action_module_name)

    def raise_failure(*args, **kwargs):
        raise ActionFailure(error_message)

    monkeypatch.setattr(action_module, "make_azure_request", raise_failure)
    action_function = getattr(action_module, action_name)
    params = getattr(action_module, params_class_name)(
        resource_group_name="rg",
        vm_name="vm",
    )

    result = action_function.__wrapped__(params, SimpleNamespace(), SimpleNamespace())

    assert result.get_summary()["status"] == expected_status
