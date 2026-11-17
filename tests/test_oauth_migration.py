# Copyright (c) 2026 Splunk Inc.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# https://www.apache.org/licenses/LICENSE-2.0
"""Upgrade coverage for legacy delegated OAuth credentials."""

from contextlib import contextmanager
from copy import deepcopy
from types import SimpleNamespace

import httpx
import pytest
from soar_sdk.auth.models import OAuthToken
from soar_sdk.exceptions import ActionFailure

from src import auth, helper


class State:
    asset_id = "asset-id"

    def __init__(self, legacy, current=None):
        self.current = current or {}
        self.writes = 0
        self.backend = SimpleNamespace(load_state=lambda: legacy)

    def get_all(self):
        return deepcopy(self.current)

    def put_all(self, value):
        self.current = deepcopy(value)
        self.writes += 1


def asset(legacy, current=None, *, application=False):
    return SimpleNamespace(
        auth_state=State(legacy, current),
        admin_consent=application,
        tenant_id="tenant",
        client_id="client-id",
        client_secret="test-fixture",  # pragma: allowlist secret
    )


@pytest.mark.parametrize("encrypted", [False, True])
def test_migration_decrypts_only_encrypted_values_and_is_idempotent(
    monkeypatch, encrypted
):
    legacy = {
        "token": {
            "access_token": "access",
            "refresh_token": "refresh",
            "expires_in": 3600,
        }
    }
    if encrypted:
        legacy = {
            "is_encrypted": True,
            "token": {"access_token": "enc-access", "refresh_token": "enc-refresh"},
        }
    original = deepcopy(legacy)
    calls = []

    def decrypt(value, salt):
        calls.append((value, salt))
        return value.removeprefix("enc-")

    monkeypatch.setattr(auth.encryption_helper, "decrypt", decrypt)
    a = asset(legacy, {"unrelated": "preserved"})
    auth.migrate_legacy_oauth_state(a)
    auth.migrate_legacy_oauth_state(a)
    token = auth.get_azure_oauth_client(a).get_stored_token()
    assert token.access_token == "access"
    assert token.refresh_token == "refresh"
    assert token.is_expired()
    assert a.auth_state.current["unrelated"] == "preserved"
    assert a.auth_state.writes == 1
    assert legacy == original
    assert calls == (
        [("enc-access", "asset-id"), ("enc-refresh", "asset-id")] if encrypted else []
    )


def test_existing_sdk_token_wins():
    current = {"oauth": {"token": {"access_token": "newer"}, "client_id": "client-id"}}
    a = asset({"token": {"access_token": "older"}}, current)
    auth.migrate_legacy_oauth_state(a)
    assert a.auth_state.current == current
    assert a.auth_state.writes == 0


@pytest.mark.parametrize("legacy", [{}, {"token": None}, {"token": {}}, []])
def test_missing_legacy_credentials_are_noop(legacy):
    a = asset(legacy)
    auth.migrate_legacy_oauth_state(a)
    assert a.auth_state.writes == 0


def test_application_credentials_do_not_import_delegated_state():
    a = asset({"token": {"access_token": "older"}}, application=True)
    auth.migrate_legacy_oauth_state(a)
    assert a.auth_state.writes == 0


def test_decryption_failure_does_not_write_or_expose_credentials(monkeypatch):
    a = asset({"is_encrypted": True, "token": {"access_token": "ciphertext"}})

    def fail(*args):
        raise ValueError("ciphertext")

    monkeypatch.setattr(auth.encryption_helper, "decrypt", fail)
    with pytest.raises(ActionFailure, match="Run test connectivity") as error:
        auth.migrate_legacy_oauth_state(a)
    assert "ciphertext" not in str(error.value)
    assert a.auth_state.writes == 0


def test_first_token_request_refreshes_migrated_token(monkeypatch):
    a = asset({"token": {"refresh_token": "refresh"}})
    calls = []

    def refresh(self, value):
        calls.append(value)
        token = OAuthToken(access_token="fresh", refresh_token=value, expires_in=3600)
        self._store_token(token)
        return token

    monkeypatch.setattr(auth.SOARAssetOAuthClient, "refresh_token", refresh)
    assert auth.get_access_token(a) == "fresh"
    assert calls == ["refresh"]
    assert auth.get_access_token(a) == "fresh"
    assert calls == ["refresh"]


def test_http_request_migrates_before_sdk_client_creation(monkeypatch):
    a = asset({"token": {"access_token": "access", "refresh_token": "refresh"}})

    @contextmanager
    def client(asset, **kwargs):
        assert asset.auth_state.current["oauth"]["token"]["refresh_token"] == "refresh"
        yield SimpleNamespace(
            request=lambda *args, **kwargs: httpx.Response(200, json={})
        )

    monkeypatch.setattr(helper, "create_oauth_client", client)
    assert (
        helper._send_request(a, "https://management.azure.com/test").status_code == 200
    )


def test_pending_sdk_authorization_does_not_import_unreadable_legacy_token():
    current = {"oauth": {"session": {"state": "pending"}}}
    a = asset({"is_encrypted": True, "token": {"access_token": "unreadable"}}, current)
    auth.migrate_legacy_oauth_state(a)
    assert a.auth_state.current == current
    assert a.auth_state.writes == 0
