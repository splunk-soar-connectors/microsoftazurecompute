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
from ..consts import VM_LIST_TAGS_ENDPOINT


class ListTagsParams(Params):
    subscription_id: str | None = Param(
        description="Subscription ID to overwrite asset configuration value"
    )


class CountOutput(PermissiveActionOutput):
    type: str = OutputField(example_values=["Total"])
    value: float = OutputField(example_values=[22])


class ValuesOutput(PermissiveActionOutput):
    count: CountOutput
    id: str = OutputField(
        example_values=[
            "/subscriptions/a81fccf8-0405-43ae-990c-ab1389e40c6d/tagNames/author/tagValues/appdev"
        ]
    )
    tagValue: str = OutputField(example_values=["appdev"])


class ListTagsOutput(PermissiveActionOutput):
    count: CountOutput
    id: str = OutputField(
        example_values=[
            "/subscriptions/a81fccf8-0405-43ae-990c-ab1389e40c6d/tagNames/author"
        ]
    )
    tagName: str = OutputField(
        cef_types=["vm management tag name"], example_values=["author"]
    )
    values: list[ValuesOutput]


class ListTagsSummary(ActionOutput):
    num_tags: int


@app.view_handler(template="microsoftazurecompute_list_tags.html")
def display_list_tags(outputs: list[ListTagsOutput]) -> dict:
    data = [output.model_dump() for output in outputs]
    return {"results": [{"data": data, "param": {}, "summary": {}}]}


@app.action(
    description="Get the names and values of all resource tags that are defined in the subscription",
    action_type="investigate",
    read_only=True,
    summary_type=ListTagsSummary,
    view_handler=display_list_tags,
)
def list_tags(
    params: ListTagsParams, soar: SOARClient, asset: Asset
) -> list[ListTagsOutput]:

    values, page_error = make_azure_collection_request(
        asset, VM_LIST_TAGS_ENDPOINT, subscription_id=params.subscription_id
    )
    summary = ListTagsSummary(num_tags=len(values))
    outputs = [ListTagsOutput(**tag) for tag in values]
    if page_error:
        return failed_collection_result(
            f"Azure inventory is incomplete. Collected {len(values)} tags. {page_error}",
            params.model_dump(),
            outputs,
            summary,
        )
    soar.set_summary(summary)
    return outputs
