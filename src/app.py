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
import time
from hmac import compare_digest

from soar_sdk.abstract import SOARClient
from soar_sdk.app import App
from soar_sdk.asset import AssetField, BaseAsset, FieldCategory
from soar_sdk.auth import create_oauth_callback_handler
from soar_sdk.exceptions import ActionFailure
from soar_sdk.logging import getLogger
from soar_sdk.webhooks.models import WebhookRequest, WebhookResponse

from .auth import (
    build_admin_consent_url,
    create_admin_consent_state,
    get_access_token,
    get_authorization_flow,
    get_azure_oauth_client,
    grant_admin_consent,
    is_client_credentials,
)
from .consts import VM_LIST_VMS_ALL_ENDPOINT
from .helper import make_azure_request

logger = getLogger()


class Asset(BaseAsset):
    subscription_id: str = AssetField(
        description="Subscription ID", category=FieldCategory.CONNECTIVITY
    )
    tenant_id: str = AssetField(
        description="Tenant ID", category=FieldCategory.CONNECTIVITY
    )
    client_id: str = AssetField(
        description="Application (client) ID assigned to your Azure Compute app",
        category=FieldCategory.CONNECTIVITY,
    )
    client_secret: str = AssetField(
        description="Client Secret", sensitive=True, category=FieldCategory.CONNECTIVITY
    )
    admin_access: bool = AssetField(
        description="Admin Access Required",
        default=True,
        category=FieldCategory.CONNECTIVITY,
    )
    admin_consent: bool = AssetField(
        description="Admin consent already provided",
        default=True,
        category=FieldCategory.CONNECTIVITY,
    )


app = App(
    name="Microsoft Azure Compute",
    app_type="virtualization",
    logo="logo_microsoftazurecompute.svg",
    logo_dark="logo_microsoftazurecompute_dark.svg",
    product_vendor="Microsoft",
    product_name="Azure Compute",
    publisher="Splunk",
    appid="39c7128b-666b-4a16-9d44-afab6a9b825d",
    fips_compliant=True,
    encrypt_cache_state=True,
    encrypt_ingest_state=True,
    asset_cls=Asset,
).enable_webhooks(default_requires_auth=False)


@app.test_connectivity()
def test_connectivity(soar: SOARClient, asset: Asset) -> None:
    redirect_uri = app.get_webhook_url("oauth_callback")

    if not is_client_credentials(asset):
        flow = get_authorization_flow(asset, soar.get_asset_id(), redirect_uri)
        if asset.admin_access:
            consent_state = create_admin_consent_state(asset)
            consent_url = build_admin_consent_url(asset, redirect_uri, consent_state)
            logger.info(
                f"Please authorize administrator access using URL: {consent_url}"
            )
            for _ in range(40):
                time.sleep(3)
                auth_state = asset.auth_state.get_all(force_reload=True)
                if auth_state.get("azure_admin_consent"):
                    break
            else:
                raise ActionFailure(
                    "Administrator consent was not received before timeout"
                )

        authorization_url = flow.get_authorization_url()
        logger.info(
            f"Please authorize user in a separate tab using URL: {authorization_url}"
        )
        flow.wait_for_authorization(
            on_progress=lambda iteration: logger.progress(
                f"Waiting for authorization... ({iteration})"
            )
        )

    get_access_token(asset, force_renew=is_client_credentials(asset))
    make_azure_request(asset, VM_LIST_VMS_ALL_ENDPOINT)


@app.webhook("oauth_callback")
def oauth_callback(request: WebhookRequest[Asset]) -> WebhookResponse:
    query = {key: values[0] if values else "" for key, values in request.query.items()}
    admin_consent = query.get("admin_consent")
    if admin_consent is not None:
        auth_state = request.asset.auth_state.get_all(force_reload=True)
        expected_state = auth_state.get("azure_admin_consent_state", "")
        callback_state = query.get("state", "")
        if (
            not expected_state
            or not callback_state
            or not compare_digest(expected_state, callback_state)
        ):
            return WebhookResponse.text_response(
                content="Invalid or expired authorization state", status_code=400
            )
        if admin_consent.lower() != "true":
            return WebhookResponse.text_response(
                content="Admin Consent declined. Please close this window and try again later.",
                status_code=400,
            )
        grant_admin_consent(request.asset)
        return WebhookResponse.text_response(
            content="Admin Consent received. Please close this window.", status_code=200
        )

    handler = create_oauth_callback_handler(
        lambda asset: get_azure_oauth_client(
            asset, app.get_webhook_url("oauth_callback")
        )
    )
    return handler(request)


from . import actions  # noqa: F401
