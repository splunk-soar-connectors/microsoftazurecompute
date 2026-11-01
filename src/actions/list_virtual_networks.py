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
from ..helper import (
    failed_collection_result,
    make_azure_collection_request,
    make_view_result,
    validate_arm_path_value,
)
from ..consts import VM_LIST_VIRTUAL_NETWORKS_ENDPOINT


class ListVirtualNetworksParams(Params):
    resource_group_name: str | None = Param(
        description="The name of the resource group",
        primary=True,
        cef_types=["vm management resource group"],
    )
    subscription_id: str | None = Param(
        description="Subscription ID to overwrite asset configuration value"
    )


class AddressspaceOutput(PermissiveActionOutput):
    addressPrefixes: str = OutputField(example_values=["10.0.0.0/24"])


class IpconfigurationsOutput(PermissiveActionOutput):
    id: str = OutputField(
        example_values=[
            "/subscriptions/a81fccf8-0405-43ae-990c-ab1389e40c6d/resourceGroups/myResourceGroup1/providers/Microsoft.Network/networkInterfaces/testvm133/ipConfigurations/ipconfig1"
        ]
    )


class PropertiesOutput(PermissiveActionOutput):
    addressSpace: AddressspaceOutput
    enableDdosProtection: bool
    enableVmProtection: bool
    provisioningState: str = OutputField(example_values=["Succeeded"])
    resourceGuid: str = OutputField(
        example_values=["1b6e07c0-a869-4a24-abfe-e93390cd0095"]
    )
    subnets: list["SubnetsOutput"]


class SubnetPropertiesOutput(PermissiveActionOutput):
    addressPrefix: str = OutputField(example_values=["10.1.0.0/24"])
    ipConfigurations: list[IpconfigurationsOutput]
    provisioningState: str = OutputField(example_values=["Succeeded"])


class SubnetsOutput(PermissiveActionOutput):
    etag: str = OutputField(example_values=['W/"afd6a89a-57fd-4eb4-bcbf-49ee9d377fc5"'])
    id: str = OutputField(
        example_values=[
            "/subscriptions/a81fccf8-0405-43ae-990c-ab1389e40c6d/resourceGroups/myResourceGroup1/providers/Microsoft.Network/virtualNetworks/myNetworkInterface1/subnets/default"
        ]
    )
    name: str = OutputField(example_values=["default"])
    properties: SubnetPropertiesOutput
    type: str = OutputField(
        example_values=["Microsoft.Network/virtualNetworks/subnets"]
    )


class TagsOutput(PermissiveActionOutput):
    author: str = OutputField(example_values=["appdev"])


class ListVirtualNetworksOutput(PermissiveActionOutput):
    etag: str = OutputField(example_values=['W/"afd6a89a-57fd-4eb4-bcbf-49ee9d377fc5"'])
    id: str = OutputField(
        example_values=[
            "/subscriptions/a81fccf8-0405-43ae-990c-ab1389e40c6d/resourceGroups/myResourceGroup1/providers/Microsoft.Network/virtualNetworks/myNetworkInterface1"
        ]
    )
    location: str = OutputField(example_values=["westus"])
    name: str = OutputField(
        cef_types=["vm management virtual network"],
        example_values=["myNetworkInterface1"],
    )
    properties: PropertiesOutput
    tags: TagsOutput
    type: str = OutputField(example_values=["Microsoft.Network/virtualNetworks"])


PropertiesOutput.model_rebuild()


class ListVirtualNetworksSummary(ActionOutput):
    num_virtual_networks: int


@app.view_handler(template="microsoftazurecompute_list_virtual_networks.html")
def display_list_virtual_networks(
    outputs: list[ListVirtualNetworksOutput], params: list[ListVirtualNetworksParams]
) -> dict:
    return make_view_result(
        outputs, params, {"resource_group_name": "resource_group_name"}
    )


@app.action(
    description="Get the list of virtual networks",
    action_type="investigate",
    read_only=True,
    summary_type=ListVirtualNetworksSummary,
    view_handler=display_list_virtual_networks,
)
def list_virtual_networks(
    params: ListVirtualNetworksParams, soar: SOARClient, asset: Asset
) -> list[ListVirtualNetworksOutput]:

    group = (
        validate_arm_path_value(params.resource_group_name, "resource_group_name")
        if params.resource_group_name
        else None
    )
    group_part = f"/resourceGroups/{group}" if group else ""
    endpoint = VM_LIST_VIRTUAL_NETWORKS_ENDPOINT.format(resourceGroup=group_part)
    values, page_error = make_azure_collection_request(
        asset, endpoint, subscription_id=params.subscription_id
    )
    summary = ListVirtualNetworksSummary(num_virtual_networks=len(values))
    outputs = [ListVirtualNetworksOutput(**item) for item in values]
    if page_error:
        return failed_collection_result(
            "Azure inventory is incomplete. "
            f"Collected {len(values)} virtual networks. {page_error}",
            params.model_dump(),
            outputs,
            summary,
        )
    soar.set_summary(summary)
    return outputs
