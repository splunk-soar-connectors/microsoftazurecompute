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
"""Preserve inputs through real SDK action failure adaptation."""

from importlib import import_module
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from soar_sdk.action_results import ActionResult
from soar_sdk.auth.client import AuthorizationRequiredError
from soar_sdk.exceptions import ActionFailure

from src.action_errors import preserve_failure_params
from src.app import app
from soar_sdk.params import Param, Params


ACTIONS = [name for name in app.get_actions() if name != "test_connectivity"]


@pytest.mark.parametrize("name", ACTIONS)
@pytest.mark.parametrize(
    "error_type", [ActionFailure, AuthorizationRequiredError, ValueError]
)
def test_action_failure_retains_original_params(monkeypatch, name, error_type):
    action = app.get_actions()[name]
    module = import_module(f"src.actions.{name}")
    inputs = {
        "resource_group_name": "rg",
        "vm_name": "vm",
        "subscription_id": "sub",
        "group_name": "sg",
        "location": "West US",
        "snapshot_name": "snapshot",
        "create_option": "Copy",
        "source_resource_id": "/subscriptions/sub/disks/disk",
        "tag_name": "tag",
        "virtual_network_name": "vnet",
        "ip_address": "10.0.0.4",
        "group_type": "network",
        "command_id": "RunShellScript",
        "results_url": "https://management.azure.com/subscriptions/sub/results",
        "endpoint": "/providers/Microsoft.Compute/virtualMachines",
        "http_method": "GET",
    }
    params = action.params_class(
        **{
            key: value
            for key, value in inputs.items()
            if key in action.params_class.model_fields
        }
    )
    helper_name = next(
        key
        for key in [
            "_send_request",
            "make_azure_collection_request",
            "make_async_request",
            "make_absolute_request",
            "make_azure_request",
            "get_access_token",
        ]
        if hasattr(module, key)
    )
    request = Mock(side_effect=error_type("request denied"))
    monkeypatch.setattr(module, helper_name, request)
    results = []
    monkeypatch.setattr(
        app, "actions_manager", SimpleNamespace(add_result=results.append)
    )
    soar = SimpleNamespace(get_message=lambda: "", get_summary=lambda: None)

    status = action(params, soar=soar, asset=SimpleNamespace(subscription_id="sub"))

    assert status is False
    request.assert_called_once()
    assert len(results) == 1
    assert results[0].get_status() is False
    assert results[0].get_param() == params.model_dump(by_alias=True)
    assert "request denied" in results[0].get_message()
    assert "Traceback" not in results[0].get_message()


def test_existing_partial_result_passes_through_unchanged():
    params = Params()
    result = ActionResult(False, "second step failed", {"tag_name": "tag"})
    result.add_data({"id": "created-tag"})
    result.set_summary({"created": 1})

    @preserve_failure_params
    def handler(params: Params):
        return result

    assert handler(params) is result
    assert result.get_data() == [{"id": "created-tag"}]
    assert result.get_summary() == {"created": 1}


def test_unexpected_programming_error_remains_visible():
    @preserve_failure_params
    def handler(params: Params):
        raise RuntimeError("unexpected programming failure")

    with pytest.raises(RuntimeError, match="unexpected programming failure"):
        handler(Params())


def test_failure_tuple_uses_parameter_aliases():
    class AliasParams(Params):
        value: str = Param(alias="original_name")

    @preserve_failure_params
    def handler(params: AliasParams):
        raise ActionFailure("invalid request")

    status, message, params = handler(AliasParams(original_name="input"))
    assert status is False
    assert "invalid request" in message
    assert params == {"original_name": "input"}
