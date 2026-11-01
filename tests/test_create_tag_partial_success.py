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
"""Tests for partial success while creating an Azure tag."""

from importlib import import_module
from types import SimpleNamespace

from soar_sdk.action_results import ActionResult
from soar_sdk.exceptions import ActionFailure


def test_create_tag_preserves_created_name_when_value_retry_fails(monkeypatch):
    action_module = import_module("src.actions.create_tag")
    retry_error = ActionFailure("Status Code: 403. Tag value write was denied")
    calls = []

    def make_azure_request(asset, endpoint, **kwargs):
        calls.append((endpoint, kwargs))
        if len(calls) == 1:
            raise ActionFailure("PredefinedTagNameNotFound")
        if len(calls) == 2:
            return {
                "id": "/subscriptions/sub/tagNames/environment",
                "name": "environment",
            }
        raise retry_error

    monkeypatch.setattr(action_module, "make_azure_request", make_azure_request)
    params = action_module.CreateTagParams(tag_name="environment", tag_value="prod")
    soar = SimpleNamespace(
        set_message=lambda message: None, set_summary=lambda summary: None
    )
    asset = SimpleNamespace(subscription_id="sub")

    result = action_module.create_tag.__wrapped__(params, soar, asset)

    assert isinstance(result, ActionResult)
    assert result.get_status() is False
    assert result.get_message() == str(retry_error)
    assert result.get_param() == params.model_dump()
    assert result.get_data() == [
        {
            "id": "/subscriptions/sub/tagNames/environment",
            "name": "environment",
            "tagName": "environment",
            "tagValue": "prod",
            "failed_stage": "create_tag_value",
        }
    ]
    assert len(calls) == 3
