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
import json
import re
from typing import Any
from urllib.parse import unquote, urlsplit

from soar_sdk.action_results import MakeRequestOutput
from soar_sdk.exceptions import ActionFailure
from soar_sdk.params import MakeRequestParams, Param

from ..app import Asset, app
from ..consts import MS_BASE_URL
from ..helper import _send_request, resolve_subscription

DEFAULT_REQUEST_TIMEOUT_SECONDS = 30
INVALID_ENDPOINT_MESSAGE = (
    "Invalid endpoint: {endpoint}. Provide an ARM path within the configured "
    "subscription, such as '/resourceGroups/<name>/providers/"
    "Microsoft.Compute/virtualMachines', without the base URL or a "
    "'/subscriptions/...' prefix."
)


class AzureComputeMakeRequestParams(MakeRequestParams):
    endpoint: str = Param(
        description=(
            "Azure Resource Manager endpoint path relative to the configured "
            "subscription. Example: '/resourceGroups/{resourceGroupName}/"
            "providers/Microsoft.Compute/virtualMachines'. Pass api-version and "
            "other query values in query_parameters. Do not include the base URL "
            "or a '/subscriptions/{subscriptionId}' prefix."
        ),
        required=True,
    )


def _get_endpoint(endpoint: str) -> str:
    endpoint = endpoint.strip()
    parsed = urlsplit(endpoint)
    path = unquote(parsed.path)
    segments = path.split("/")

    invalid = (
        not path
        or bool(parsed.scheme or parsed.netloc or parsed.query or parsed.fragment)
        or "\\" in path
        or "//" in path
        or any(segment in {".", ".."} for segment in segments)
        or any(ord(char) < 32 or ord(char) == 127 for char in path)
        or path.casefold() == "/subscriptions"
        or path.casefold().startswith("/subscriptions/")
        or re.search(r"%(?:2f|5c)", endpoint, re.IGNORECASE) is not None
    )
    if invalid:
        raise ActionFailure(INVALID_ENDPOINT_MESSAGE.format(endpoint=endpoint))

    raw_path = parsed.path
    return raw_path if raw_path.startswith("/") else f"/{raw_path}"


def _get_headers(params: AzureComputeMakeRequestParams) -> dict[str, str]:
    headers = {"Accept": "application/json"}
    if not params.headers:
        if params.body:
            headers["Content-Type"] = "application/json"
        return headers

    try:
        parsed_headers = json.loads(params.headers)
    except (json.JSONDecodeError, TypeError) as exc:
        raise ActionFailure(f"Invalid JSON headers: {params.headers}") from exc

    if not isinstance(parsed_headers, dict):
        raise ActionFailure(f"Invalid JSON headers: {params.headers}")
    if any(not isinstance(value, str) for value in parsed_headers.values()):
        raise ActionFailure("Header values must be strings")

    headers.update(parsed_headers)
    if params.body and not any(key.lower() == "content-type" for key in headers):
        headers["Content-Type"] = "application/json"
    return headers


def _get_query_parameters(
    params: AzureComputeMakeRequestParams,
    endpoint: str,
) -> tuple[str, dict[str, Any] | None]:
    if not params.query_parameters:
        return endpoint, None

    try:
        parsed_params = json.loads(params.query_parameters)
    except (json.JSONDecodeError, TypeError):
        query_string = params.query_parameters.lstrip("?")
        return f"{endpoint}?{query_string}", None

    if not isinstance(parsed_params, dict):
        raise ActionFailure(f"Invalid query parameters: {params.query_parameters}")

    return endpoint, parsed_params


def _get_body(
    params: AzureComputeMakeRequestParams, headers: dict[str, str]
) -> tuple[Any, str | None]:
    if not params.body:
        return None, None

    content_type = next(
        (value for key, value in headers.items() if key.lower() == "content-type"), ""
    )
    if "json" not in content_type.lower():
        return None, params.body

    try:
        return json.loads(params.body), None
    except (json.JSONDecodeError, TypeError) as exc:
        raise ActionFailure(f"Invalid JSON body: {params.body}") from exc


@app.make_request()
def make_request(
    params: AzureComputeMakeRequestParams, asset: Asset
) -> MakeRequestOutput:
    """Make an authenticated request to Azure Resource Manager."""
    endpoint = _get_endpoint(params.endpoint)
    headers = _get_headers(params)
    endpoint, query_parameters = _get_query_parameters(params, endpoint)
    json_body, data = _get_body(params, headers)
    timeout = (
        params.timeout
        if params.timeout is not None
        else DEFAULT_REQUEST_TIMEOUT_SECONDS
    )
    if timeout <= 0:
        raise ActionFailure("Request timeout must be greater than zero")

    subscription_id = resolve_subscription(asset)
    url = f"{MS_BASE_URL.format(subscriptionId=subscription_id)}{endpoint}"
    response = _send_request(
        asset,
        url,
        method=params.http_method,
        params=query_parameters,
        headers=headers,
        json_body=json_body,
        data=data,
        verify=params.verify_ssl,
        timeout=timeout,
    )

    return MakeRequestOutput(
        status_code=response.status_code,
        response_body=response.text,
    )
