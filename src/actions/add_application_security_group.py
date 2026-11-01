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
from soar_sdk.action_results import ActionOutput, OutputField, PermissiveActionOutput
from soar_sdk.params import Param, Params

from ..app import Asset, app
from soar_sdk.exceptions import ActionFailure
from ..helper import make_azure_request, make_view_result, validate_arm_path_value
import json
from ..consts import MS_AZURE_INVALID_JSON, VM_SECURITY_GROUP_ENDPOINT


class AddApplicationGroupParams(Params):
    resource_group_name: str = Param(
        description="The name of the resource group",
        primary=True,
        cef_types=["vm management resource group"],
    )
    group_name: str = Param(
        description="Name of security group to add",
        primary=True,
        cef_types=["vm management group name"],
    )
    location: str = Param(
        description="Resource location",
        value_list=[
            "Australia East",
            "Australia Southeast",
            "Brazil South",
            "Canada Central",
            "Canada East",
            "Central India",
            "Central US",
            "East Asia",
            "East US",
            "East US 2",
            "France Central",
            "Japan East",
            "Japan West",
            "Korea Central",
            "Korea South",
            "North Central US",
            "North Europe",
            "South Central US",
            "South India",
            "Southeast Asia",
            "UK South",
            "UK West",
            "West Central US",
            "West Europe",
            "West India",
            "West US",
            "West US 2",
        ],
    )
    tags: str | None = Param(
        description="String object of resource tags. It should be in JSON format"
    )
    subscription_id: str | None = Param(
        description="Subscription ID to overwrite asset configuration value"
    )


class PropertiesOutput(PermissiveActionOutput):
    provisioningState: str = OutputField(example_values=["Succeeded"])


class TagsOutput(PermissiveActionOutput):
    author: str = OutputField(example_values=["Splunk"])


class AddApplicationGroupOutput(PermissiveActionOutput):
    etag: str = OutputField(example_values=['W/"b6eab29d-32f4-48d2-80e1-06f8dfb3616a"'])
    id: str = OutputField(
        example_values=[
            "/subscriptions/a81fccf8-0405-43ae-990c-ab1389e40c6d/resourceGroups/myResourceGroup1/providers/Microsoft.Network/applicationSecurityGroups/test_group"
        ]
    )
    location: str = OutputField(example_values=["westus"])
    name: str = OutputField(
        cef_types=["vm management group name"], example_values=["example_name"]
    )
    properties: PropertiesOutput
    tags: TagsOutput
    type: str = OutputField(
        example_values=["Microsoft.Network/applicationSecurityGroups"]
    )


class AddApplicationSecurityGroupSummary(ActionOutput):
    status: str


@app.view_handler(template="microsoftazurecompute_add_application_security_group.html")
def display_add_application_security_group(
    outputs: list[AddApplicationGroupOutput], params: list[AddApplicationGroupParams]
) -> dict:
    return make_view_result(
        outputs,
        params,
        {
            "resource_group_name": "resource_group_name",
            "group_name": "group_name",
            "location": "location",
            "tags": "tags",
        },
    )


@app.action(
    description="Add an application security groups in a resource group",
    action_type="generic",
    read_only=False,
    name="add application group",
    summary_type=AddApplicationSecurityGroupSummary,
    view_handler=display_add_application_security_group,
)
def add_application_security_group(
    params: AddApplicationGroupParams, soar: SOARClient, asset: Asset
) -> AddApplicationGroupOutput:

    group = validate_arm_path_value(params.resource_group_name, "resource_group_name")
    group_name = validate_arm_path_value(params.group_name, "group_name")
    endpoint = VM_SECURITY_GROUP_ENDPOINT.format(
        resourceGroupName=group,
        groupType="applicationSecurityGroups",
        groupName=f"/{group_name}",
    )
    body = {"location": params.location, "tags": {}}
    if params.tags:
        try:
            body["tags"].update(json.loads(params.tags))
        except json.JSONDecodeError as exc:
            raise ActionFailure(
                MS_AZURE_INVALID_JSON.format(err_msg=str(exc), param="tags")
            ) from exc
    response = make_azure_request(
        asset,
        endpoint,
        subscription_id=params.subscription_id,
        method="PUT",
        json_body=body,
    )
    soar.set_summary(
        AddApplicationSecurityGroupSummary(
            status="Successfully added or updated security group"
        )
    )
    soar.set_message("Status: Successfully added or updated security group")
    return AddApplicationGroupOutput(**response)
