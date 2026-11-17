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

from ..action_errors import preserve_failure_params
from ..app import Asset, app
from ..helper import (
    format_vm_action_endpoint,
    failed_table_result,
    make_azure_request,
    validate_arm_path_value,
    vm_mutation_output_fields,
    make_vm_start_request,
    AsyncOperationError,
)


class StartVmParams(Params):
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
    wait_for_completion: bool = Param(
        required=False,
        default=False,
        description="Wait for Azure's start operation to complete. Does not check SSH, RDP, or application readiness",
    )
    wait_timeout_seconds: int = Param(
        required=False,
        default=300,
        description="Maximum polling window in seconds when wait_for_completion is true. Must be greater than zero",
    )


class StartVmSummary(ActionOutput):
    status: str | None = OutputField(example_values=["Successfully started VM"])


class StartVmOutput(PermissiveActionOutput):
    operation_url: str | None = OutputField(cef_types=["url"])
    operation_status: str | None = OutputField()
    resource_group_name: str = OutputField(column_name="Resource Group Name")
    vm_name: str = OutputField(column_name="VM Name")


@app.action(
    description="Start a stopped or suspended VM",
    verbose="By default returns after Azure accepts the request. Enable wait_for_completion to confirm the Azure operation finishes, within wait_timeout_seconds (default 300). This does not check SSH/RDP or application readiness. A failed wait retains operation_url and operation_status; the VM may still start, so inspect the operation before retrying.",
    action_type="correct",
    read_only=False,
    summary_type=StartVmSummary,
    render_as="table",
    output_class=StartVmOutput,
)
@preserve_failure_params
def start_vm(params: StartVmParams, soar: SOARClient, asset: Asset) -> StartVmOutput:
    try:
        if params.wait_for_completion and params.wait_timeout_seconds <= 0:
            raise ValueError("wait_timeout_seconds must be greater than zero")
        group = validate_arm_path_value(
            params.resource_group_name, "resource_group_name"
        )
        vm_name = validate_arm_path_value(params.vm_name, "vm_name")
        endpoint = format_vm_action_endpoint(group, vm_name, "/start")
        if params.wait_for_completion:
            response, operation_url = make_vm_start_request(
                asset,
                endpoint,
                subscription_id=params.subscription_id,
                timeout_seconds=params.wait_timeout_seconds,
            )
        else:
            response = make_azure_request(
                asset, endpoint, subscription_id=params.subscription_id, method="POST"
            )
    except AsyncOperationError as exc:
        output = vm_mutation_output_fields(
            exc.response,
            resource_group_name=params.resource_group_name,
            vm_name=params.vm_name,
        )
        output.update(
            operation_url=exc.operation_url or exc.results_url,
            operation_status=exc.operation_status,
        )
        return failed_table_result(
            str(exc),
            params.model_dump(by_alias=True),
            StartVmOutput(**output),
            StartVmSummary(status=str(exc)),
        )
    except (ActionFailure, ValueError) as exc:
        return failed_table_result(
            str(exc),
            params.model_dump(),
            StartVmOutput(
                resource_group_name=params.resource_group_name,
                vm_name=params.vm_name,
            ),
            StartVmSummary(status=None),
        )

    message = "Successfully started VM"
    soar.set_summary(StartVmSummary(status=message))
    soar.set_message(f"Status: {message}")
    output = vm_mutation_output_fields(
        response,
        resource_group_name=params.resource_group_name,
        vm_name=params.vm_name,
    )
    if params.wait_for_completion:
        output.update(operation_url=operation_url, operation_status="Succeeded")
    return StartVmOutput(**output)
