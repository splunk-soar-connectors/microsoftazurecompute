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
"""Run Command 2017-03-30 response models shared by execution and retrieval.

Source: https://learn.microsoft.com/ar-sa/rest/api/compute/virtual-machines/run-command?view=rest-compute-2017-03-30
The documented sample returns properties.output[] with string messages.
"""

from soar_sdk.action_results import PermissiveActionOutput


class CommandStatusOutput(PermissiveActionOutput):
    code: str | None = None
    level: str | None = None
    displayStatus: str | None = None
    message: str | None = None


class CommandPropertiesOutput(PermissiveActionOutput):
    output: list[CommandStatusOutput] | None = None


class CommandErrorDetailOutput(PermissiveActionOutput):
    code: str | None = None
    message: str | None = None
    target: str | None = None


class CommandInnerErrorOutput(PermissiveActionOutput):
    errordetail: str | None = None
    exceptiontype: str | None = None


class CommandErrorOutput(CommandErrorDetailOutput):
    details: list[CommandErrorDetailOutput] | None = None
    innererror: CommandInnerErrorOutput | None = None


class CommandResponseOutput(PermissiveActionOutput):
    startTime: str | None = None
    endTime: str | None = None
    status: str | None = None
    name: str | None = None
    properties: CommandPropertiesOutput | None = None
    error: CommandErrorOutput | None = None
    # The newer documented response uses value[] (no API version change here):
    # https://learn.microsoft.com/en-us/rest/api/compute/virtual-machines/run-command?view=rest-compute-2025-04-01
    value: list[CommandStatusOutput] | None = None
