# File: microsoftazurecompute_consts.py
#
# Copyright (c) 2019-2025 Splunk Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied. See the License for the specific language governing permissions
# and limitations under the License.
#
#
MS_BASE_URL = "https://management.azure.com/subscriptions/{subscriptionId}"

VM_GET_SYSTEM_INFO_ENDPOINT = "/resourceGroups/{resourceGroupName}/providers/Microsoft.Compute/virtualMachines/{vmName}?api-version=2018-06-01"
VM_LIST_VMS_RESOURCE_GROUP_ENDPOINT = "/resourceGroups/{resourceGroupName}/providers/Microsoft.Compute/virtualMachines?api-version=2018-06-01"
VM_LIST_VMS_ALL_ENDPOINT = "/providers/Microsoft.Compute/virtualMachines?api-version=2018-06-01"
VM_ACTION_ENDPOINT = "/resourceGroups/{resourceGroupName}/providers/Microsoft.Compute/virtualMachines/{vmName}/{action}?api-version=2018-06-01"
VM_SNAPSHOT_VM_ENDPOINT = "/resourceGroups/{resourceGroupName}/providers/Microsoft.Compute/snapshots/{snapshotName}?api-version=2018-06-01"
VM_LIST_TAGS_ENDPOINT = "/tagNames?api-version=2018-05-01"
VM_CREATE_TAG_ENDPOINT = "/tagNames/{tagName}{tagValue}?api-version=2018-05-01"
VM_CREATE_TAG_VALUE_PART = "/tagValues/{tagValue}"
VM_RESOURCE_GROUP_ENDPOINT = "/resourcegroups?api-version=2018-05-01"
VM_LIST_SNAPSHOTS_ENDPOINT = "{resourceValue}/providers/Microsoft.Compute/snapshots?api-version=2018-06-01"
VM_RESOURCE_GROUP_VALUE_PART = "/resourceGroups/{resourceGroupName}"
VM_SECURITY_GROUP_ENDPOINT = "/resourceGroups/{resourceGroupName}/providers/Microsoft.Network/{groupType}{groupName}?api-version=2018-11-01"
VM_LIST_VIRTUAL_NETWORKS_ENDPOINT = "{resourceGroup}/providers/Microsoft.Network/virtualNetworks?api-version=2018-11-01"
VM_LIST_SUBNETS_ENDPOINT = "/resourceGroups/{resourceGroupName}/providers/Microsoft.Network/virtualNetworks/{virtualNetworkName}/\
subnets?api-version=2018-11-01"
VM_CHECK_IP_AVAIL = "/resourceGroups/{resourceGroup}/providers/Microsoft.Network/virtualNetworks/{virtualNetwork}/\
CheckIPAddressAvailability?ipAddress={ip}&api-version=2018-11-01"
VM_RUN_COMMAND_ENDPOINT = "/resourceGroups/{resourceGroupName}/providers/Microsoft.Compute/virtualMachines/{vmName}/\
runCommand?api-version=2017-03-30"

TEST_CONNECTIVITY_FAILED_MSG = "Test Connectivity Failed"
MS_PHANTOM_SYS_INFO_URL = "{url}rest/system_info"
MS_PHANTOM_ASSET_INFO_URL = "{url}rest/asset/{asset_id}"

MS_AZURE_CONFIG_TENANT = "tenant_id"
MS_AZURE_CONFIG_SUBSCRIPTION = "subscription_id"
MS_AZURE_CONFIG_CLIENT_ID = "client_id"
MS_AZURE_CONFIG_CLIENT_SECRET = "client_secret"  # pragma: allowlist secret
MS_AZURE_CONFIG_ADMIN_ACCESS = "admin_access"
MS_AZURE_CONFIG_ADMIN_CONSENT = "admin_consent"
MS_AZURE_TOKEN_STRING = "token"
MS_AZURE_ACCESS_TOKEN_STRING = "access_token"
MS_AZURE_REFRESH_TOKEN_STRING = "refresh_token"
MS_AZURE_STATE_IS_ENCRYPTED = "is_encrypted"
MS_AZURE_PHANTOM_BASE_URL = "{phantom_base_url}rest"
MS_AZURE_PHANTOM_SYS_INFO_URL = "/system_info"
MS_AZURE_PHANTOM_ASSET_INFO_URL = "/asset/{asset_id}"
MS_AZURE_BASE_URL_NOT_FOUND_MSG = "Phantom Base URL not found in System Settings. Please specify this value in System Settings."
MS_AZURE_HTML_ERR = "Bad Request Bad Request - Invalid URL HTTP Error 400. The request URL is invalid."

# For authorization code
TC_FILE = "oauth_task.out"
SERVER_TOKEN_URL = "https://login.microsoftonline.com/{0}/oauth2/token"

MS_REST_URL_NOT_AVAILABLE_MSG = "Rest URL not available. Error: {error}"
MS_OAUTH_URL_MSG = "Using OAuth URL:"
MS_AUTHORIZE_USER_MSG = "Please authorize user in a separate tab using URL:"
MS_GENERATING_ACCESS_TOKEN_MSG = "Generating access token"
MS_TC_STATUS_SLEEP = 3
MS_REST_REQUEST_SCOPE = "user_impersonation https://management.azure.com/user_impersonation \
offline_access group.readwrite.all user.readwrite.all"
MS_AZURE_CODE_GENERATION_SCOPE = "https://management.azure.com/user_impersonation"

MS_AZURE_UNKNOWN_ERR_MSG = "Unknown error occurred. Please check the asset configuration and|or action parameters."
MS_AZURE_ERR_CODE_UNAVAILABLE = "Error code unavailable"
MS_AZURE_UNICODE_DAMMIT_TYPE_ERR_MSG = "Error occurred while connecting to the Microsoft Azure Compute server. \
Please check the asset configuration and|or the action parameters."
MS_AZURE_INVALID_PERMISSION_ERR = "Error occurred while saving the newly generated access token \
(in place of the expired token) in the state file."
MS_AZURE_INVALID_PERMISSION_ERR += " Please check the owner, owner group, and the permissions of the state file. The Phantom "
MS_AZURE_INVALID_PERMISSION_ERR += "user should have the correct access rights and ownership for the corresponding state file \
(refer to readme file for more information)."
MS_AZURE_ERR_MSG = "Status Code: {status_code}. Data from server: {err_msg}"
MS_AZURE_SERVER_ERR_MSG = "Error from server"
MS_AZURE_INVALID_JSON = "{err_msg}: Invalid format of body. Please provide valid JSON format in the '{param}' action parameter"
MS_AZURE_GROUP_TYPE_ERR_MSG = "Please provide a valid value in the 'group_type' action parameter. Expected values are 'application' or 'network'"
MS_AZURE_INVALID_TOKEN_MSGS = ["token is invalid", "Access token has expired", "ExpiredAuthenticationToken", "AuthenticationFailed"]
MS_AZURE_TIMEOUT = 30
MS_AZURE_BAD_REQUEST_CODE = 400
MS_AZURE_NOT_FOUND_CODE = 404
