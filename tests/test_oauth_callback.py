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
"""Tests for OAuth callback state validation."""

from types import SimpleNamespace

from soar_sdk.auth import AuthorizationCodeFlow, ClientCredentialsFlow
from soar_sdk.auth.client import SOARAssetOAuthClient
from src.app import oauth_callback
from src.auth import (
    get_authorization_flow,
    get_azure_oauth_client,
    get_client_credentials_flow,
)
from src.consts import MS_AZURE_CODE_GENERATION_SCOPE, MS_AZURE_RESOURCE


class FakeAuthState:
    def __init__(self, state=None):
        self.state = dict(state or {})

    def get_all(self, force_reload=False):
        return dict(self.state)

    def put_all(self, state):
        self.state = dict(state)


def make_request(state):
    asset = SimpleNamespace(
        auth_state=FakeAuthState({"azure_admin_consent_state": "expected-state"}),
        client_id="client-id",
        tenant_id="tenant-id",
    )
    request = SimpleNamespace(
        asset=asset,
        query={"admin_consent": ["true"], "state": [state]},
    )
    return request, asset


def test_admin_consent_callback_rejects_wrong_state():
    request, asset = make_request("wrong-state")

    response = oauth_callback(request)

    assert response.status_code == 400
    assert "azure_admin_consent" not in asset.auth_state.get_all()


def test_admin_consent_callback_records_consent_for_matching_state():
    request, asset = make_request("expected-state")

    response = oauth_callback(request)

    state = asset.auth_state.get_all()
    assert response.status_code == 200
    assert state["azure_admin_consent"] is True
    assert "azure_admin_consent_state" not in state


def make_asset():
    return SimpleNamespace(
        auth_state=FakeAuthState(),
        client_id="client-id",
        client_secret="client-secret",
        tenant_id="tenant-id",
    )


def test_delegated_auth_uses_sdk_flow_and_legacy_scope():
    flow = get_authorization_flow(
        make_asset(), "asset-id", "https://phantom.example/oauth_callback"
    )

    assert isinstance(flow, AuthorizationCodeFlow)
    assert flow._config.scope == MS_AZURE_CODE_GENERATION_SCOPE
    assert flow._extra_token_params is None


def test_client_credentials_auth_uses_sdk_flow_and_arm_resource():
    flow = get_client_credentials_flow(make_asset())

    assert isinstance(flow, ClientCredentialsFlow)
    assert flow._extra_params == {"resource": MS_AZURE_RESOURCE}


def test_delegated_token_refresh_uses_sdk_oauth_client():
    client = get_azure_oauth_client(make_asset())

    assert type(client) is SOARAssetOAuthClient
