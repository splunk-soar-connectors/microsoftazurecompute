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
from soar_sdk.exceptions import ActionFailure
from soar_sdk.params import Param, Params

from ..app import Asset, app
from ..helper import failed_table_result, make_azure_request, validate_arm_path_value
from ..consts import VM_GET_SYSTEM_INFO_ENDPOINT


class DeleteVmParams(Params):
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


class DeleteVmSummary(ActionOutput):
    status: str | None = OutputField(example_values=["Successfully deleted the vm"])


class DeleteVmOutput(PermissiveActionOutput):
    resource_group_name: str = OutputField(column_name="Resource Group Name")
    vm_name: str = OutputField(column_name="VM Name")


@app.action(
    description="Delete a VM",
    action_type="contain",
    read_only=False,
    summary_type=DeleteVmSummary,
    render_as="table",
    output_class=DeleteVmOutput,
)
def delete_vm(params: DeleteVmParams, soar: SOARClient, asset: Asset) -> DeleteVmOutput:

    try:
        group = validate_arm_path_value(
            params.resource_group_name, "resource_group_name"
        )
        vm_name = validate_arm_path_value(params.vm_name, "vm_name")
        endpoint = VM_GET_SYSTEM_INFO_ENDPOINT.format(
            resourceGroupName=group, vmName=vm_name
        )
        make_azure_request(
            asset, endpoint, subscription_id=params.subscription_id, method="DELETE"
        )
    except (ActionFailure, ValueError) as exc:
        return failed_table_result(
            str(exc),
            params.model_dump(),
            DeleteVmOutput(
                resource_group_name=params.resource_group_name,
                vm_name=params.vm_name,
            ),
            DeleteVmSummary(status=None),
        )

    message = "Successfully deleted the vm"
    soar.set_summary(DeleteVmSummary(status=message))
    soar.set_message(f"Status: {message}")
    return DeleteVmOutput(
        resource_group_name=params.resource_group_name,
        vm_name=params.vm_name,
    )
