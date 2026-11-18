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
"""Exercise bounded Azure command tracking without real sleeps or requests."""

from types import SimpleNamespace
from importlib import import_module
from unittest.mock import Mock

import httpx
import pytest

from src import helper
from src.app import app
from src.helper import AsyncOperationError

OP = "https://management.azure.com/subscriptions/sub/operations/status"
RESULT = "https://management.azure.com/subscriptions/sub/operations/result"
ASSET = SimpleNamespace(subscription_id="sub")


def response(status=200, payload=None, **headers):
    return httpx.Response(
        status, json=payload if payload is not None else {}, headers=headers
    )


def accepted(**headers):
    return response(202, **{"Azure-AsyncOperation": OP, "Location": RESULT, **headers})


@pytest.fixture
def clock(monkeypatch):
    state = SimpleNamespace(now=0.0, sleeps=[])

    def sleep(delay):
        state.sleeps.append(delay)
        state.now += delay

    monkeypatch.setattr(helper.time, "monotonic", lambda: state.now)
    monkeypatch.setattr(helper.time, "sleep", sleep)
    return state


def execute(monkeypatch, responses):
    send = Mock(side_effect=responses)
    monkeypatch.setattr(helper, "_send_request", send)
    return send


def test_success_stops_at_first_terminal_status(monkeypatch, clock):
    result = {"properties": {"output": [{"message": "done"}]}}
    send = execute(
        monkeypatch,
        [
            accepted(),
            response(payload={"status": "Succeeded"}),
            response(payload=result),
        ],
    )
    assert helper.make_async_request(ASSET, "/run", json_body={"commandId": "cmd"}) == (
        result,
        RESULT,
    )
    assert clock.sleeps == [3]
    assert [call.args[1] for call in send.call_args_list] == [
        "https://management.azure.com/subscriptions/sub/run",
        OP,
        RESULT,
    ]
    assert send.call_args_list[0].kwargs["method"] == "POST"
    assert all(
        call.kwargs.get("method", "GET") == "GET" for call in send.call_args_list[1:]
    )


@pytest.mark.parametrize("state", ["Failed", "Canceled", "Cancelled"])
def test_remote_failure_keeps_error_and_tracking_urls(monkeypatch, clock, state):
    payload = {
        "status": state,
        "error": {"code": "Denied", "message": "guest rejected command"},
    }
    send = execute(monkeypatch, [accepted(), response(payload=payload)])
    with pytest.raises(AsyncOperationError, match="guest rejected command") as caught:
        helper.make_async_request(ASSET, "/run")
    error = caught.value
    assert error.operation_status == state
    assert error.response == payload
    assert error.operation_url == OP
    assert error.results_url == RESULT
    assert send.call_count == 2
    assert clock.sleeps == [3]


def test_pending_timeout_is_bounded_and_never_resubmits(monkeypatch, clock):
    send = execute(
        monkeypatch, [accepted()] + [response(payload={"status": "InProgress"})] * 30
    )
    with pytest.raises(AsyncOperationError, match="completion not confirmed") as caught:
        helper.make_async_request(ASSET, "/run")
    assert clock.now == 60
    assert send.call_count == 20
    assert caught.value.operation_status == "InProgress"
    assert caught.value.results_url == RESULT
    assert sum(call.kwargs.get("method") == "POST" for call in send.call_args_list) == 1
    assert all(0 < call.kwargs["timeout"] <= 30 for call in send.call_args_list[1:])


def test_retry_after_updates_and_is_capped_to_deadline(monkeypatch, clock):
    send = execute(
        monkeypatch,
        [
            accepted(**{"Retry-After": "7"}),
            response(payload={"status": "Running"}, **{"Retry-After": "120"}),
        ],
    )
    with pytest.raises(AsyncOperationError, match="completion not confirmed"):
        helper.make_async_request(ASSET, "/run")
    assert clock.sleeps == [7, 53]
    assert send.call_count == 2


