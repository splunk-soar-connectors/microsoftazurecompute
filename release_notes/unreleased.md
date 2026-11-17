**Unreleased**

* Migrate Microsoft Azure Compute to the Splunk SOAR SDK.
* Add the SDK `make_request` action for custom ARM requests under the asset's configured subscription.
* Fix duplicate path separators in VM start, stop, and deallocate requests.
* Retry client-credential requests once after HTTP 401 only, preventing successful response text from replaying mutations.
* Restore IPv4/IPv6 validation for `get ip availability` and send the address as a structured query parameter.
* Align app and package Python support with SDK 7.1.2: Python 3.13 and 3.15.
* Return a clear invalid-tags error for malformed JSON or invalid tag structures in both security-group creation actions.
* Preserve original action parameters when reporting API, OAuth, and input-validation failures.
* Bound `run command` asynchronous polling to a 60-second window, stop on terminal states, and preserve tracking information when results cannot be returned.
* Add opt-in `start vm` completion polling with `wait_for_completion` (default false) and `wait_timeout_seconds` (default 300).
* Model resource tags as optional objects with user-defined keys instead of requiring example-specific tag names. Runtime tag keys, values, and existing playbook payload paths remain unchanged; generated metadata no longer lists sample tag names as fixed fields.

* **Optional start VM completion wait**

* `start vm` preserves its existing submission behavior and success message when `wait_for_completion` is false or omitted. Set it to true to wait for Azure's start operation to finish. `wait_timeout_seconds` defaults to 300, must be greater than zero when waiting is enabled, and is ignored when waiting is disabled. Polling respects positive `Retry-After` seconds with a three-second fallback and caps HTTP timeouts to the remaining polling budget. Network/transport overhead can add elapsed time. The existing Azure API version is unchanged.

* With waiting enabled, success means Azure reported terminal `Succeeded` (or completed the start synchronously). It does not establish guest OS, SSH/RDP, or application readiness. Returned data includes `operation_status` and the safe `operation_url` when Azure provides one, alongside VM identity and Azure response fields. Existing successful summary/message paths remain available.

* Azure failure/cancellation returns a failed action result with its error details. Timeout, missing tracking headers or a polling error returns failure with completion marked unconfirmed. Failed results retain original parameters, VM identity, last known operation state and available safe tracking URL; the explanation is in the action message and summary status. Inspect Azure or the operation URL before deciding to retry: the original start may still finish. Timeout does not cancel the operation, and polling never resubmits the accepted start request. `get results` is intended for guest commands, not VM-start operation URLs. Other lifecycle and resource-creation actions keep their existing behavior.

* **Run command asynchronous outcomes**

* `run command` no longer polls indefinitely or continues polling after Azure reports a terminal state. After Azure accepts a command, the app polls within a 60-second window. It respects positive `Retry-After` values in seconds, otherwise polling every three seconds, and limits each request's timeout to the remaining polling budget (up to 30 seconds). Network/transport overhead can add to elapsed time; this window does not cancel the Azure command.

* `Succeeded`: retrieve the results and retain the existing successful result fields and summary. `Failed` or `Canceled`: return a failed action result with Azure's error details. Polling timeout or status-retrieval error: return a failed result stating that completion is not confirmed. The command may still be running or may already have completed. Result-retrieval error after `Succeeded`: return failure stating that execution succeeded but its results could not be returned. This does not imply execution failed or was rolled back.

* These failed results retain the original input parameters, the last known Azure response under `action_result.data.*.results`, and the available safe tracking URLs/state: `action_result.data.*.operation_url`, `action_result.data.*.results_url`, and `action_result.data.*.operation_status`. The failure explanation is also in the action message and `action_result.summary.status`. A failed result can therefore contain data; check `action_result.status` rather than data presence.

* The accepted command is never resubmitted automatically. Use `get results` with the returned `results_url` (and the same subscription override, if used) to retrieve the outcome later rather than rerunning the command. If Azure supplied only an operation-status URL, retain it for inspection; it is not necessarily a command-results endpoint. Missing/unsafe tracking URLs cause a controlled failure after submission; unsafe URLs are never requested or exposed as recovery destinations.

* **Authentication upgrade**

