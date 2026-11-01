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


class AddNetworkGroupParams(Params):
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
    tags: str | None = Param(description="String object of resource tags")
    default_security_rules: str | None = Param(
        description="Comma separated list of default security rules for the network security group"
    )
    provisioning_state: str | None = Param(
        description="The provisioning state of the public IP resource",
        value_list=["Updating", "Deleting", "Failed"],
    )
    resource_guid: str | None = Param(
        description="The resource GUID property of the network security group resource"
    )
    security_rules: str | None = Param(
        description="Comma separated list of security rules of the network security group"
    )
    subscription_id: str | None = Param(
        description="Subscription ID to overwrite asset configuration value"
    )


class PropertiesOutput(PermissiveActionOutput):
    defaultSecurityRules: list["DefaultsecurityrulesOutput"]
    provisioningState: str = OutputField(example_values=["Succeeded", "Updating"])
    resourceGuid: str = OutputField(
        example_values=["0214f54b-2274-470c-b87a-85578d05b942"]
    )


class DefaultSecurityRulePropertiesOutput(PermissiveActionOutput):
    access: str = OutputField(example_values=["Allow"])
    description: str = OutputField(
        example_values=["Allow inbound traffic from all VMs in VNET"]
    )
    destinationAddressPrefix: str = OutputField(example_values=["VirtualNetwork"])
    destinationPortRange: str = OutputField(example_values=["*"])
    direction: str = OutputField(example_values=["Inbound"])
    priority: float = OutputField(example_values=[65000])
    protocol: str = OutputField(example_values=["*"])
    provisioningState: str = OutputField(example_values=["Succeeded", "Updating"])
    sourceAddressPrefix: str = OutputField(example_values=["VirtualNetwork"])
    sourcePortRange: str = OutputField(example_values=["*"])


class DefaultsecurityrulesOutput(PermissiveActionOutput):
    etag: str = OutputField(
        example_values=[
            'W/"12b43767-ecc7-4ed4-af5f-0c13b78dae0e"',
            'W/"d62d2fcf-970a-4955-b996-d586ea2f8a3c"',
        ]
    )
    id: str = OutputField(
        example_values=[
            "/subscriptions/a81fccf8-0405-43ae-990c-ab1389e40c6d/resourceGroups/myResourceGroup1/providers/Microsoft.Network/networkSecurityGroups/netwGroup1/defaultSecurityRules/AllowVnetInBound"
        ]
    )
    name: str = OutputField(example_values=["AllowVnetInBound"])
    properties: "DefaultSecurityRulePropertiesOutput"
    type: str = OutputField(
        example_values=["Microsoft.Network/networkSecurityGroups/defaultSecurityRules"]
    )


class TagsOutput(PermissiveActionOutput):
    author: str = OutputField(example_values=["test-user"])


class AddNetworkGroupOutput(PermissiveActionOutput):
    etag: str = OutputField(
        example_values=[
            'W/"12b43767-ecc7-4ed4-af5f-0c13b78dae0e"',
            'W/"d62d2fcf-970a-4955-b996-d586ea2f8a3c"',
        ]
    )
    id: str = OutputField(
        example_values=[
            "/subscriptions/a81fccf8-0405-43ae-990c-ab1389e40c6d/resourceGroups/myResourceGroup1/providers/Microsoft.Network/networkSecurityGroups/netwGroup1"
        ]
    )
    location: str = OutputField(example_values=["westus2"])
    name: str = OutputField(example_values=["netwGroup1"])
    properties: "PropertiesOutput"
    tags: TagsOutput
    type: str = OutputField(example_values=["Microsoft.Network/networkSecurityGroups"])


PropertiesOutput.model_rebuild()


class AddNetworkSecurityGroupSummary(ActionOutput):
    status: str


@app.view_handler(template="microsoftazurecompute_add_network_security_group.html")
def display_add_network_security_group(
    outputs: list[AddNetworkGroupOutput], params: list[AddNetworkGroupParams]
) -> dict:
    return make_view_result(
        outputs,
        params,
        {
            "resource_group_name": "resource_group_name",
            "group_name": "group_name",
            "location": "location",
            "tags": "tags",
            "default_security_rules": "default_security_rules",
            "provisioning_state": "provisioning_state",
            "resource_guid": "resource_guid",
            "security_rules": "security_rules",
        },
    )


@app.action(
    description="Add a network security group in a resource group",
    action_type="generic",
    read_only=False,
    verbose="The 'security_rules' parameter accept JSON format value. For non-JSON values, the parameter values will be ignored. Refer to <a href='https://docs.microsoft.com/en-us/rest/api/virtualnetwork/networksecuritygroups/createorupdate' target='_blank'>API Docs</a> for more information on adding a network security group.",
    name="add network group",
    summary_type=AddNetworkSecurityGroupSummary,
    view_handler=display_add_network_security_group,
)
def add_network_security_group(
    params: AddNetworkGroupParams, soar: SOARClient, asset: Asset
) -> AddNetworkGroupOutput:

    group = validate_arm_path_value(params.resource_group_name, "resource_group_name")
    group_name = validate_arm_path_value(params.group_name, "group_name")
    endpoint = VM_SECURITY_GROUP_ENDPOINT.format(
        resourceGroupName=group,
        groupType="networkSecurityGroups",
        groupName=f"/{group_name}",
    )
    body = {"location": params.location, "properties": {}, "tags": {}}
    if params.tags:
        try:
            body["tags"].update(json.loads(params.tags))
        except json.JSONDecodeError as exc:
            raise ActionFailure(
                MS_AZURE_INVALID_JSON.format(err_msg=str(exc), param="tags")
            ) from exc
    for source, target in (
        (params.default_security_rules, "defaultSecurityRules"),
        (params.provisioning_state, "provisioningState"),
        (params.resource_guid, "resourceGuid"),
    ):
        if source:
            body["properties"][target] = source
    if params.security_rules:
        try:
            body["properties"]["securityRules"] = json.loads(params.security_rules)
        except json.JSONDecodeError:
            body["properties"]["securityRules"] = params.security_rules
    response = make_azure_request(
        asset,
        endpoint,
        subscription_id=params.subscription_id,
        method="PUT",
        json_body=body,
    )
    soar.set_summary(
        AddNetworkSecurityGroupSummary(
            status="Successfully added or updated security group"
        )
    )
    soar.set_message("Status: Successfully added or updated security group")
    return AddNetworkGroupOutput(**response)
