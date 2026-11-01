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
from ..helper import make_azure_request, validate_arm_path_value
from ..consts import VM_CHECK_IP_AVAIL


class GetIpAvailabilityParams(Params):
    resource_group_name: str = Param(
        description="The name of the resource group",
        primary=True,
        cef_types=["vm management resource group"],
        column_name="Resource Group Name",
    )
    virtual_network_name: str = Param(
        description="The name of the virtual network",
        primary=True,
        cef_types=["vm management virtual network"],
        column_name="Virtual Network Name",
    )
    ip_address: str = Param(
        description="The private IP address to be verified",
        primary=True,
        cef_types=["ip", "ipv6"],
        column_name="IP Address",
    )
    subscription_id: str | None = Param(
        description="Subscription ID to overwrite asset configuration value"
    )


class GetIpAvailabilityOutput(PermissiveActionOutput):
    availableAddress: str = OutputField(
        column_name="Available IP Addresses",
        cef_types=["ip", "ipv6"],
        example_values=["10.1.0.4"],
    )


class GetIpAvailabilitySummary(ActionOutput):
    num_ips_available: int
    available: bool


@app.action(
    description="Check if a private IP address is available for use",
    action_type="investigate",
    read_only=True,
    name="get ip availability",
    summary_type=GetIpAvailabilitySummary,
    render_as="table",
)
def check_address_availability(
    params: GetIpAvailabilityParams, soar: SOARClient, asset: Asset
) -> list[GetIpAvailabilityOutput]:

    group = validate_arm_path_value(params.resource_group_name, "resource_group_name")
    vnet = validate_arm_path_value(params.virtual_network_name, "virtual_network_name")
    endpoint = VM_CHECK_IP_AVAIL.format(
        resourceGroup=group, virtualNetwork=vnet, ip=params.ip_address
    )
    response = make_azure_request(
        asset, endpoint, subscription_id=params.subscription_id
    )
    values = response.get("availableIPAddresses", [])
    soar.set_summary(
        GetIpAvailabilitySummary(
            num_ips_available=len(values), available=response.get("available")
        )
    )
    return [GetIpAvailabilityOutput(availableAddress=value) for value in values]