* Existing delegated OAuth tokens are migrated automatically from legacy state into SDK auth state on the first action. Encrypted legacy tokens are decrypted with the asset ID before SDK storage encrypts the migrated state. Existing SDK OAuth tokens take precedence. Migrated tokens are refreshed before use because legacy relative expiry values cannot establish their current validity. If the legacy refresh token is missing, expired, revoked, or unreadable, run test connectivity to authorize the asset again. When reauthorizing, update the Microsoft Entra app registration's Web redirect URI to the SOAR webhook callback URL for this app's `oauth_callback` route. The callback URL is generated by SOAR for the app and asset; the legacy `/result` redirect is no longer used. Client credentials assets obtain fresh tokens using their configured credentials.

* **Action result compatibility**

* The SDK conversion changes some action result payloads. Check `action_result.status` to determine whether an action succeeded; a nonempty `action_result.data` does not imply success. Summary status and progress messages remain available. Synthetic success `status` fields have been removed from data rows.

* `create_tag`: For name-only creation, the Azure response remains in `action_result.data`, with `tagName` and `tagValue` added to the row. For creation with a value, the response moves from legacy `action_result.extra_data` to `action_result.data`, also with `tagName` and `tagValue`. If the connector creates the name but the value retry fails, the action fails and the data row retains the created name response, tag identity, and `failed_stage: "create_tag_value"`. The API error is available in the action result message. `start_vm`, `stop_vm`, `deallocate_vm`, `generalize_vm`, and `redeploy_vm`: Successful results include the Azure response fields plus `resource_group_name` and `vm_name`. If Azure returns an empty body, the row still contains the VM identifiers. Failed results may also include a row containing the input VM identifiers; inspect `action_result.status` and the message for outcome. `delete_vm`: Legacy success returned no data. The SDK result includes a row with `resource_group_name` and `vm_name`. `generate_token`: Legacy success returned no data. The SDK result contains an empty output row. The seven collection actions follow Azure nextLink URLs and count all returned pages. If a later page cannot be retrieved, the action fails while retaining rows collected from earlier pages; the count reflects the rows retained. Custom views use SDK-provided action parameters aligned with output rows, so each result group displays the matching input labels without adding view-only parameter fields to data rows. Several actions add input values to output rows for table or view context. These are not Azure response fields: `list_subnets` adds `resource_group_name` and `virtual_network_name`; `list_security_groups` adds `resource_group_name` and `group_type`; `run_command` adds `resource_group_name`, `vm_name`, and `command_id`. Consumers that depend on exact data-row shapes or key sets should account for these additions.

* **Command and virtual-network output schemas**

* Breaking change for `run_command` and `get_results` playbooks using bare-list command responses: `results` is now always an object. A bare status list is wrapped under `results.properties.output`; Azure operation objects remain intact, including their status, times, errors and vendor fields. Messages stay strings exactly as returned by Azure, including JSON text; consumers needing structured message content must parse the string themselves.

* Old bare-list payload: `{"results": [{"message": {"answer": 42}}]}`. New payload: `{"results": {"properties": {"output": [{"message": "{\"answer\": 42}"}]}}}`. Replace `action_result.data.*.results.*.message` with `action_result.data.*.results.properties.output.*.message` for bare lists and the documented 2017-03-30 operation response. The newer `value` response shape is preserved and modeled at `action_result.data.*.results.value.*.message`. `displayStatus` belongs on each status entry, not the top-level action output. Summary status and the `results_url` field are unchanged.

* `list_virtual_networks` now declares address prefixes as a list. Runtime network data is unchanged; use `action_result.data.*.properties.addressSpace.addressPrefixes.*` for individual prefixes.

* Evidence: Microsoft [Run Command 2017-03-30 response example](https://learn.microsoft.com/ar-sa/rest/api/compute/virtual-machines/run-command?view=rest-compute-2017-03-30), [newer value response example](https://learn.microsoft.com/en-us/rest/api/compute/virtual-machines/run-command?view=rest-compute-2025-04-01), and [virtual network API response types](https://learn.microsoft.com/en-us/rest/api/virtualnetwork/virtual-networks/get). The [2018-11-01 resource contract](https://learn.microsoft.com/en-us/azure/templates/microsoft.network/2018-11-01/virtualnetworks) also specifies addressPrefixes as string[].