@pytest.mark.parametrize("delay", ["bad", "-1", "0"])
def test_invalid_retry_after_uses_default(monkeypatch, clock, delay):
    execute(
        monkeypatch,
        [
            accepted(**{"Retry-After": delay}),
            response(payload={"status": "Succeeded"}),
            response(),
        ],
    )
    helper.make_async_request(ASSET, "/run")
    assert clock.sleeps == [3]


@pytest.mark.parametrize("failed_stage", ["status", "results"])
def test_http_failure_after_submission_preserves_last_state(
    monkeypatch, clock, failed_stage
):
    sequence = [accepted()]
    if failed_stage == "results":
        sequence.append(response(payload={"status": "Succeeded"}))
    sequence.append(
        response(403, {"error": {"code": "Denied", "message": "cannot read outcome"}})
    )
    send = execute(monkeypatch, sequence)
    with pytest.raises(AsyncOperationError, match="cannot read outcome") as caught:
        helper.make_async_request(ASSET, "/run")
    assert caught.value.results_url == RESULT
    assert caught.value.operation_url == OP
    assert caught.value.operation_status == (
        "Succeeded" if failed_stage == "results" else "InProgress"
    )
    assert send.call_count == len(sequence)


@pytest.mark.parametrize("payload", [[1], {}, {"status": None}])
def test_malformed_status_retains_recovery_context(monkeypatch, clock, payload):
    execute(monkeypatch, [accepted(), response(payload=payload)])
    with pytest.raises(AsyncOperationError, match="completion not confirmed") as caught:
        helper.make_async_request(ASSET, "/run")
    assert caught.value.results_url == RESULT


def test_location_only_tracking_does_not_fetch_result_twice(monkeypatch, clock):
    send = execute(
        monkeypatch,
        [
            response(202, Location=RESULT),
            response(202),
            response(payload={"value": [{"message": "done"}]}),
        ],
    )
    result, url = helper.make_async_request(ASSET, "/run")
    assert url == RESULT
    assert result["value"][0]["message"] == "done"
    assert send.call_count == 3


@pytest.mark.parametrize(
    "headers",
    [
        {},
        {"Location": "https://untrusted.example/result"},
        {"Azure-AsyncOperation": OP},
    ],
)
def test_missing_or_unsafe_urls_do_not_trigger_unsafe_requests(
    monkeypatch, clock, headers
):
    sequence = [response(202, **headers)]
    if headers == {"Azure-AsyncOperation": OP}:
        sequence.append(response(payload={"status": "Succeeded"}))
    send = execute(monkeypatch, sequence)
    with pytest.raises(AsyncOperationError) as caught:
        helper.make_async_request(ASSET, "/run")
    assert caught.value.results_url is None
    assert all("untrusted" not in call.args[1] for call in send.call_args_list)


def test_successful_submission_with_failed_result_is_not_success(monkeypatch, clock):
    execute(
        monkeypatch,
        [
            accepted(),
            response(payload={"status": "Succeeded"}),
            response(payload={"status": "Failed", "error": {"message": "guest error"}}),
        ],
    )
    with pytest.raises(AsyncOperationError, match="guest error"):
        helper.make_async_request(ASSET, "/run")


def test_synchronous_result_shape_unchanged(monkeypatch, clock):
    execute(monkeypatch, [response(payload={"value": []})])
    assert helper.make_async_request(ASSET, "/run") == ({"value": []}, None)
    assert not clock.sleeps


