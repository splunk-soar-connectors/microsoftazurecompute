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
from posixpath import normpath
from urllib.parse import unquote, urlparse

from soar_sdk.abstract import SOARClient
from soar_sdk.action_results import ActionOutput, OutputField, PermissiveActionOutput
from soar_sdk.params import Param, Params

from ..app import Asset, app
from soar_sdk.exceptions import ActionFailure
from ..helper import make_absolute_request, normalize_command_results, resolve_subscription


class GetResultsParams(Params):
    results_url: str = Param(
        description="URL to fetch result of run command",
        primary=True,
        cef_types=["vm management results url"],
    )
    subscription_id: str | None = Param(
        description="Subscription ID to overwrite asset configuration value"
    )


class GetResultsResultOutput(PermissiveActionOutput):
    code: str = OutputField(
        example_values=[
            "ComponentStatus/StdOut/succeeded",
            "ComponentStatus/StdErr/succeeded",
        ]
    )
    level: str = OutputField(example_values=["Info"])
    message: str = OutputField()


class GetResultsOutput(PermissiveActionOutput):
    results_url: str | None = OutputField(
        column_name="Results URL",
        cef_types=["vm management results url"],
        example_values=[
            "https://management.azure.com/subscriptions/<subscription_id>/providers/Microsoft.Compute/locations/<location>/operations/<operation_id>monitor=true&api-version=2017-03-30"
        ],
    )
    displayStatus: str = OutputField(example_values=["Provisioning succeeded"])
    results: list[GetResultsResultOutput] | None = OutputField()


class GetResultsSummary(ActionOutput):
    status: str = OutputField(example_values=["Successfully fetched result"])


@app.action(
    description="Fetch the results of a previously executed run_command action",
    action_type="investigate",
    verbose="Commands in Azure can take up to 90 minutes to execute. This allows you to retrieve results of previously executed actions. Refer to <a href='https://docs.microsoft.com/en-us/azure/virtual-machines/windows/run-command' target='_blank'>API Docs</a> for more information.",
    summary_type=GetResultsSummary,
    read_only=True,
    render_as="table",
    output_class=GetResultsOutput,
)
def get_results(
    params: GetResultsParams, soar: SOARClient, asset: Asset
) -> GetResultsOutput:

    parsed = urlparse(params.results_url)
    subscription = resolve_subscription(asset, params.subscription_id)
    normalized_path = normpath(unquote(parsed.path))
    subscription_path = f"/subscriptions/{subscription}"
    if (
        parsed.scheme != "https"
        or parsed.netloc != "management.azure.com"
        or parsed.fragment
        or not normalized_path.startswith(f"{subscription_path}/")
    ):
        raise ActionFailure(
            "Please provide a valid value in the 'results_url' action parameter"
        )

    canonical_url = f"https://management.azure.com{normalized_path}"
    if parsed.query:
        canonical_url = f"{canonical_url}?{parsed.query}"
    response = make_absolute_request(asset, canonical_url)
    data = normalize_command_results(response, params.results_url)
    soar.set_summary(GetResultsSummary(status="Successfully fetched result"))
    soar.set_message("Status: Successfully fetched result")
    data.update(results_url=params.results_url)
    return GetResultsOutput(**data)
