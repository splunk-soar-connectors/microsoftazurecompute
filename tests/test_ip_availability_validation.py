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
"""Preserve legacy address validation and isolate query values."""

from importlib import import_module
from types import SimpleNamespace

import pytest

from src.app import app


action_module = import_module("src.actions.check_address_availability")


@pytest.mark.parametrize(
    "address",
    ["10.0.0.4", "2001:db8::4", "2001:0db8:0:0:0:0:0:4", "::1"],
)
def test_valid_address_is_sent_as_query_data(monkeypatch, address):
    calls = []

    def request(asset, endpoint, **kwargs):
        calls.append((endpoint, kwargs))
        return {"available": True, "availableIPAddresses": []}

    monkeypatch.setattr(action_module, "make_azure_request", request)
    params = action_module.GetIpAvailabilityParams(
        resource_group_name="rg",
        virtual_network_name="vnet",
        ip_address=address,
        subscription_id="sub",
    )
    summaries = []

    result = action_module.check_address_availability.__wrapped__(
        params, SimpleNamespace(set_summary=summaries.append), object()
    )

    assert result == []
    endpoint, kwargs = calls[0]
    assert "?" not in endpoint
    assert kwargs["params"] == {"ipAddress": address, "api-version": "2018-11-01"}
    assert kwargs["subscription_id"] == "sub"
    assert summaries[0].available is True


@pytest.mark.parametrize(
    "address",
    [
        "",
        " ",
        " 10.0.0.4",
        "10.0.0.4 ",
        "999.1.1.1",
        "not-an-ip",
        "10.0.0.4,10.0.0.5",
        "10.0.0.0/24",
        "https://10.0.0.4",
        "10.0.0.4&api-version=bad",
        "10.0.0.4#fragment",
        "2001:db8::xyz",
    ],
)
def test_invalid_address_fails_with_parameters_before_request(monkeypatch, address):
    def unexpected_request(*args, **kwargs):
        pytest.fail("Invalid addresses must not reach Azure")

    monkeypatch.setattr(action_module, "make_azure_request", unexpected_request)
    results = []
    monkeypatch.setattr(
        app, "actions_manager", SimpleNamespace(add_result=results.append)
    )
    params = action_module.GetIpAvailabilityParams(
        resource_group_name="rg",
        virtual_network_name="vnet",
        ip_address=address,
        subscription_id="sub",
    )
    soar = SimpleNamespace(get_message=lambda: "", get_summary=lambda: None)

    status = action_module.check_address_availability(params, soar=soar, asset=object())

    assert status is False
    assert len(results) == 1
    assert results[0].get_param() == params.model_dump(by_alias=True)
    assert "IPv4 or IPv6" in results[0].get_message()
    assert "Traceback" not in results[0].get_message()
