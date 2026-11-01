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
import secrets
from urllib.parse import urlencode

from soar_sdk.auth import AuthorizationCodeFlow, ClientCredentialsFlow
from soar_sdk.auth.client import (
    AuthorizationRequiredError,
    SOARAssetOAuthClient,
    TokenExpiredError,
)
from soar_sdk.auth.models import OAuthConfig, OAuthGrantType

from .consts import MS_AZURE_CODE_GENERATION_SCOPE, MS_AZURE_RESOURCE, SERVER_TOKEN_URL


def oauth_config(asset, redirect_uri: str | None = None) -> OAuthConfig:
    tenant = asset.tenant_id
    return OAuthConfig(
        client_id=asset.client_id,
        client_secret=asset.client_secret,
        authorization_endpoint=(
            f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize"
        ),
        token_endpoint=f"https://login.microsoftonline.com/{tenant}/oauth2/token",
        redirect_uri=redirect_uri,
        scope=None,
        grant_type=OAuthGrantType.AUTHORIZATION_CODE,
    )


def get_azure_oauth_client(
    asset, redirect_uri: str | None = None
) -> SOARAssetOAuthClient:
    return SOARAssetOAuthClient(oauth_config(asset, redirect_uri), asset.auth_state)


def get_authorization_flow(
    asset, asset_id: str, redirect_uri: str
) -> AuthorizationCodeFlow:
    return AuthorizationCodeFlow(
        asset.auth_state,
        str(asset_id),
        client_id=asset.client_id,
        client_secret=asset.client_secret,
        authorization_endpoint=(
            f"https://login.microsoftonline.com/{asset.tenant_id}/oauth2/v2.0/authorize"
        ),
        token_endpoint=f"https://login.microsoftonline.com/{asset.tenant_id}/oauth2/token",
        redirect_uri=redirect_uri,
        scope=MS_AZURE_CODE_GENERATION_SCOPE,
        use_pkce=False,
        poll_timeout=120,
        poll_interval=3,
    )


def get_client_credentials_flow(asset) -> ClientCredentialsFlow:
    return ClientCredentialsFlow(
        asset.auth_state,
        client_id=asset.client_id,
        client_secret=asset.client_secret,
        token_endpoint=SERVER_TOKEN_URL.format(asset.tenant_id),
        extra_params={"resource": MS_AZURE_RESOURCE},
    )


def is_client_credentials(asset) -> bool:
    return bool(asset.admin_consent)


def create_admin_consent_state(asset) -> str:
    state = secrets.token_urlsafe(32)
    auth_state = dict(asset.auth_state.get_all())
    auth_state["azure_admin_consent_state"] = state
    asset.auth_state.put_all(auth_state)
    return state


def grant_admin_consent(asset) -> None:
    auth_state = dict(asset.auth_state.get_all())
    auth_state["azure_admin_consent"] = True
    auth_state.pop("azure_admin_consent_state", None)
    asset.auth_state.put_all(auth_state)


def build_admin_consent_url(asset, redirect_uri: str, state: str) -> str:
    query = urlencode(
        {
            "client_id": asset.client_id,
            "redirect_uri": redirect_uri,
            "state": state,
        }
    )
    return f"https://login.microsoftonline.com/{asset.tenant_id}/adminconsent?{query}"


def get_access_token(asset, *, force_renew: bool = False) -> str:
    if is_client_credentials(asset):
        flow = get_client_credentials_flow(asset)
        token = flow.authenticate() if force_renew else flow.get_token()
        return token.access_token

    client = get_azure_oauth_client(asset)
    try:
        token = client.get_valid_token(auto_refresh=False)
        if not force_renew:
            return token.access_token
    except TokenExpiredError:
        token = client.get_stored_token()

    if token and token.refresh_token:
        return client.refresh_token(token.refresh_token).access_token
    raise AuthorizationRequiredError(
        "Unexpected OAuth state. Please run test connectivity first."
    )
