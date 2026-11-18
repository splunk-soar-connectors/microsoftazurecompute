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
"""Check opt-in start completion using the actual SDK action adapter."""

from importlib import import_module
from types import SimpleNamespace
from unittest.mock import Mock

import httpx
import pytest

from src import helper
from src.app import app

OP = "https://management.azure.com/subscriptions/override/operations/start"
LOCATION = "https://management.azure.com/subscriptions/override/operations/location"


def response(code=200, payload=None, headers=None):
    return httpx.Response(
        code, json=payload if payload is not None else {}, headers=headers
    )


def accepted(headers=None):
    return response(
        202, headers=headers if headers is not None else {"Azure-AsyncOperation": OP}
    )


@pytest.fixture
def run_action(monkeypatch):
    module = import_module("src.actions.start_vm")
    state = SimpleNamespace(now=0.0, sleeps=[], results=[], summary=None, message="")

    def sleep(delay):
        state.sleeps.append(delay)
        state.now += delay

    monkeypatch.setattr(helper.time, "monotonic", lambda: state.now)
    monkeypatch.setattr(helper.time, "sleep", sleep)
    monkeypatch.setattr(
        app, "actions_manager", SimpleNamespace(add_result=state.results.append)
    )
    soar = SimpleNamespace(
        set_summary=lambda value: setattr(state, "summary", value),
        get_summary=lambda: state.summary,
        set_message=lambda value: setattr(state, "message", value),
        get_message=lambda: state.message,
    )

    def run(responses, **params):
        state.send = Mock(side_effect=responses)
        monkeypatch.setattr(helper, "_send_request", state.send)
        state.params = module.StartVmParams(
            resource_group_name="rg", vm_name="vm", subscription_id="override", **params
        )
        state.status = module.start_vm(
            state.params, soar=soar, asset=SimpleNamespace(subscription_id="asset-sub")
        )
        return state

    return run


@pytest.mark.parametrize(
    "params",
    [
        {},
        {"wait_for_completion": False},
        {"wait_for_completion": False, "wait_timeout_seconds": 0},
    ],
)
def test_default_mode_returns_after_submission_without_new_output_fields(
    run_action, params
):
    state = run_action([accepted()], **params)
    assert state.status is True
    state.send.assert_called_once()
    assert state.sleeps == []
    result = state.results[0]
    assert result.get_summary() == {"status": "Successfully started VM"}
    assert result.get_data() == [{"resource_group_name": "rg", "vm_name": "vm"}]


def test_wait_confirms_operation_without_results_fetch_or_vm_probe(run_action):
    state = run_action(
        [
            accepted(
                {"Azure-AsyncOperation": OP, "Location": LOCATION, "Retry-After": "2"}
            ),
            response(payload={"status": "Running"}, headers={"Retry-After": "4"}),
            response(payload={"status": "Succeeded"}),
        ],
        wait_for_completion=True,
    )
    assert state.status is True
    assert state.sleeps == [2, 4]
    calls = state.send.call_args_list
    assert (
        calls[0].args[1]
        == "https://management.azure.com/subscriptions/override/resourceGroups/rg/providers/Microsoft.Compute/virtualMachines/vm/start?api-version=2018-06-01"
    )
    assert calls[0].kwargs["method"] == "POST"
    assert [call.args[1] for call in calls[1:]] == [OP, OP]
    assert all(call.kwargs.get("method", "GET") == "GET" for call in calls[1:])
    assert state.results[0].get_data()[0]["operation_status"] == "Succeeded"
    assert state.results[0].get_data()[0]["operation_url"] == OP


@pytest.mark.parametrize("code", [200, 204])
def test_synchronous_completion_needs_no_poll(run_action, code):
    state = run_action([httpx.Response(code)], wait_for_completion=True)
    assert state.status is True
    state.send.assert_called_once()
    assert state.sleeps == []
    assert state.results[0].get_data()[0]["operation_status"] == "Succeeded"


