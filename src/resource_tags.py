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
"""Azure resource tags have user-defined keys, not a fixed property schema."""

from soar_sdk.action_results import PermissiveActionOutput


class ResourceTagsOutput(PermissiveActionOutput):
    """Retain arbitrary tag keys without advertising example names as fields.

    The SDK cannot publish a typed dictionary as an output datapath. Its
    permissive object model preserves the mapping without inventing static
    tag-name datapaths or changing the runtime JSON shape.
    """
