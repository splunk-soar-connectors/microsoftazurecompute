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
"""Preserve action inputs when reporting expected request/auth/validation errors."""

from collections.abc import Callable
from functools import wraps

from soar_sdk.auth.client import OAuthClientError
from soar_sdk.exceptions import ActionFailure
from soar_sdk.params import Params


def preserve_failure_params(function: Callable) -> Callable:
    """Return the SDK's failure tuple before its exception adapter loses inputs.

    Apply inside the SDK action decorator. Existing results, including partial
    failures with data and summaries, pass through unchanged. Unexpected errors
    still reach the SDK's exception reporting.
    """

    @wraps(function)
    def wrapped(params: Params, *args, **kwargs):
        try:
            return function(params, *args, **kwargs)
        except (ActionFailure, OAuthClientError, ValueError) as exc:
            return False, str(exc), params.model_dump(by_alias=True)

    return wrapped
