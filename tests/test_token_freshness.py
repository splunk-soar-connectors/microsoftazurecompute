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
"""Tests for explicit token-generation operations."""

from importlib import import_module
from types import SimpleNamespace


def test_generate_token_forces_fresh_token(monkeypatch):
    action_module = import_module("src.actions.generate_token")
    calls = []
    monkeypatch.setattr(
        action_module,
        "get_access_token",
        lambda asset, *, force_renew=False: calls.append(force_renew),
    )
    soar = SimpleNamespace(set_message=lambda message: None)

    output = action_module.generate_token.__wrapped__(
        SimpleNamespace(), soar, SimpleNamespace()
    )

    assert calls == [True]
    assert output.model_dump() == {}


def test_client_credentials_connectivity_forces_fresh_token(monkeypatch):
    app_module = import_module("src.app")
    monkeypatch.setattr(
        app_module.app,
        "get_webhook_url",
        lambda route: "https://phantom.example/callback",
    )
    calls = []
    monkeypatch.setattr(
        app_module,
        "get_access_token",
        lambda asset, *, force_renew=False: calls.append(force_renew),
    )
    monkeypatch.setattr(app_module, "make_azure_request", lambda *args: None)
    soar = SimpleNamespace(get_asset_id=lambda: "asset-id")
    asset = SimpleNamespace(admin_consent=True, admin_access=False)

    app_module.test_connectivity.__wrapped__(soar, asset)

    assert calls == [True]


def test_delegated_connectivity_does_not_refresh_after_new_authorization(
    monkeypatch,
):
    app_module = import_module("src.app")
    monkeypatch.setattr(
        app_module.app,
        "get_webhook_url",
        lambda route: "https://phantom.example/callback",
    )
    calls = []

    class FakeFlow:
        def get_authorization_url(self):
            return "https://login.example/authorize"

        def wait_for_authorization(self, on_progress=None):
            return None

    monkeypatch.setattr(app_module, "get_authorization_flow", lambda *args: FakeFlow())
    monkeypatch.setattr(
        app_module,
        "get_access_token",
        lambda asset, *, force_renew=False: calls.append(force_renew),
    )
    monkeypatch.setattr(app_module, "make_azure_request", lambda *args: None)
    monkeypatch.setattr(app_module.time, "sleep", lambda seconds: None)
    soar = SimpleNamespace(get_asset_id=lambda: "asset-id", logger=None)
    asset = SimpleNamespace(admin_consent=False, admin_access=False)

    app_module.test_connectivity.__wrapped__(soar, asset)

    assert calls == [False]
