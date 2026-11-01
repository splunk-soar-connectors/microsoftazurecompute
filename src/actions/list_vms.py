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
from ..consts import VM_LIST_VMS_RESOURCE_GROUP_ENDPOINT
from ..consts import VM_LIST_VMS_ALL_ENDPOINT


class ListVmsParams(Params):
    resource_group_name: str | None = Param(
        description="Name of the resource group",
        primary=True,
        cef_types=["vm management resource group"],
    )
    subscription_id: str | None = Param(
        description="Subscription ID to overwrite asset configuration value"
    )


class BootdiagnosticsOutput(PermissiveActionOutput):
    enabled: bool
    storageUri: str = OutputField(
        cef_types=["url"],
        example_values=["https://myresourcegroup1diag406.blob.core.windows.net/"],
    )


class DiagnosticsprofileOutput(PermissiveActionOutput):
    bootDiagnostics: BootdiagnosticsOutput


class HardwareprofileOutput(PermissiveActionOutput):
    vmSize: str = OutputField(example_values=["Standard_B1s"])


class NetworkinterfacesOutput(PermissiveActionOutput):
    id: str = OutputField(
        example_values=[
            "/subscriptions/a81fccf8-0405-43ae-990c-ab1389e40c6d/resourceGroups/myResourceGroup1/providers/Microsoft.Network/networkInterfaces/virtualmachine1259"
        ]
    )


class NetworkprofileOutput(PermissiveActionOutput):
    networkInterfaces: list[NetworkinterfacesOutput]


class PublickeysOutput(PermissiveActionOutput):
    keyData: str = OutputField(
        example_values=[
            "ssh-rsa sample_rsa_AAAbWxYa/Cw\r\nI3pXrnLZbh2obel1riER4uqamt1mbM+maPPxCCyBDyDIy31\r\nKTDYhRJ7j2vNbaa5Oyt6H8Zasypmpzth2jEwKDDi62EkQTyrNsm/CFkycMuflVZx\r\neVxXjIFG2ix0ENkSg1VXbAb6Nz0r+zBFXkOppdpSe/j+oqKihw7KjFLe0YtIwxiN\r\nFu0MHCBBvdSBmFtzrhkk3g7bnMqbD8JQdzKgkNW4xM9\r\nZRjXtwdsn7XOVcNsJ2K0e4u5xJfb6RmBQAh3IplVXX\r\nGOMl3d9S/AWmL2FLO/j9250ntbi2BsU+g0G6E\r\ncpC9JxMu5laUd/Cee2EhG+27U51nzE4O/eaVQwNAEKdYRYP9rocOisx\r\npeqy6TbUwnrrir/4y8woNYso+R4k= generated-by-azure\r\n"
        ]
    )
    path: str = OutputField(example_values=["/home/azureuser/.ssh/authorized_keys"])


class SshOutput(PermissiveActionOutput):
    publicKeys: list[PublickeysOutput]


class LinuxconfigurationOutput(PermissiveActionOutput):
    disablePasswordAuthentication: bool
    provisionVMAgent: bool
    ssh: SshOutput


class WindowsconfigurationOutput(PermissiveActionOutput):
    enableAutomaticUpdates: bool = OutputField(example_values=[True])
    provisionVMAgent: bool = OutputField(example_values=[True])


class OsprofileOutput(PermissiveActionOutput):
    adminUsername: str = OutputField(
        cef_types=["user name"], example_values=["test-user"]
    )
    allowExtensionOperations: bool
    computerName: str = OutputField(
        cef_types=["vm management virtual machine"], example_values=["virtualMachine1"]
    )
    linuxConfiguration: LinuxconfigurationOutput | None = None
    windowsConfiguration: WindowsconfigurationOutput | None = None


class ImagereferenceOutput(PermissiveActionOutput):
    offer: str = OutputField(example_values=["UbuntuServer"])
    publisher: str = OutputField(example_values=["Canonical"])
    sku: str = OutputField(example_values=["18.04-LTS"])
    version: str = OutputField(example_values=["latest"])


