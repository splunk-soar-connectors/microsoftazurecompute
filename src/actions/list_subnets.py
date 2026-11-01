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
    validate_arm_path_value,
)
from ..consts import VM_LIST_SUBNETS_ENDPOINT


class ListSubnetsParams(Params):
    resource_group_name: str = Param(
        description="The name of the resource group",
        primary=True,
        cef_types=["vm management resource group"],
    )
    virtual_network_name: str = Param(
        description="The name of the virtual network",
        primary=True,
        cef_types=["vm management virtual network"],
    )
    subscription_id: str | None = Param(
        description="Subscription ID to overwrite asset configuration value"
    )


class IpconfigurationsOutput(PermissiveActionOutput):
    id: str = OutputField(
        example_values=[
            "/subscriptions/a81fccf8-0405-43ae-990c-ab1389e40c6d/resourceGroups/test/providers/Microsoft.Network/networkInterfaces/unmanagedvm260/ipConfigurations/ipconfig1"
        ]
    )


class PropertiesOutput(PermissiveActionOutput):
    addressPrefix: str = OutputField(example_values=["10.1.0.0/24"])
    ipConfigurations: list[IpconfigurationsOutput]
    provisioningState: str = OutputField(example_values=["Succeeded"])


class ListSubnetsOutput(PermissiveActionOutput):
    resource_group_name: str = OutputField(column_name="Resource Group Name")
    virtual_network_name: str = OutputField(column_name="Virtual Network Name")
    name: str = OutputField(column_name="Name", example_values=["default"])
    etag: str = OutputField(
        column_name="Etag",
        example_values=['W/"2290fbd6-434f-410c-a80a-3e66f030cdb2"'],
    )
    id: str = OutputField(
        column_name="ID",
        example_values=[
            "/subscriptions/a81fccf8-0405-43ae-990c-ab1389e40c6d/resourceGroups/myResourceGroup1/providers/Microsoft.Network/virtualNetworks/myNetworkInterface1/subnets/default"
        ],
    )
    properties: PropertiesOutput
    type: str = OutputField(
        example_values=["Microsoft.Network/virtualNetworks/subnets"]
    )


class ListSubnetsSummary(ActionOutput):
    num_subnets: int = OutputField(example_values=[4])


@app.action(
    description="Get the list of subnets",
    action_type="investigate",
    read_only=True,
    summary_type=ListSubnetsSummary,
    render_as="table",
)
def list_subnets(
    params: ListSubnetsParams, soar: SOARClient, asset: Asset
) -> list[ListSubnetsOutput]:

    group = validate_arm_path_value(params.resource_group_name, "resource_group_name")
    vnet = validate_arm_path_value(params.virtual_network_name, "virtual_network_name")
    endpoint = VM_LIST_SUBNETS_ENDPOINT.format(
        resourceGroupName=group, virtualNetworkName=vnet
    )
    values, page_error = make_azure_collection_request(
        asset, endpoint, subscription_id=params.subscription_id
    )
    summary = ListSubnetsSummary(num_subnets=len(values))
    outputs = [
        ListSubnetsOutput(
            resource_group_name=params.resource_group_name,
            virtual_network_name=params.virtual_network_name,
            **item,
        )
        for item in values
    ]
    if page_error:
        return failed_collection_result(
            "Azure inventory is incomplete. "
            f"Collected {len(values)} subnets. {page_error}",
            params.model_dump(),
            outputs,
            summary,
        )
    soar.set_summary(summary)
    return outputs
