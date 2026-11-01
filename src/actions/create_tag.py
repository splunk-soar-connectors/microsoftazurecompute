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
from soar_sdk.abstract import SOARClient
from soar_sdk.action_results import (
    ActionOutput,
    ActionResult,
    OutputField,
    PermissiveActionOutput,
)
from soar_sdk.params import Param, Params

from ..app import Asset, app
from soar_sdk.exceptions import ActionFailure
from ..helper import make_azure_request, validate_arm_path_value
from ..consts import VM_CREATE_TAG_ENDPOINT
from ..consts import VM_CREATE_TAG_VALUE_PART


class CreateTagParams(Params):
    tag_name: str = Param(
        description="The name of the tag",
        primary=True,
        cef_types=["vm management tag name"],
    )
    tag_value: str | None = Param(
        description="The value of the tag to create or update"
    )
    subscription_id: str | None = Param(
        description="Subscription ID to overwrite asset configuration value"
    )


class CountOutput(PermissiveActionOutput):
    type: str = OutputField(example_values=["Total"])
    value: float = OutputField(example_values=[0])


class CreateTagOutput(PermissiveActionOutput):
    tagName: str = OutputField(column_name="Tag Name", example_values=["QA1"])
    tagValue: str = OutputField(column_name="Tag Value", example_values=["QA"])
    count: CountOutput
    id: str = OutputField(
        example_values=[
            "/subscriptions/a81fccf8-0405-43ae-990c-ab1389e40c6d/tagNames/QA1"
        ]
    )


def await_request(endpoint, asset, subscription_id):
    return make_azure_request(
        asset, endpoint, subscription_id=subscription_id, method="PUT"
    )


def await_create_name(create_name):
    return create_name()


class CreateTagSummary(ActionOutput):
    status: str = OutputField(example_values=["Successfully created tag"])


@app.action(
    description="Create or update a tag",
    action_type="generic",
    read_only=False,
    summary_type=CreateTagSummary,
    render_as="table",
    output_class=CreateTagOutput,
)
def create_tag(
    params: CreateTagParams, soar: SOARClient, asset: Asset
) -> CreateTagOutput:

    tag_name = validate_arm_path_value(params.tag_name, "tag_name")
    tag_value = params.tag_value
    if tag_value:
        tag_value = validate_arm_path_value(tag_value, "tag_value")

    def create_name():
        endpoint = VM_CREATE_TAG_ENDPOINT.format(tagName=tag_name, tagValue="")
        return await_request(endpoint, asset, params.subscription_id)

    if not tag_value:
        response = await_create_name(create_name)
    else:
        value_part = VM_CREATE_TAG_VALUE_PART.format(tagValue=tag_value)
        endpoint = VM_CREATE_TAG_ENDPOINT.format(tagName=tag_name, tagValue=value_part)
        try:
            response = make_azure_request(
                asset, endpoint, subscription_id=params.subscription_id, method="PUT"
            )
        except ActionFailure as exc:
            if "PredefinedTagNameNotFound" not in str(exc):
                raise
            name_response = await_create_name(create_name)
            try:
                response = make_azure_request(
                    asset,
                    endpoint,
                    subscription_id=params.subscription_id,
                    method="PUT",
                )
            except ActionFailure as retry_error:
                if isinstance(name_response, dict):
                    partial_data = dict(name_response)
                elif name_response is not None:
                    partial_data = {"azure_response": name_response}
                else:
                    partial_data = {}
                partial_data.update(
                    tagName=params.tag_name,
                    tagValue=tag_value,
                    failed_stage="create_tag_value",
                )
                result = ActionResult(
                    status=False,
                    message=str(retry_error),
                    param=params.model_dump(),
                )
                result.add_data(partial_data)
                return result
    soar.set_summary(CreateTagSummary(status="Successfully created tag"))
    soar.set_message("Status: Successfully created tag")
    output = dict(response)
    output.update(tagName=params.tag_name, tagValue=params.tag_value or "")
    return CreateTagOutput(**output)