@pytest.mark.parametrize("remote_state", ["Failed", "Canceled", "Cancelled"])
def test_failed_start_preserves_inputs_error_and_operation_url(
    run_action, remote_state
):
    state = run_action(
        [
            accepted(),
            response(
                payload={"status": remote_state, "error": {"message": "quota exceeded"}}
            ),
        ],
        wait_for_completion=True,
    )
    assert state.status is False
    result = state.results[0]
    assert result.get_param() == state.params.model_dump(by_alias=True)
    assert result.get_data()[0]["operation_status"] == remote_state
    assert result.get_data()[0]["operation_url"] == OP
    assert "quota exceeded" in result.get_message()
    assert result.get_summary()["status"] == result.get_message()
    assert state.send.call_count == 2


def test_timeout_preserves_pending_state_without_restarting_vm(run_action):
    state = run_action(
        [accepted(), response(payload={"status": "InProgress"})],
        wait_for_completion=True,
        wait_timeout_seconds=5,
    )
    assert state.status is False
    assert state.now == 5
    assert state.send.call_count == 2
    result = state.results[0]
    assert "completion not confirmed" in result.get_message()
    assert "5-second" in result.get_message()
    assert result.get_param() == state.params.model_dump(by_alias=True)
    assert result.get_data()[0]["operation_url"] == OP
    assert result.get_data()[0]["operation_status"] == "InProgress"
    assert state.send.call_args_list[1].kwargs["timeout"] == 2


@pytest.mark.parametrize("timeout", [0, -1])
def test_invalid_timeout_fails_before_starting_vm(run_action, timeout):
    state = run_action([], wait_for_completion=True, wait_timeout_seconds=timeout)
    assert state.status is False
    state.send.assert_not_called()
    assert (
        "wait_timeout_seconds must be greater than zero"
        in state.results[0].get_message()
    )


def test_poll_permission_error_keeps_safe_recovery_context(run_action):
    state = run_action(
        [accepted(), response(403, {"error": {"message": "monitoring denied"}})],
        wait_for_completion=True,
    )
    assert state.status is False
    result = state.results[0]
    assert "completion not confirmed" in result.get_message()
    assert "monitoring denied" in result.get_message()
    assert result.get_data()[0]["operation_url"] == OP
    assert result.get_data()[0]["operation_status"] == "InProgress"


@pytest.mark.parametrize(
    "headers", [{}, {"Azure-AsyncOperation": "https://untrusted.example/op"}]
)
def test_tracking_headers_fail_safely_after_submission(run_action, headers):
    state = run_action([accepted(headers)], wait_for_completion=True)
    assert state.status is False
    state.send.assert_called_once()
    assert state.results[0].get_data()[0]["operation_url"] is None
    assert "completion not confirmed" in state.results[0].get_message()


def test_location_only_completion_is_supported(run_action):
    state = run_action(
        [accepted({"Location": LOCATION}), response(202), response(204)],
        wait_for_completion=True,
    )
    assert state.status is True
    assert [call.args[1] for call in state.send.call_args_list[1:]] == [
        LOCATION,
        LOCATION,
    ]
    assert state.results[0].get_data()[0]["operation_url"] == LOCATION


def test_registered_wait_inputs_are_optional_with_compatible_defaults():
    metadata = app.get_actions()["start_vm"].meta.model_dump()["parameters"]
    assert metadata["wait_for_completion"]["required"] is False
    assert metadata["wait_for_completion"]["default"] is False
    assert metadata["wait_timeout_seconds"]["required"] is False
    assert metadata["wait_timeout_seconds"]["default"] == 300


def test_failed_synchronous_response_is_not_reported_as_started(run_action):
    state = run_action(
        [
            response(
                payload={"status": "Failed", "error": {"message": "quota exceeded"}}
            )
        ],
        wait_for_completion=True,
    )
    assert state.status is False
    assert "quota exceeded" in state.results[0].get_message()
    assert state.results[0].get_data()[0]["operation_status"] == "Failed"
    state.send.assert_called_once()


def test_malformed_status_after_submission_preserves_operation(run_action):
    state = run_action([accepted(), response(payload={})], wait_for_completion=True)
    assert state.status is False
    assert "completion not confirmed" in state.results[0].get_message()
    assert state.results[0].get_data()[0]["operation_url"] == OP
