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
"""Verify authentication retries without replaying successful mutations."""

from types import SimpleNamespace

import httpx
import pytest

from src import helper
from src.consts import MS_AZURE_INVALID_TOKEN_MSGS


@pytest.fixture
def request_transport(monkeypatch):
    requests = []
    tokens = []
    responses = []
    client_class = httpx.Client

    def send(request):
        requests.append(request)
        return responses.pop(0)

    def get_token(asset, *, force_renew=False):
        tokens.append(force_renew)
        return "renewed-token" if force_renew else "initial-token"

    monkeypatch.setattr(helper, "get_access_token", get_token)
    monkeypatch.setattr(
        httpx,
        "Client",
        lambda **kwargs: client_class(transport=httpx.MockTransport(send), **kwargs),
    )
    return SimpleNamespace(requests=requests, tokens=tokens, responses=responses)


@pytest.mark.parametrize("phrase", MS_AZURE_INVALID_TOKEN_MSGS)
@pytest.mark.parametrize("status_code", [200, 201, 202, 400, 403, 500])
def test_response_text_does_not_replay_request(request_transport, status_code, phrase):
    response = httpx.Response(status_code, json={"message": phrase})
    request_transport.responses.append(response)

    result = helper._send_request(
        SimpleNamespace(admin_consent=True),
        "https://management.azure.com/subscriptions/sub/operation",
        method="POST",
        json_body={"commandId": "RunShellScript"},
    )

    assert result is response
    assert len(request_transport.requests) == 1
    assert request_transport.tokens == [False]


@pytest.mark.parametrize("retry_status", [200, 401])
def test_401_renews_and_retries_once(request_transport, retry_status):
    request_transport.responses.extend(
        [httpx.Response(401), httpx.Response(retry_status)]
    )

    response = helper._send_request(
        SimpleNamespace(admin_consent=True),
        "https://management.azure.com/subscriptions/sub/operation",
        method="POST",
        params={"api-version": "2017-03-30"},
        headers={"X-Probe": "retained"},
        json_body={"commandId": "RunShellScript"},
    )

    assert response.status_code == retry_status
    assert request_transport.tokens == [False, True]
    first, retried = request_transport.requests
    assert first.headers["Authorization"] == "Bearer initial-token"
    assert retried.headers["Authorization"] == "Bearer renewed-token"
    assert first.method == retried.method == "POST"
    assert first.url == retried.url
    assert first.content == retried.content
    assert retried.headers["X-Probe"] == "retained"
