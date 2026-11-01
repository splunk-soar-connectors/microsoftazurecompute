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
from ..consts import VM_LIST_SNAPSHOTS_ENDPOINT
from ..consts import VM_RESOURCE_GROUP_VALUE_PART


class ListSnapshotsParams(Params):
    resource_group_name: str | None = Param(
        description="The name of the resource group",
        primary=True,
        cef_types=["vm management resource group"],
    )
    subscription_id: str | None = Param(
        description="Subscription ID to overwrite asset configuration value"
    )


class CreationdataOutput(PermissiveActionOutput):
    createOption: str = OutputField(example_values=["Copy"])
    sourceResourceId: str = OutputField(
        example_values=[
            "/subscriptions/a81fccf8-0405-43ae-990c-ab1389e40c6d/resourceGroups/MYRESOURCEGROUP1/providers/Microsoft.Compute/disks/testVM_OsDisk_1_1c75b0f4f5df46ba88997aac183d8ad6"
        ]
    )
    sourceUri: str = OutputField(
        example_values=[
            "https://testdisks466.blob.core.windows.net/vhds/unmanagedVM20190125164741.vhd"
        ]
    )


class PropertiesOutput(PermissiveActionOutput):
    creationData: CreationdataOutput
    diskSizeGB: float = OutputField(example_values=[30])
    diskState: str = OutputField(example_values=["Unattached"])
    osType: str = OutputField(example_values=["Linux"])
    provisioningState: str = OutputField(example_values=["Succeeded"])
    timeCreated: str = OutputField(example_values=["2019-01-17T20:55:06.9032116+00:00"])


class SkuOutput(PermissiveActionOutput):
    name: str = OutputField(example_values=["Standard_LRS"])
    tier: str = OutputField(example_values=["Standard"])


class TagsOutput(PermissiveActionOutput):
    author: str = OutputField(example_values=["appdev"])
    type: str = OutputField(example_values=["snapshot"])


class ListSnapshotsOutput(PermissiveActionOutput):
    id: str = OutputField(
        example_values=[
            "/subscriptions/a81fccf8-0405-43ae-990c-ab1389e40c6d/resourceGroups/myResourceGroup1/providers/Microsoft.Compute/snapshots/mySnapshot1"
        ]
    )
    location: str = OutputField(example_values=["westus"])
    name: str = OutputField(
        cef_types=["vm management tag name"], example_values=["mySnapshot1"]
    )
    properties: PropertiesOutput
    sku: SkuOutput
    tags: TagsOutput
    type: str = OutputField(example_values=["Microsoft.Compute/snapshots"])


class ListSnapshotsSummary(ActionOutput):
    num_snapshots: int


@app.view_handler(template="microsoftazurecompute_list_snapshots.html")
def display_list_snapshots(
    outputs: list[ListSnapshotsOutput], params: list[ListSnapshotsParams]
) -> dict:
    return make_view_result(
        outputs, params, {"resource_group_name": "resource_group_name"}
    )


@app.action(
    description="Get the list of snapshots under the subscription",
    action_type="investigate",
    read_only=True,
    summary_type=ListSnapshotsSummary,
    view_handler=display_list_snapshots,
)
def list_snapshots(
    params: ListSnapshotsParams, soar: SOARClient, asset: Asset
) -> list[ListSnapshotsOutput]:

    group = (
        validate_arm_path_value(params.resource_group_name, "resource_group_name")
        if params.resource_group_name
        else None
    )
    resource_part = (
        VM_RESOURCE_GROUP_VALUE_PART.format(resourceGroupName=group) if group else ""
    )
    endpoint = VM_LIST_SNAPSHOTS_ENDPOINT.format(resourceValue=resource_part)
    values, page_error = make_azure_collection_request(
        asset, endpoint, subscription_id=params.subscription_id
    )
    summary = ListSnapshotsSummary(num_snapshots=len(values))
    outputs = [ListSnapshotsOutput(**item) for item in values]
    if page_error:
        return failed_collection_result(
            "Azure inventory is incomplete. "
            f"Collected {len(values)} snapshots. {page_error}",
            params.model_dump(),
            outputs,
            summary,
        )
    soar.set_summary(summary)
    return outputs
