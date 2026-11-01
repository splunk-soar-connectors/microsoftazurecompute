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
from ..helper import failed_collection_result, make_azure_collection_request
from ..consts import VM_RESOURCE_GROUP_ENDPOINT


class ListResourceGroupsParams(Params):
    subscription_id: str | None = Param(
        description="Subscription ID to overwrite asset configuration value"
    )


class PropertiesOutput(PermissiveActionOutput):
    provisioningState: str = OutputField(
        column_name="Provisioning State", example_values=["Succeeded"]
    )


class TagsOutput(PermissiveActionOutput):
    company: str = OutputField(example_values=["mycomp"])
    keyname____keyvalue__: str = OutputField(
        example_values=["abcd"], alias='{"keyname": "keyvalue"}'
    )


class ListResourceGroupsOutput(PermissiveActionOutput):
    name: str = OutputField(
        column_name="Resource Name",
        cef_types=["vm management resource group"],
        example_values=["DefaultResourceGroup-EUS"],
    )
    location: str = OutputField(column_name="Location", example_values=["eastus"])
    properties: PropertiesOutput
    id: str = OutputField(
        column_name="ID",
        example_values=[
            "/subscriptions/a81fccf8-0405-43ae-990c-ab1389e40c6d/resourceGroups/DefaultResourceGroup-EUS"
        ],
    )
    tags: TagsOutput


class ListResourceGroupsSummary(ActionOutput):
    num_resource_groups: int = OutputField(example_values=[4])


@app.action(
    description="Get the list of resource groups for the subscription",
    action_type="investigate",
    read_only=True,
    summary_type=ListResourceGroupsSummary,
    render_as="table",
)
def list_resource_groups(
    params: ListResourceGroupsParams, soar: SOARClient, asset: Asset
) -> list[ListResourceGroupsOutput]:

    values, page_error = make_azure_collection_request(
        asset, VM_RESOURCE_GROUP_ENDPOINT, subscription_id=params.subscription_id
    )
    summary = ListResourceGroupsSummary(num_resource_groups=len(values))
    outputs = [ListResourceGroupsOutput(**item) for item in values]
    if page_error:
        return failed_collection_result(
            "Azure inventory is incomplete. "
            f"Collected {len(values)} resource groups. {page_error}",
            params.model_dump(),
            outputs,
            summary,
        )
    soar.set_summary(summary)
    return outputs