def test_real_action_failure_contains_params_summary_and_recovery_data(
    monkeypatch, clock
):
    module = import_module("src.actions.run_command")
    send = execute(monkeypatch, [accepted(**{"Retry-After": "60"})])
    results = []
    monkeypatch.setattr(
        app, "actions_manager", SimpleNamespace(add_result=results.append)
    )
    params = module.RunCommandParams(
        resource_group_name="rg", vm_name="vm", command_id="cmd", subscription_id="sub"
    )
    soar = SimpleNamespace(get_message=lambda: "", get_summary=lambda: None)
    assert module.run_command(params, soar=soar, asset=ASSET) is False
    result = results[0]
    assert result.get_param() == params.model_dump(by_alias=True)
    assert "completion not confirmed" in result.get_summary()["status"]
    data = result.get_data()[0]
    assert data["operation_url"] == OP
    assert data["results_url"] == RESULT
    assert data["operation_status"] == "InProgress"
    assert data["command_id"] == "cmd"
    assert send.call_count == 1


def test_result_not_yet_available_is_not_completed_action(monkeypatch, clock):
    execute(
        monkeypatch,
        [accepted(), response(payload={"status": "Succeeded"}), response(202)],
    )
    with pytest.raises(
        AsyncOperationError, match="results are not yet available"
    ) as caught:
        helper.make_async_request(ASSET, "/run")
    assert caught.value.operation_status == "Succeeded"
    assert caught.value.results_url == RESULT


def test_network_time_counts_against_polling_budget(monkeypatch, clock):
    calls = []

    def send(asset, url, **kwargs):
        calls.append((url, kwargs))
        if len(calls) == 1:
            return accepted()
        clock.now += 58
        return response(payload={"status": "Running"})

    monkeypatch.setattr(helper, "_send_request", send)
    with pytest.raises(AsyncOperationError, match="completion not confirmed"):
        helper.make_async_request(ASSET, "/run")
    assert len(calls) == 2
    assert clock.sleeps == [3]


@pytest.mark.parametrize("stage", ["remote_failure", "status_fetch", "result_fetch"])
def test_actual_action_retains_failure_outcome(monkeypatch, clock, stage):
    module = import_module("src.actions.run_command")
    denial = response(403, {"error": {"message": "read denied"}})
    sequences = {
        "remote_failure": [
            accepted(),
            response(
                payload={"status": "Failed", "error": {"message": "guest failed"}}
            ),
        ],
        "status_fetch": [accepted(), denial],
        "result_fetch": [accepted(), response(payload={"status": "Succeeded"}), denial],
    }
    execute(monkeypatch, sequences[stage])
    results = []
    monkeypatch.setattr(
        app, "actions_manager", SimpleNamespace(add_result=results.append)
    )
    params = module.RunCommandParams(
        resource_group_name="rg", vm_name="vm", command_id="cmd", subscription_id="sub"
    )
    soar = SimpleNamespace(get_message=lambda: "", get_summary=lambda: None)
    assert module.run_command(params, soar=soar, asset=ASSET) is False
    result = results[0]
    assert result.get_param() == params.model_dump(by_alias=True)
    assert result.get_data()[0]["results_url"] == RESULT
    assert result.get_data()[0]["operation_url"] == OP
    expected = {
        "remote_failure": "Failed",
        "status_fetch": "InProgress",
        "result_fetch": "Succeeded",
    }[stage]
    assert result.get_data()[0]["operation_status"] == expected
    assert result.get_summary()["status"] == result.get_message()


def test_synchronous_failed_operation_does_not_report_success(monkeypatch, clock):
    execute(
        monkeypatch,
        [response(payload={"status": "Failed", "error": {"message": "guest failed"}})],
    )
    with pytest.raises(AsyncOperationError, match="guest failed") as caught:
        helper.make_async_request(ASSET, "/run")
    assert caught.value.operation_status == "Failed"
    assert not clock.sleeps


def test_malformed_results_keeps_succeeded_state_and_urls(monkeypatch, clock):
    execute(
        monkeypatch,
        [
            accepted(),
            response(payload={"status": "Succeeded"}),
            response(payload="invalid"),
        ],
    )
    with pytest.raises(AsyncOperationError, match="invalid results response") as caught:
        helper.make_async_request(ASSET, "/run")
    assert caught.value.operation_status == "Succeeded"
    assert caught.value.results_url == RESULT
    assert caught.value.operation_url == OP
