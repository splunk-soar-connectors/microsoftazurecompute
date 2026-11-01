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
from ..helper import make_async_request, validate_arm_path_value
from ..consts import VM_RUN_COMMAND_ENDPOINT
from ..helper import normalize_command_results, parse_command_list


class RunCommandParams(Params):
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
    command_id: str = Param(
        description="The command to run against the VM",
        primary=True,
        cef_types=["vm management command id"],
    )
    script: str | None = Param(
        description="The script to be executed. When this value is given, the given script will override the default script of the command"
    )
    script_parameters: str | None = Param(description="The run command parameters")
    subscription_id: str | None = Param(
        description="Subscription ID to overwrite asset configuration value"
    )


class RunCommandResultOutput(PermissiveActionOutput):
    code: str = OutputField(
        example_values=[
            "ComponentStatus/StdOut/succeeded",
            "ComponentStatus/StdErr/succeeded",
        ]
    )
    level: str = OutputField(example_values=["Info", "Error", "Warning"])
    message: str = OutputField()


class RunCommandOutput(PermissiveActionOutput):
    resource_group_name: str = OutputField(column_name="Resource Group Name")
    vm_name: str = OutputField(column_name="VM Name")
    command_id: str = OutputField(column_name="Command ID")
    script: str = OutputField(column_name="Script")
    script_parameters: str = OutputField(column_name="Parameters")
    displayStatus: str = OutputField(example_values=["Provisioning succeeded"])
    results_url: str = OutputField(
        column_name="Results URL",
        cef_types=["vm management results url"],
        example_values=[
            "https://management.azure.com/subscriptions/<subscription_id>/providers/Microsoft.Compute/locations/<location>/operations/<operation_id>monitor=true&api-version=2017-03-30"
        ],
    )
    results: list[RunCommandResultOutput] | None = OutputField()


class RunCommandSummary(ActionOutput):
    status: str = OutputField(example_values=["Successfully executed command"])


@app.action(
    description="Run a command on the virtual machine",
    action_type="generic",
    read_only=False,
    verbose="Run a command or a script in an Azure Windows or Linux VM. Refer to <a href='https://learn.microsoft.com/en-us/rest/api/compute/virtual-machines/run-command?tabs=HTTP' target='_blank'>API Docs</a> for more information.",
    summary_type=RunCommandSummary,
    render_as="table",
    output_class=RunCommandOutput,
)
def run_command(
    params: RunCommandParams, soar: SOARClient, asset: Asset
) -> RunCommandOutput:

    group = validate_arm_path_value(params.resource_group_name, "resource_group_name")
    vm_name = validate_arm_path_value(params.vm_name, "vm_name")
    script = parse_command_list(params.script, "script", allow_plain_text=True)
    script_parameters = parse_command_list(
        params.script_parameters, "script_parameters", allow_plain_text=False
    )
    body = {
        "commandId": params.command_id,
        "script": script,
        "parameters": script_parameters,
    }
    endpoint = VM_RUN_COMMAND_ENDPOINT.format(resourceGroupName=group, vmName=vm_name)
    response, results_url = make_async_request(
        asset, endpoint, subscription_id=params.subscription_id, json_body=body
    )
    data = normalize_command_results(response, results_url)
    soar.set_summary(RunCommandSummary(status="Successfully executed command"))
    soar.set_message("Status: Successfully executed command")
    data.update(
        resource_group_name=params.resource_group_name,
        vm_name=params.vm_name,
        command_id=params.command_id,
        script=params.script or "",
        script_parameters=params.script_parameters or "",
    )
    return RunCommandOutput(**data)
