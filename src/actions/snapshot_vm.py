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
from ..helper import make_azure_request, make_view_result, validate_arm_path_value
from ..consts import VM_SNAPSHOT_VM_ENDPOINT


class SnapshotVmParams(Params):
    resource_group_name: str = Param(
        description="The name of the resource group",
        primary=True,
        cef_types=["vm management resource group"],
    )
    snapshot_name: str = Param(
        description="The name of the snapshot that is being created. The name can't be changed after the snapshot is created. Supported characters for the name are a-z, A-Z, 0-9, and _. The max name length is 80 characters"
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
    create_option: str = Param(
        description="Source for disk's creation", value_list=["Copy", "Import"]
    )
    source_resource_id: str | None = Param(
        description="If create_option is Copy, this is the ARM ID of the source snapshot or disk"
    )
    source_uri: str | None = Param(
        description="If create_option is Import, this is the URI of a blob to be imported into a managed disk"
    )
    subscription_id: str | None = Param(
        description="Subscription ID to overwrite asset configuration value"
    )


class CreationdataOutput(PermissiveActionOutput):
    createOption: str = OutputField(example_values=["Copy"])
    sourceResourceId: str = OutputField(
        example_values=[
            "subscriptions/a81fccf8-0405-43ae-990c-ab1389e40c6d/resourceGroups/myResourceGroup1/providers/Microsoft.Compute/snapshots/mySnapshot1"
        ]
    )
    sourceUri: str = OutputField(
        example_values=[
            "https://testdisks466.blob.core.windows.net/vhds/unmanagedVM20190125164741.vhd"
        ]
    )


class PropertiesOutput(PermissiveActionOutput):
    creationData: CreationdataOutput
    diskSizeBytes: float = OutputField(example_values=[13636730880])
    diskSizeGB: float = OutputField(example_values=[30])
    faultDomain: float = OutputField(cef_types=["domain"], example_values=[0])
    isArmResource: bool
    osType: str = OutputField(example_values=["Linux"])
    provisioningState: str = OutputField(example_values=["Updating"])


class SkuOutput(PermissiveActionOutput):
    name: str = OutputField(example_values=["Standard_LRS"])
    tier: str = OutputField(example_values=["Standard"])


class TagsOutput(PermissiveActionOutput):
    author: str = OutputField(example_values=["appdev"])


class SnapshotVmOutput(PermissiveActionOutput):
    location: str = OutputField(example_values=["West US"])
    name: str = OutputField(example_values=["my_new_snapshot"])
    properties: PropertiesOutput
    sku: SkuOutput
    tags: TagsOutput


class SnapshotVmSummary(ActionOutput):
    status: str
    provisioning_state: str


@app.view_handler(template="microsoftazurecompute_snapshot_vm.html")
def display_snapshot_vm(
    outputs: list[SnapshotVmOutput], params: list[SnapshotVmParams]
) -> dict:
    return make_view_result(
        outputs,
        params,
        {
            "resource_group_name": "resource_group_name",
            "snapshot_name": "snapshot_name",
            "location": "location",
            "create_option": "create_option",
            "source_resource_id": "source_resource_id",
            "source_uri": "source_uri",
        },
    )


@app.action(
    description="Take a snapshot of the VM",
    action_type="generic",
    read_only=False,
    verbose="While creating a snapshot using the COPY option, 'source_resource_id' parameter is required and while using the IMPORT option, 'source_uri' parameter is required. For the 'source_uri' parameter, the uri value should be valid page blob uri path. For more information refer to <a href='https://docs.microsoft.com/en-us/rest/api/compute/snapshots/create-or-update' target='_blank'>API Docs</a>.",
    summary_type=SnapshotVmSummary,
    view_handler=display_snapshot_vm,
)
def snapshot_vm(
    params: SnapshotVmParams, soar: SOARClient, asset: Asset
) -> SnapshotVmOutput:

    snapshot_name = validate_arm_path_value(params.snapshot_name, "snapshot_name")
    group = validate_arm_path_value(params.resource_group_name, "resource_group_name")
    endpoint = VM_SNAPSHOT_VM_ENDPOINT.format(
        resourceGroupName=group, snapshotName=snapshot_name
    )
    creation_data = {"createOption": params.create_option}
    if params.source_resource_id:
        creation_data["sourceResourceId"] = params.source_resource_id
    if params.source_uri:
        creation_data["sourceUri"] = params.source_uri
    body = {
        "name": snapshot_name,
        "location": params.location,
        "properties": {"creationData": creation_data},
    }
    response = make_azure_request(
        asset,
        endpoint,
        subscription_id=params.subscription_id,
        method="PUT",
        json_body=body,
    )
    state = response.get("properties", {}).get("provisioningState", "Unavailable")
    soar.set_summary(
        SnapshotVmSummary(
            status="Successfully created snapshot", provisioning_state=state
        )
    )
    soar.set_message(
        f"Status: Successfully created snapshot, Provisioning state: {state}"
    )
    return SnapshotVmOutput(**response)
