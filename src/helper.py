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
from contextlib import suppress
import re
import time
from urllib.parse import urlparse

from soar_sdk.action_results import ActionOutput, ActionResult
from soar_sdk.auth import create_oauth_client
from soar_sdk.params import Params
from soar_sdk.exceptions import ActionFailure

from .auth import get_access_token, is_client_credentials, oauth_config
from .consts import (
    MS_AZURE_ERR_MSG,
    MS_AZURE_INVALID_TOKEN_MSGS,
    MS_AZURE_SERVER_ERR_MSG,
    MS_BASE_URL,
    VM_ACTION_ENDPOINT,
)


def is_safe_arm_path_value(value: str) -> bool:
    return (
        isinstance(value, str)
        and bool(value)
        and value not in {".", ".."}
        and re.fullmatch(r"[^/%?#\\\x00-\x1f\x7f]+", value) is not None
    )


def validate_arm_path_value(value: str, field_name: str) -> str:
    if not is_safe_arm_path_value(value):
        raise ValueError(f"Please provide a valid {field_name} path value")
    return value


def format_vm_action_endpoint(
    resource_group_name: str, vm_name: str, action: str
) -> str:
    action = validate_arm_path_value(action.strip("/"), "action")
    return VM_ACTION_ENDPOINT.format(
        resourceGroupName=resource_group_name,
        vmName=vm_name,
        action=action,
    )


def resolve_subscription(asset, override: str | None = None) -> str:
    value = override or asset.subscription_id
    return validate_arm_path_value(value, "subscription_id")


def is_allowed_arm_url(value: str) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    return parsed.scheme == "https" and parsed.netloc == "management.azure.com"


def _send_request(
    asset,
    url: str,
    *,
    method: str = "GET",
    params=None,
    headers: dict[str, str] | None = None,
    json_body=None,
    data=None,
    verify: bool = True,
    timeout: float = 30.0,
):
    import httpx  # noqa: PLC0415

    request_headers = {"Accept": "application/json"}
    if json_body is not None or data is not None:
        request_headers["Content-Type"] = "application/json"
    for header_name, header_value in (headers or {}).items():
        existing_name = next(
            (
                name
                for name in request_headers
                if name.lower() == header_name.lower()
            ),
            None,
        )
        if existing_name is not None:
            del request_headers[existing_name]
        request_headers[header_name] = header_value

    def send_with_token(token: str):
        outgoing_headers = {
            name: value
            for name, value in request_headers.items()
            if name.lower() != "authorization"
        }
        outgoing_headers["Authorization"] = f"Bearer {token}"
        with httpx.Client(timeout=timeout, verify=verify, follow_redirects=True) as client:
            return client.request(
                method,
                url,
                headers=outgoing_headers,
                params=params,
                json=json_body,
                data=data,
            )

    try:
        if not is_client_credentials(asset):
            with create_oauth_client(
                asset,
                client_id=asset.client_id,
                client_secret=asset.client_secret,
                token_endpoint=oauth_config(asset).token_endpoint,
                timeout=timeout,
                verify=verify,
                follow_redirects=True,
            ) as client:
                return client.request(
                    method,
                    url,
                    headers=request_headers,
                    params=params,
                    json=json_body,
                    data=data,
                )

        response = send_with_token(get_access_token(asset))
        if response.status_code == 401 or any(
            phrase in response.text for phrase in MS_AZURE_INVALID_TOKEN_MSGS
        ):
            response = send_with_token(get_access_token(asset, force_renew=True))
        return response
    except httpx.RequestError as exc:
        raise ActionFailure(f"Error connecting to server: {exc}") from exc


def _response_data(response):
    if 200 <= response.status_code < 399:
        if not response.text:
            return {}
        try:
            return response.json()
        except (ValueError, json.JSONDecodeError) as exc:
            raise ActionFailure(f"Unable to parse JSON response: {exc}") from exc

    message = None
    try:
        payload = response.json()
    except ValueError:
        payload = None
    if isinstance(payload, dict):
        error = payload.get("error")
        if isinstance(error, dict):
            code = error.get("code")
            detail = error.get("message")
            if detail:
                message = f"{MS_AZURE_SERVER_ERR_MSG}. {detail}"
                if code:
                    message += f". Response code from server: {code}"
        elif error:
            message = f"{MS_AZURE_SERVER_ERR_MSG}. {error}"
    if message is None:
        message = response.text or "Empty response and no information in the header"
    raise ActionFailure(
        MS_AZURE_ERR_MSG.format(status_code=response.status_code, err_msg=message)
    )


def make_azure_request(
    asset,
    endpoint: str,
    *,
    subscription_id: str | None = None,
    method: str = "GET",
    params=None,
    json_body=None,
    data=None,
):
    subscription = resolve_subscription(asset, subscription_id)
    url = f"{MS_BASE_URL.format(subscriptionId=subscription)}{endpoint}"
    response = _send_request(
        asset, url, method=method, params=params, json_body=json_body, data=data
    )
    return _response_data(response)


