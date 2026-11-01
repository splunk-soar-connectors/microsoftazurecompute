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
from ..helper import (
    failed_collection_result,
    make_azure_collection_request,
    validate_arm_path_value,
)
from ..consts import MS_AZURE_GROUP_TYPE_ERR_MSG, VM_SECURITY_GROUP_ENDPOINT


class ListSecurityGroupsParams(Params):
    resource_group_name: str = Param(
        description="The name of the resource group",
        primary=True,
        cef_types=["vm management resource group"],
    )
    group_type: str = Param(
        description="Type of security group to query",
        value_list=["network", "application"],
    )
    subscription_id: str | None = Param(
        description="Subscription ID to overwrite asset configuration value"
    )


class PropertiesOutput(PermissiveActionOutput):
    defaultSecurityRules: list["DefaultsecurityrulesOutput"]
    networkInterfaces: list["NetworkinterfacesOutput"]
    provisioningState: str = OutputField(
        column_name="Provisioning State", example_values=["Succeeded"]
    )
    resourceGuid: str = OutputField(
        example_values=["93cab2f8-f56e-44f1-b804-886405bd362a"]
    )
    securityRules: list["SecurityrulesOutput"]


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
    provisioningState: str = OutputField(example_values=["Succeeded"])
    sourceAddressPrefix: str = OutputField(example_values=["VirtualNetwork"])
    sourcePortRange: str = OutputField(example_values=["*"])


class SecurityRulePropertiesOutput(PermissiveActionOutput):
    access: str = OutputField(example_values=["Allow"])
    destinationAddressPrefix: str = OutputField(example_values=["*"])
    destinationPortRange: str = OutputField(example_values=["22"])
    direction: str = OutputField(example_values=["Inbound"])
    priority: float = OutputField(example_values=[300])
    protocol: str = OutputField(example_values=["TCP"])
    sourceAddressPrefix: str = OutputField(example_values=["*"])
    sourcePortRange: str = OutputField(example_values=["*"])


class DefaultsecurityrulesOutput(PermissiveActionOutput):
    etag: str = OutputField(example_values=['W/"d086e328-28dc-4534-8f54-1373c8d4f255"'])
    id: str = OutputField(
        example_values=[
            "/subscriptions/a81fccf8-0405-43ae-990c-ab1389e40c6d/resourceGroups/test/providers/Microsoft.Network/networkSecurityGroups/aaaaa-nsg/defaultSecurityRules/AllowVnetInBound"
        ]
    )
    name: str = OutputField(example_values=["AllowVnetInBound"])
    properties: "DefaultSecurityRulePropertiesOutput"
    type: str = OutputField(
        example_values=["Microsoft.Network/networkSecurityGroups/defaultSecurityRules"]
    )


class NetworkinterfacesOutput(PermissiveActionOutput):
    id: str = OutputField(
        example_values=[
            "/subscriptions/a81fccf8-0405-43ae-990c-ab1389e40c6d/resourceGroups/test/providers/Microsoft.Network/networkInterfaces/aaaaa382"
        ]
    )


class SecurityrulesOutput(PermissiveActionOutput):
    etag: str = OutputField(example_values=['W/"1c2086b4-b285-41f2-8ce0-9898a57f60ad"'])
    id: str = OutputField(
        example_values=[
            "/subscriptions/4c357906-2c22-4d91-98aa-180d9a85a370/resourceGroups/Test_Group/providers/Microsoft.Network/networkSecurityGroups/test.vm-3-nsg/securityRules/SSH"
        ]
    )
    name: str = OutputField(example_values=["SSH"])
    properties: "SecurityRulePropertiesOutput"
    type: str = OutputField(
        example_values=["Microsoft.Network/networkSecurityGroups/securityRules"]
    )


class TagsOutput(PermissiveActionOutput):
    author: str = OutputField(example_values=["Splunk"])


class ListSecurityGroupsOutput(PermissiveActionOutput):
    resource_group_name: str = OutputField(column_name="Resource Group Name")
    name: str = OutputField(
        column_name="Group Name",
        cef_types=["vm management group name"],
        example_values=["appSGtest"],
    )
    group_type: str = OutputField(column_name="Type")
    location: str = OutputField(column_name="Location", example_values=["westus"])
    properties: "PropertiesOutput"
    id: str = OutputField(
        column_name="ID",
        example_values=[
            "/subscriptions/a81fccf8-0405-43ae-990c-ab1389e40c6d/resourceGroups/myResourceGroup1/providers/Microsoft.Network/applicationSecurityGroups/appSGtest"
        ],
    )
    etag: str = OutputField(example_values=['W/"bc870279-4d7a-4ced-a4b1-0311c27b5111"'])
    tags: TagsOutput
    type: str = OutputField(
        example_values=["Microsoft.Network/applicationSecurityGroups"]
    )


PropertiesOutput.model_rebuild()


class ListSecurityGroupsSummary(ActionOutput):
    num_security_groups: int = OutputField(example_values=[4])


@app.action(
    description="Get the list of all security groups in a resource group",
    action_type="investigate",
    read_only=True,
    verbose="API limitation: Network Security Group (classic) is not part of the response.",
    summary_type=ListSecurityGroupsSummary,
    render_as="table",
)
def list_security_groups(
    params: ListSecurityGroupsParams, soar: SOARClient, asset: Asset
) -> list[ListSecurityGroupsOutput]:

    group = validate_arm_path_value(params.resource_group_name, "resource_group_name")
    if params.group_type == "network":
        group_type = "networkSecurityGroups"
    elif params.group_type == "application":
        group_type = "applicationSecurityGroups"
    else:
        raise ActionFailure(MS_AZURE_GROUP_TYPE_ERR_MSG)
    endpoint = VM_SECURITY_GROUP_ENDPOINT.format(
        resourceGroupName=group, groupType=group_type, groupName=""
    )
    values, page_error = make_azure_collection_request(
        asset, endpoint, subscription_id=params.subscription_id
    )
    summary = ListSecurityGroupsSummary(num_security_groups=len(values))
    outputs = [
        ListSecurityGroupsOutput(
            resource_group_name=params.resource_group_name,
            group_type=params.group_type,
            **item,
        )
        for item in values
    ]
    if page_error:
        return failed_collection_result(
            "Azure inventory is incomplete. "
            f"Collected {len(values)} security groups. {page_error}",
            params.model_dump(),
            outputs,
            summary,
        )
    soar.set_summary(summary)
    return outputs
