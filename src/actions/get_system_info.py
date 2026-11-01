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
from soar_sdk.action_results import OutputField, PermissiveActionOutput
from soar_sdk.params import Param, Params

from ..app import Asset, app
from ..helper import make_azure_request, make_view_result, validate_arm_path_value
from ..consts import VM_GET_SYSTEM_INFO_ENDPOINT


class GetSystemInfoParams(Params):
    resource_group_name: str = Param(
        description="The name of the resource group",
        primary=True,
        cef_types=["vm management resource group"],
    )
    vm_name: str = Param(
        description="The name of the virtual machine",
        primary=True,
        cef_types=["vm management virtual machine"],
    )
    subscription_id: str | None = Param(
        description="Subscription ID to overwrite asset configuration value"
    )


class BootdiagnosticsOutput(PermissiveActionOutput):
    enabled: bool
    storageUri: str = OutputField(
        cef_types=["url"],
        example_values=["https://myresourcegroup1diag311.blob.core.windows.net/"],
    )


class DiagnosticsprofileOutput(PermissiveActionOutput):
    bootDiagnostics: BootdiagnosticsOutput


class HardwareprofileOutput(PermissiveActionOutput):
    vmSize: str = OutputField(example_values=["Standard_B1s"])


class NetworkinterfacesOutput(PermissiveActionOutput):
    id: str = OutputField(
        example_values=[
            "/subscriptions/a81fccf8-0405-43ae-990c-ab1389e40c6d/resourceGroups/myResourceGroup1/providers/Microsoft.Network/networkInterfaces/testvm133"
        ]
    )


class NetworkprofileOutput(PermissiveActionOutput):
    networkInterfaces: list[NetworkinterfacesOutput]


class LinuxconfigurationOutput(PermissiveActionOutput):
    disablePasswordAuthentication: bool
    provisionVMAgent: bool


class WindowsconfigurationOutput(PermissiveActionOutput):
    enableAutomaticUpdates: bool
    provisionVMAgent: bool


class OsprofileOutput(PermissiveActionOutput):
    adminUsername: str = OutputField(cef_types=["user name"], example_values=["test"])
    allowExtensionOperations: bool
    computerName: str = OutputField(
        cef_types=["vm management virtual machine"], example_values=["testVM"]
    )
    linuxConfiguration: LinuxconfigurationOutput
    windowsConfiguration: WindowsconfigurationOutput


class ImagereferenceOutput(PermissiveActionOutput):
    offer: str = OutputField(example_values=["UbuntuServer"])
    publisher: str = OutputField(example_values=["Canonical"])
    sku: str = OutputField(example_values=["18.04-LTS"])
    version: str = OutputField(example_values=["latest"])


class ManageddiskOutput(PermissiveActionOutput):
    id: str = OutputField(
        example_values=[
            "/subscriptions/a81fccf8-0405-43ae-990c-ab1389e40c6d/resourceGroups/myResourceGroup1/providers/Microsoft.Compute/disks/testVM_OsDisk_1_1c75b0f4f5df46ba88997aac183d8ad6"
        ]
    )
    storageAccountType: str = OutputField(example_values=["Premium_LRS"])


class VhdOutput(PermissiveActionOutput):
    uri: str = OutputField(
        example_values=[
            "https://testdisks466.blob.core.windows.net/vhds/unmanagedVM20190125164741.vhd"
        ]
    )


class OsdiskOutput(PermissiveActionOutput):
    caching: str = OutputField(example_values=["ReadWrite"])
    createOption: str = OutputField(example_values=["FromImage"])
    diskSizeGB: float = OutputField(example_values=[30])
    managedDisk: ManageddiskOutput
    name: str = OutputField(
        example_values=["testVM_OsDisk_1_1c75b0f4f5df46ba88997aac183d8ad6"]
    )
    osType: str = OutputField(example_values=["Linux"])
    vhd: VhdOutput


class StorageprofileOutput(PermissiveActionOutput):
    imageReference: ImagereferenceOutput
    osDisk: OsdiskOutput