def make_azure_collection_request(
    asset,
    endpoint: str,
    *,
    subscription_id: str | None = None,
) -> tuple[list, str | None]:
    """Fetch every page of an ARM collection, retaining items on later-page errors."""
    response = make_azure_request(
        asset, endpoint, subscription_id=subscription_id
    )
    if not isinstance(response, dict):
        raise ActionFailure("Azure returned an invalid collection response")

    values = response.get("value", [])
    if not isinstance(values, list):
        raise ActionFailure("Azure returned an invalid collection response")

    next_link = response.get("nextLink")
    seen_links = set()
    while next_link:
        if not is_allowed_arm_url(next_link):
            return values, "Azure returned an invalid pagination URL"
        if next_link in seen_links:
            return values, "Azure returned a repeated pagination URL"
        seen_links.add(next_link)

        try:
            page = make_absolute_request(asset, next_link)
        except (ActionFailure, ValueError) as exc:
            return values, f"Unable to retrieve the next Azure page: {exc}"

        if not isinstance(page, dict):
            return values, "Azure returned an invalid paginated collection response"
        page_values = page.get("value", [])
        if not isinstance(page_values, list):
            return values, "Azure returned an invalid paginated collection response"
        values.extend(page_values)
        next_link = page.get("nextLink")

    return values, None


def make_absolute_request(asset, url: str, *, method: str = "GET"):
    if not is_allowed_arm_url(url):
        raise ValueError("Please provide a valid Azure management URL")
    response = _send_request(asset, url, method=method)
    return _response_data(response)


def make_async_request(
    asset,
    endpoint: str,
    *,
    subscription_id: str | None = None,
    method: str = "POST",
    json_body=None,
):
    subscription = resolve_subscription(asset, subscription_id)
    url = f"{MS_BASE_URL.format(subscriptionId=subscription)}{endpoint}"
    response = _send_request(asset, url, method=method, json_body=json_body)
    if response.status_code == 202:
        operation_url = response.headers.get("Azure-AsyncOperation")
        location_url = response.headers.get("Location")
        if not operation_url or not location_url:
            raise ActionFailure("Azure did not return asynchronous operation URLs")
        if not is_allowed_arm_url(operation_url) or not is_allowed_arm_url(
            location_url
        ):
            raise ActionFailure("Azure returned an invalid asynchronous operation URL")

        state = "InProgress"
        attempts = 0
        while attempts < 20 or state == "InProgress":
            time.sleep(3)
            status_data = make_absolute_request(asset, operation_url)
            state = status_data.get("status") if isinstance(status_data, dict) else None
            attempts += 1
        return make_absolute_request(asset, location_url), location_url

    if response.status_code != 200:
        return _response_data(response), None
    return _response_data(response), None


def parse_command_list(value: str | None, field_name: str, *, allow_plain_text: bool):

    if not value:
        return value
    try:
        parsed = json.loads(value)
    except ValueError as exc:
        if allow_plain_text:
            return [value]
        raise ActionFailure(f"'{field_name}' input is not a JSON dictionary") from exc
    return parsed if isinstance(parsed, list) else [parsed]


def normalize_command_results(response, results_url: str | None) -> dict:

    if isinstance(response, list):
        results = list(response)
        for result in results:
            if result.get("message"):
                with suppress(TypeError, ValueError):
                    result["message"] = json.loads(result["message"])
    else:
        results = response
    return {"results_url": results_url, "results": results}


def vm_mutation_output_fields(
    response,
    *,
    resource_group_name: str,
    vm_name: str,
) -> dict:
    """Keep Azure response fields alongside the VM mutation output fields."""
    if isinstance(response, dict):
        fields = dict(response)
    elif response is not None:
        fields = {"azure_response": response}
    else:
        fields = {}

    fields.update(
        resource_group_name=resource_group_name,
        vm_name=vm_name,
    )
    return fields


def failed_table_result(
    message: str,
    params: dict,
    output: ActionOutput,
    summary: ActionOutput | None = None,
) -> ActionResult:
    """Return a failed action result while retaining table data and input parameters."""
    result = ActionResult(status=False, message=message, param=params)
    result.add_data(output.model_dump(by_alias=True))
    if summary is not None:
        result.set_summary(summary.model_dump(by_alias=True))
    return result


def failed_collection_result(
    message: str,
    params: dict,
    outputs: list[ActionOutput],
    summary: ActionOutput | None = None,
) -> ActionResult:
    """Return a failed collection result while retaining rows collected so far."""
    result = ActionResult(status=False, message=message, param=params)
    for output in outputs:
        result.add_data(output.model_dump(by_alias=True))
    if summary is not None:
        result.set_summary(summary.model_dump(by_alias=True))
    return result


def make_view_result(
    outputs: list[ActionOutput],
    action_params: list[Params],
    param_fields: dict[str, str],
) -> dict:
    """Group view rows by their SDK-provided action parameters."""
    groups: dict[tuple, dict] = {}
    for output, params in zip(outputs, action_params, strict=True):
        param = {name: getattr(params, field) for name, field in param_fields.items()}
        key = tuple(param.values())
        if key not in groups:
            groups[key] = {"data": [], "param": param, "summary": {}}
        groups[key]["data"].append(output.model_dump())

    if not groups:
        return {"results": [{"data": [], "param": {}, "summary": {}}]}
    return {"results": list(groups.values())}