class ManageddiskOutput(PermissiveActionOutput):
    id: str = OutputField(
        example_values=[
            "/subscriptions/a81fccf8-0405-43ae-990c-ab1389e40c6d/resourceGroups/myResourceGroup1/providers/Microsoft.Compute/disks/virtualMachine1_OsDisk_1_3475f0acf8aa4d3e8daa84c7327adde1"
        ]
    )
    storageAccountType: str = OutputField(example_values=["StandardSSD_LRS"])


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
        example_values=["virtualMachine1_OsDisk_1_3475f0acf8aa4d3e8daa84c7327adde1"]
    )
    osType: str = OutputField(example_values=["Linux"])
    vhd: VhdOutput


class StorageprofileOutput(PermissiveActionOutput):
    imageReference: ImagereferenceOutput
    osDisk: OsdiskOutput


class PropertiesOutput(PermissiveActionOutput):
    diagnosticsProfile: DiagnosticsprofileOutput
    hardwareProfile: HardwareprofileOutput
    networkProfile: NetworkprofileOutput
    osProfile: OsprofileOutput
    provisioningState: str = OutputField(example_values=["Succeeded"])
    storageProfile: StorageprofileOutput
    vmId: str = OutputField(example_values=["6ead047c-7405-4f68-a0da-0b12fd99e185"])


class ResourcesOutput(PermissiveActionOutput):
    id: str = OutputField(
        example_values=[
            "/subscriptions/a81fccf8-0405-43ae-990c-ab1389e40c6d/resourceGroups/MYRESOURCEGROUP1/providers/Microsoft.Compute/virtualMachines/virtualMachine1/extensions/OmsAgentForLinux"
        ]
    )


class TagsOutput(PermissiveActionOutput):
    author: str = OutputField(example_values=["appdev"])
    company: str = OutputField(example_values=["Splunk"])
    type: str = OutputField(example_values=["vm"])


class ListVmsOutput(PermissiveActionOutput):
    id: str = OutputField(
        example_values=[
            "/subscriptions/a81fccf8-0405-43ae-990c-ab1389e40c6d/resourceGroups/MYRESOURCEGROUP1/providers/Microsoft.Compute/virtualMachines/virtualMachine1"
        ]
    )
    location: str = OutputField(example_values=["eastus"])
    name: str = OutputField(
        cef_types=["vm management virtual machine"], example_values=["virtualMachine1"]
    )
    properties: PropertiesOutput
    resources: list[ResourcesOutput]
    tags: TagsOutput
    type: str = OutputField(example_values=["Microsoft.Compute/virtualMachines"])


class ListVmsSummary(ActionOutput):
    num_vms: int


@app.view_handler(template="microsoftazurecompute_list_vms.html")
def display_list_vms(
    outputs: list[ListVmsOutput], params: list[ListVmsParams]
) -> dict:
    return make_view_result(
        outputs, params, {"resource_group_name": "resource_group_name"}
    )


@app.action(
    description="Get the list of registered VMs",
    action_type="investigate",
    read_only=True,
    summary_type=ListVmsSummary,
    view_handler=display_list_vms,
)
def list_vms(
    params: ListVmsParams, soar: SOARClient, asset: Asset
) -> list[ListVmsOutput]:

    if params.resource_group_name:
        group = validate_arm_path_value(
            params.resource_group_name, "resource_group_name"
        )
        endpoint = VM_LIST_VMS_RESOURCE_GROUP_ENDPOINT.format(resourceGroupName=group)
    else:
        endpoint = VM_LIST_VMS_ALL_ENDPOINT
    values, page_error = make_azure_collection_request(
        asset, endpoint, subscription_id=params.subscription_id
    )
    summary = ListVmsSummary(num_vms=len(values))
    outputs = [ListVmsOutput(**vm) for vm in values]
    if page_error:
        return failed_collection_result(
            f"Azure inventory is incomplete. Collected {len(values)} VMs. {page_error}",
            params.model_dump(),
            outputs,
            summary,
        )
    soar.set_summary(summary)
    return outputs
