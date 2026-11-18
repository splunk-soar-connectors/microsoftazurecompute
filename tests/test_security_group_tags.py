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
"""Validate security-group tags through the SDK action boundary."""

from importlib import import_module
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from src.app import app


@pytest.fixture(
    params=[
        ("add_application_security_group", "AddApplicationGroupParams"),
        ("add_network_security_group", "AddNetworkGroupParams"),
    ]
)
def action_case(request):
    name, params_name = request.param
    module = import_module(f"src.actions.{name}")
    return module, getattr(module, name), getattr(module, params_name)


@pytest.mark.parametrize(
    "tags", ["null", "42", "true", '"text"', "[42]", '["key"]', '{"broken":']
)
def test_invalid_tags_fail_before_request_without_traceback(
    monkeypatch, action_case, tags
):
    module, action, params_class = action_case
    request = Mock(side_effect=AssertionError("Invalid tags must not reach Azure"))
    monkeypatch.setattr(module, "make_azure_request", request)
    results = []
    monkeypatch.setattr(
        app, "actions_manager", SimpleNamespace(add_result=results.append)
    )
    params = params_class(
        resource_group_name="rg", group_name="sg", location="West US", tags=tags
    )

    assert action(params, asset=object()) is False

    request.assert_not_called()
    assert len(results) == 1
    assert "'tags' action parameter" in results[0].get_message()
    assert "Traceback" not in results[0].get_message()


@pytest.mark.parametrize(
    "tags, expected",
    [
        (None, {}),
        ("", {}),
        ("{}", {}),
        ("[]", {}),
        ('{"environment":"prod"}', {"environment": "prod"}),
        ('[["environment","prod"]]', {"environment": "prod"}),
    ],
)
def test_legacy_accepted_tags_preserve_request_body(
    monkeypatch, action_case, tags, expected
):
    module, action, params_class = action_case
    request = Mock(return_value={})
    monkeypatch.setattr(module, "make_azure_request", request)
    params = params_class(
        resource_group_name="rg", group_name="sg", location="West US", tags=tags
    )
    soar = SimpleNamespace(
        set_summary=lambda value: None, set_message=lambda value: None
    )

    action.__wrapped__(params, soar, object())

    request.assert_called_once()
    body = request.call_args.kwargs["json_body"]
    assert body["tags"] == expected
    assert body["location"] == "West US"