class ExtensionPropertiesOutput(PermissiveActionOutput):
    autoUpgradeMinorVersion: bool
    provisioningState: str = OutputField(example_values=["Updating"])
    publisher: str = OutputField(
        example_values=["Microsoft.EnterpriseCloud.Monitoring"]
    )
    settings: "SettingsOutput"
    type: str = OutputField(example_values=["OmsAgentForLinux"])
    typeHandlerVersion: str = OutputField(example_values=["1.4"])


class SettingsOutput(PermissiveActionOutput):
    azureResourceId: str
    stopOnMultipleConnections: str = OutputField(example_values=["true"])
    workspaceId: str = OutputField(
        example_values=["4a6116d3-9349-40bb-8b06-ac937da327b6"]
    )


class PropertiesOutput(PermissiveActionOutput):
    diagnosticsProfile: DiagnosticsprofileOutput
    hardwareProfile: HardwareprofileOutput
    networkProfile: NetworkprofileOutput
    osProfile: OsprofileOutput
    provisioningState: str = OutputField(example_values=["Updating"])
    storageProfile: StorageprofileOutput
    vmId: str = OutputField(example_values=["58a871bc-1cbb-4a86-8603-a73527071c74"])


class ResourcesOutput(PermissiveActionOutput):
    id: str = OutputField(
        example_values=[
            "/subscriptions/a81fccf8-0405-43ae-990c-ab1389e40c6d/resourceGroups/myresourcegroup1/providers/Microsoft.Compute/virtualMachines/virtualMachine1/extensions/OmsAgentForLinux"
        ]
    )
    location: str = OutputField(example_values=["eastus"])
    name: str = OutputField(example_values=["OmsAgentForLinux"])
    properties: ExtensionPropertiesOutput
    type: str = OutputField(
        example_values=["Microsoft.Compute/virtualMachines/extensions"]
    )


class TagsOutput(PermissiveActionOutput):
    author: str = OutputField(example_values=["appdev"])
    company: str = OutputField(example_values=["Splunk"])


class GetSystemInfoOutput(PermissiveActionOutput):
    id: str = OutputField(
        example_values=[
            "/subscriptions/a81fccf8-0405-43ae-990c-ab1389e40c6d/resourceGroups/myResourceGroup1/providers/Microsoft.Compute/virtualMachines/testVM"
        ]
    )
    location: str = OutputField(example_values=["westus"])
    name: str = OutputField(
        cef_types=["vm management virtual machine"], example_values=["testVM"]
    )
    properties: PropertiesOutput
    resources: list[ResourcesOutput]
    tags: TagsOutput
    type: str = OutputField(example_values=["Microsoft.Compute/virtualMachines"])


ExtensionPropertiesOutput.model_rebuild()
PropertiesOutput.model_rebuild()


@app.view_handler(template="microsoftazurecompute_get_system_info.html")
def display_get_system_info(
    outputs: list[GetSystemInfoOutput], params: list[GetSystemInfoParams]
) -> dict:
    return make_view_result(
        outputs,
        params,
        {
            "resource_group_name": "resource_group_name",
            "vm_name": "vm_name",
        },
    )


@app.action(
    description="Get information about a VM",
    action_type="investigate",
    read_only=True,
    view_handler=display_get_system_info,
)
def get_system_info(
    params: GetSystemInfoParams, soar: SOARClient, asset: Asset
) -> GetSystemInfoOutput:

    resource_group = validate_arm_path_value(
        params.resource_group_name, "resource_group_name"
    )
    vm_name = validate_arm_path_value(params.vm_name, "vm_name")
    endpoint = VM_GET_SYSTEM_INFO_ENDPOINT.format(
        resourceGroupName=resource_group, vmName=vm_name
    )
    response = make_azure_request(
        asset, endpoint, subscription_id=params.subscription_id
    )
    soar.set_message("The system info was successfully retrieved")
    return GetSystemInfoOutput(**response)
