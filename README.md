[comment]: # "Auto-generated SOAR connector documentation"
# Microsoft Azure Compute

Publisher: Splunk  
Connector Version: 2\.1\.1  
Product Vendor: Microsoft  
Product Name: Azure Compute  
Product Version Supported (regex): "\.\*"  
Minimum Product Version: 4\.10\.0\.40961  

This app implements virtualization actions for Microsoft Azure Virtual Machines

[comment]: # " File: readme.md"
[comment]: # "  Copyright (c) 2019-2021 Splunk Inc."
[comment]: # ""
[comment]: # "  Licensed under Apache 2.0 (https://www.apache.org/licenses/LICENSE-2.0.txt)"
[comment]: # ""
-   For an admin user, you can run the test connectivity directly.
-   For a non-admin user, you need to get the admin consent first. This can be done by granting
    admin consent in the Azure portal.

## Authentication

This app requires creating a Microsoft Graph Application. To do so, navigate to
[https://apps.dev.microsoft.com](https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps/ApplicationsListBlade)
in a browser and log in with a Microsoft account, then select **New registration** .  
  
On the next page, give your application a name and select **Register** .  
  
Once the app is created, three steps need to be taken on the next page:  
  
Under **Certificates and Secrets** , select **New client secret** . Note this key somewhere secure,
as it cannot be retrieved after closing the window.  
  
**For Interactive OAuth**

-   Under **Authentication** select **Add a platform** . In the **Add a platform** window, select
    **Web** . The **Redirect URLs** should be filled right here. It should look something like:

      

    https://\<phantom_host>/rest/handler/microsoftazurecompute_39c7128b-666b-4a16-9d44-afab6a9b825d/\<asset_name>/result

-   Under **API permissions** the following **Delegated Permissions** need to be added:
    -   Group.ReadWrite.All
    -   offline_access
    -   User.ReadWrite.All

**For Non-Interactive OAuth**

-   Under **API permissions** the following **Application Permissions** need to be added:
    -   Group.ReadWrite.All
    -   User.ReadWrite.All
-   On the Azure portal, go to subscriptions and select your subscription.
-   Go to Access control(IAM) section and click on add role assignment.
-   Select **Contributer** in the **Role** field from the drop down and select your application in
    the **Select** field.

After making these changes, click **Save** at the bottom of the screen.

## Configure the Microsoft Azure Compute Phantom app Asset

When creating an asset for the **Microsoft Azure Compute** app, place **Subscription Id** of the app
in the **Subscription ID** field, place **Application Id** of the app created during the previous
step in the **Client ID** field, and place the password generated during the app creation process in
the **Client Secret** field. Then, after filling out the **Tenant ID** field, click **SAVE** .  
  
After saving, a new field will appear in the **Asset Settings** tab. Take the URL found in the
**POST incoming for Microsoft Azure Compute to this location** field and place it in the **Redirect
URLs** field mentioned in a previous step. To this URL, add **/result** . After doing so the URL
should look something like:  
  

https://\<phantom_host>/rest/handler/microsoftazurecompute_39c7128b-666b-4a16-9d44-afab6a9b825d/\<asset_name>/result

  
Once again, click save at the bottom of the screen.

## Method to run test connectivity

After setting up the asset and user, click the **TEST CONNECTIVITY** button. A window should pop up
and display a URL. Navigate to this URL in a separate browser tab. This new tab will redirect to a
Microsoft login page. Log in to a Microsoft account. After logging in, review the requested
permissions listed, then click **Accept** . Finally, close that tab. The test connectivity window
should show a success.  
If the admin consent is required then, the display url will occur twice. The first one will be for
admin access.  
  
The app should now be ready to be used.

## State file permissions

Please check the permissions for the state file as mentioned below.

#### State file path

-   For Non-NRI instance: /opt/phantom/local_data/app_states/\<appid>/\<asset_id>\_state.json
-   For NRI instance:
    /\<PHANTOM_HOME_DIRECTORY>/local_data/app_states/\<appid>/\<asset_id>\_state.json

#### State file permissions

-   File rights: rw-rw-r-- (664) (The phantom user should have read and write access for the state
    file)
-   File owner: Appropriate phantom user

## Playbook Backward Compatibility

-   A new action has been added. Hence, it is requested to the end-user to please update their
    existing playbooks by inserting the corresponding action blocks for this action on the earlier
    versions of the app.

      

    -   Get Results

-   The parameters have been modified in the below existing action. Hence, it is requested to the
    end-user to please update their existing playbooks by re-inserting \| modifying \| deleting the
    corresponding action blocks on the earlier versions of the app.

      

    -   Run Command - Below parameter have been modified

          

        -   The parameter 'body' has been removed
        -   New parameters 'command_id', 'script', 'script_parameters' have been added


### Configuration Variables
The below configuration variables are required for this Connector to operate.  These variables are specified when configuring a Azure Compute asset in SOAR.

VARIABLE | REQUIRED | TYPE | DESCRIPTION
-------- | -------- | ---- | -----------
**subscription\_id** |  required  | string | Subscription ID
**tenant\_id** |  required  | string | Tenant ID
**client\_id** |  required  | string | Application \(client\) ID assigned to your Azure Compute app
**client\_secret** |  required  | password | Client Secret
**admin\_access** |  optional  | boolean | Admin Access Required
**admin\_consent** |  optional  | boolean | Admin consent already provided

### Supported Actions  
[test connectivity](#action-test-connectivity) - Validate the asset configuration for connectivity using supplied configuration  
[generate token](#action-generate-token) - Generates a token  
[get system info](#action-get-system-info) - Get information about a VM  
[list vms](#action-list-vms) - Get the list of registered VMs  
[snapshot vm](#action-snapshot-vm) - Take a snapshot of the VM  
[start vm](#action-start-vm) - Start a stopped or suspended VM  
[stop vm](#action-stop-vm) - Stop a VM  
[delete vm](#action-delete-vm) - Delete a VM  
[deallocate vm](#action-deallocate-vm) - Shut down the virtual machine and release the compute resources\. You are not billed for the compute resource that this virtual machine uses  
[list tags](#action-list-tags) - Get the names and values of all resource tags that are defined in the subscription  
[create tag](#action-create-tag) - Create or update a tag  
[list resource groups](#action-list-resource-groups) - Get the list of resource groups for the subscription  
[list snapshots](#action-list-snapshots) - Get the list of snapshots under the subscription  
[list security groups](#action-list-security-groups) - Get the list of all security groups in a resource group  
[add network group](#action-add-network-group) - Add a network security group in a resource group  
[add application group](#action-add-application-group) - Add an application security groups in a resource group  
[list virtual networks](#action-list-virtual-networks) - Get the list of virtual networks  
[list subnets](#action-list-subnets) - Get the list of subnets  
[get ip availability](#action-get-ip-availability) - Check if a private IP address is available for use  
[generalize vm](#action-generalize-vm) - Set the state of the virtual machine to be generalized  
[redeploy vm](#action-redeploy-vm) - Redeploy a virtual machine  
[run command](#action-run-command) - Run a command on the virtual machine  
[get results](#action-get-results) - Fetch the results of a previously executed run\_command action  

## action: 'test connectivity'
Validate the asset configuration for connectivity using supplied configuration

Type: **test**  
Read only: **True**

#### Action Parameters
No parameters are required for this action

#### Action Output
No Output  

## action: 'generate token'
Generates a token

Type: **generic**  
Read only: **False**

This action generated a new token whenever any action fails because of an invalid or expired token\.

#### Action Parameters
No parameters are required for this action

#### Action Output
DATA PATH | TYPE | CONTAINS
--------- | ---- | --------
action\_result\.data | string | 
action\_result\.status | string | 
action\_result\.message | string | 
action\_result\.summary | string | 
summary\.total\_objects | numeric | 
summary\.total\_objects\_successful | numeric |   

## action: 'get system info'
Get information about a VM

Type: **investigate**  
Read only: **True**

#### Action Parameters
PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**resource\_group\_name** |  required  | The name of the resource group | string |  `vm management resource group` 
**vm\_name** |  required  | The name of the virtual machine | string |  `vm management virtual machine` 

#### Action Output
DATA PATH | TYPE | CONTAINS
--------- | ---- | --------
action\_result\.parameter\.resource\_group\_name | string |  `vm management resource group` 
action\_result\.parameter\.vm\_name | string |  `vm management virtual machine` 
action\_result\.data\.\*\.id | string | 
action\_result\.data\.\*\.location | string | 
action\_result\.data\.\*\.name | string |  `vm management virtual machine` 
action\_result\.data\.\*\.properties\.diagnosticsProfile\.bootDiagnostics\.enabled | boolean | 
action\_result\.data\.\*\.properties\.diagnosticsProfile\.bootDiagnostics\.storageUri | string |  `url` 
action\_result\.data\.\*\.properties\.hardwareProfile\.vmSize | string | 
action\_result\.data\.\*\.properties\.networkProfile\.networkInterfaces\.\*\.id | string | 
action\_result\.data\.\*\.properties\.osProfile\.adminUsername | string |  `user name` 
action\_result\.data\.\*\.properties\.osProfile\.allowExtensionOperations | boolean | 
action\_result\.data\.\*\.properties\.osProfile\.computerName | string |  `vm management virtual machine` 
action\_result\.data\.\*\.properties\.osProfile\.linuxConfiguration\.disablePasswordAuthentication | boolean | 
action\_result\.data\.\*\.properties\.osProfile\.linuxConfiguration\.provisionVMAgent | boolean | 
action\_result\.data\.\*\.properties\.osProfile\.windowsConfiguration\.enableAutomaticUpdates | boolean | 
action\_result\.data\.\*\.properties\.osProfile\.windowsConfiguration\.provisionVMAgent | boolean | 
action\_result\.data\.\*\.properties\.provisioningState | string | 
action\_result\.data\.\*\.properties\.storageProfile\.imageReference\.offer | string | 
action\_result\.data\.\*\.properties\.storageProfile\.imageReference\.publisher | string | 
action\_result\.data\.\*\.properties\.storageProfile\.imageReference\.sku | string | 
action\_result\.data\.\*\.properties\.storageProfile\.imageReference\.version | string | 
action\_result\.data\.\*\.properties\.storageProfile\.osDisk\.caching | string | 
action\_result\.data\.\*\.properties\.storageProfile\.osDisk\.createOption | string | 
action\_result\.data\.\*\.properties\.storageProfile\.osDisk\.diskSizeGB | numeric | 
action\_result\.data\.\*\.properties\.storageProfile\.osDisk\.managedDisk\.id | string | 
action\_result\.data\.\*\.properties\.storageProfile\.osDisk\.managedDisk\.storageAccountType | string | 
action\_result\.data\.\*\.properties\.storageProfile\.osDisk\.name | string | 
action\_result\.data\.\*\.properties\.storageProfile\.osDisk\.osType | string | 
action\_result\.data\.\*\.properties\.storageProfile\.osDisk\.vhd\.uri | string | 
action\_result\.data\.\*\.properties\.vmId | string | 
action\_result\.data\.\*\.resources\.\*\.id | string | 
action\_result\.data\.\*\.resources\.\*\.location | string | 
action\_result\.data\.\*\.resources\.\*\.name | string | 
action\_result\.data\.\*\.resources\.\*\.properties\.autoUpgradeMinorVersion | boolean | 
action\_result\.data\.\*\.resources\.\*\.properties\.provisioningState | string | 
action\_result\.data\.\*\.resources\.\*\.properties\.publisher | string | 
action\_result\.data\.\*\.resources\.\*\.properties\.settings\.azureResourceId | string | 
action\_result\.data\.\*\.resources\.\*\.properties\.settings\.stopOnMultipleConnections | string | 
action\_result\.data\.\*\.resources\.\*\.properties\.settings\.workspaceId | string | 
action\_result\.data\.\*\.resources\.\*\.properties\.type | string | 
action\_result\.data\.\*\.resources\.\*\.properties\.typeHandlerVersion | string | 
action\_result\.data\.\*\.resources\.\*\.type | string | 
action\_result\.data\.\*\.tags\.author | string | 
action\_result\.data\.\*\.tags\.company | string | 
action\_result\.data\.\*\.type | string | 
action\_result\.status | string | 
action\_result\.message | string | 
action\_result\.summary | string | 
summary\.total\_objects | numeric | 
summary\.total\_objects\_successful | numeric |   

## action: 'list vms'
Get the list of registered VMs

Type: **investigate**  
Read only: **True**

#### Action Parameters
PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**resource\_group\_name** |  optional  | Name of the resource group | string |  `vm management resource group` 

#### Action Output
DATA PATH | TYPE | CONTAINS
--------- | ---- | --------
action\_result\.parameter\.resource\_group\_name | string |  `vm management resource group` 
action\_result\.data\.\*\.id | string | 
action\_result\.data\.\*\.location | string | 
action\_result\.data\.\*\.name | string |  `vm management virtual machine` 
action\_result\.data\.\*\.properties\.diagnosticsProfile\.bootDiagnostics\.enabled | boolean | 
action\_result\.data\.\*\.properties\.diagnosticsProfile\.bootDiagnostics\.storageUri | string |  `url` 
action\_result\.data\.\*\.properties\.hardwareProfile\.vmSize | string | 
action\_result\.data\.\*\.properties\.networkProfile\.networkInterfaces\.\*\.id | string | 
action\_result\.data\.\*\.properties\.osProfile\.adminUsername | string |  `user name` 
action\_result\.data\.\*\.properties\.osProfile\.allowExtensionOperations | boolean | 
action\_result\.data\.\*\.properties\.osProfile\.computerName | string |  `vm management virtual machine` 
action\_result\.data\.\*\.properties\.osProfile\.linuxConfiguration\.disablePasswordAuthentication | boolean | 
action\_result\.data\.\*\.properties\.osProfile\.linuxConfiguration\.provisionVMAgent | boolean | 
action\_result\.data\.\*\.properties\.osProfile\.linuxConfiguration\.ssh\.publicKeys\.\*\.path | string | 
action\_result\.data\.\*\.properties\.osProfile\.linuxConfiguration\.ssh\.publicKeys\.\*\.keyData | string | 
action\_result\.data\.\*\.properties\.osProfile\.windowsConfiguration\.enableAutomaticUpdates | boolean | 
action\_result\.data\.\*\.properties\.osProfile\.windowsConfiguration\.provisionVMAgent | boolean | 
action\_result\.data\.\*\.properties\.provisioningState | string | 
action\_result\.data\.\*\.properties\.storageProfile\.imageReference\.offer | string | 
action\_result\.data\.\*\.properties\.storageProfile\.imageReference\.publisher | string | 
action\_result\.data\.\*\.properties\.storageProfile\.imageReference\.sku | string | 
action\_result\.data\.\*\.properties\.storageProfile\.imageReference\.version | string | 
action\_result\.data\.\*\.properties\.storageProfile\.osDisk\.caching | string | 
action\_result\.data\.\*\.properties\.storageProfile\.osDisk\.createOption | string | 
action\_result\.data\.\*\.properties\.storageProfile\.osDisk\.diskSizeGB | numeric | 
action\_result\.data\.\*\.properties\.storageProfile\.osDisk\.managedDisk\.id | string | 
action\_result\.data\.\*\.properties\.storageProfile\.osDisk\.managedDisk\.storageAccountType | string | 
action\_result\.data\.\*\.properties\.storageProfile\.osDisk\.name | string | 
action\_result\.data\.\*\.properties\.storageProfile\.osDisk\.osType | string | 
action\_result\.data\.\*\.properties\.storageProfile\.osDisk\.vhd\.uri | string | 
action\_result\.data\.\*\.properties\.vmId | string | 
action\_result\.data\.\*\.resources\.\*\.id | string | 
action\_result\.data\.\*\.tags\.author | string | 
action\_result\.data\.\*\.tags\.company | string | 
action\_result\.data\.\*\.tags\.type | string | 
action\_result\.data\.\*\.type | string | 
action\_result\.status | string | 
action\_result\.message | string | 
action\_result\.summary\.num\_vms | numeric | 
summary\.total\_objects | numeric | 
summary\.total\_objects\_successful | numeric |   

## action: 'snapshot vm'
Take a snapshot of the VM

Type: **generic**  
Read only: **False**

While creating a snapshot using the COPY option, 'source\_resource\_id' parameter is required and while using the IMPORT option, 'source\_uri' parameter is required\. For the 'source\_uri' parameter, the uri value should be valid page blob uri path\. For more information refer to <a href='https\://docs\.microsoft\.com/en\-us/rest/api/compute/snapshots/create\-or\-update' target='\_blank'>API Docs</a>\.

#### Action Parameters
PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**resource\_group\_name** |  required  | The name of the resource group | string |  `vm management resource group` 
**snapshot\_name** |  required  | The name of the snapshot that is being created\. The name can't be changed after the snapshot is created\. Supported characters for the name are a\-z, A\-Z, 0\-9, and \_\. The max name length is 80 characters | string | 
**location** |  required  | Resource location | string | 
**create\_option** |  required  | Source for disk's creation | string | 
**source\_resource\_id** |  optional  | If create\_option is Copy, this is the ARM ID of the source snapshot or disk | string | 
**source\_uri** |  optional  | If create\_option is Import, this is the URI of a blob to be imported into a managed disk | string | 

#### Action Output
DATA PATH | TYPE | CONTAINS
--------- | ---- | --------
action\_result\.parameter\.create\_option | string | 
action\_result\.parameter\.location | string | 
action\_result\.parameter\.resource\_group\_name | string |  `vm management resource group` 
action\_result\.parameter\.snapshot\_name | string | 
action\_result\.parameter\.source\_resource\_id | string | 
action\_result\.parameter\.source\_uri | string | 
action\_result\.data\.\*\.location | string | 
action\_result\.data\.\*\.name | string | 
action\_result\.data\.\*\.properties\.creationData\.createOption | string | 
action\_result\.data\.\*\.properties\.creationData\.sourceResourceId | string | 
action\_result\.data\.\*\.properties\.creationData\.sourceUri | string | 
action\_result\.data\.\*\.properties\.diskSizeBytes | numeric | 
action\_result\.data\.\*\.properties\.diskSizeGB | numeric | 
action\_result\.data\.\*\.properties\.faultDomain | numeric |  `domain` 
action\_result\.data\.\*\.properties\.isArmResource | boolean | 
action\_result\.data\.\*\.properties\.osType | string | 
action\_result\.data\.\*\.properties\.provisioningState | string | 
action\_result\.data\.\*\.sku\.name | string | 
action\_result\.data\.\*\.sku\.tier | string | 
action\_result\.data\.\*\.tags\.author | string | 
action\_result\.status | string | 
action\_result\.message | string | 
action\_result\.summary\.provisioning\_state | string | 
action\_result\.summary\.status | string | 
summary\.total\_objects | numeric | 
summary\.total\_objects\_successful | numeric |   

## action: 'start vm'
Start a stopped or suspended VM

Type: **correct**  
Read only: **False**

#### Action Parameters
PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**resource\_group\_name** |  required  | The name of the resource group | string |  `vm management resource group` 
**vm\_name** |  required  | The name of the virtual machine | string |  `vm management virtual machine` 

#### Action Output
DATA PATH | TYPE | CONTAINS
--------- | ---- | --------
action\_result\.parameter\.resource\_group\_name | string |  `vm management resource group` 
action\_result\.parameter\.vm\_name | string |  `vm management virtual machine` 
action\_result\.data | string | 
action\_result\.status | string | 
action\_result\.message | string | 
action\_result\.summary\.status | string | 
summary\.total\_objects | numeric | 
summary\.total\_objects\_successful | numeric |   

## action: 'stop vm'
Stop a VM

Type: **contain**  
Read only: **False**

#### Action Parameters
PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**resource\_group\_name** |  required  | The name of the resource group | string |  `vm management resource group` 
**vm\_name** |  required  | The name of the virtual machine | string |  `vm management virtual machine` 

#### Action Output
DATA PATH | TYPE | CONTAINS
--------- | ---- | --------
action\_result\.parameter\.resource\_group\_name | string |  `vm management resource group` 
action\_result\.parameter\.vm\_name | string |  `vm management virtual machine` 
action\_result\.data | string | 
action\_result\.status | string | 
action\_result\.message | string | 
action\_result\.summary\.status | string | 
summary\.total\_objects | numeric | 
summary\.total\_objects\_successful | numeric |   

## action: 'delete vm'
Delete a VM

Type: **contain**  
Read only: **False**

#### Action Parameters
PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**resource\_group\_name** |  required  | The name of the resource group | string |  `vm management resource group` 
**vm\_name** |  required  | The name of the virtual machine | string |  `vm management virtual machine` 

#### Action Output
DATA PATH | TYPE | CONTAINS
--------- | ---- | --------
action\_result\.parameter\.resource\_group\_name | string |  `vm management resource group` 
action\_result\.parameter\.vm\_name | string |  `vm management virtual machine` 
action\_result\.data | string | 
action\_result\.status | string | 
action\_result\.message | string | 
action\_result\.summary\.status | string | 
summary\.total\_objects | numeric | 
summary\.total\_objects\_successful | numeric |   

## action: 'deallocate vm'
Shut down the virtual machine and release the compute resources\. You are not billed for the compute resource that this virtual machine uses

Type: **contain**  
Read only: **False**

#### Action Parameters
PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**resource\_group\_name** |  required  | The name of the resource group | string |  `vm management resource group` 
**vm\_name** |  required  | The name of the virtual machine | string |  `vm management virtual machine` 

#### Action Output
DATA PATH | TYPE | CONTAINS
--------- | ---- | --------
action\_result\.parameter\.resource\_group\_name | string |  `vm management resource group` 
action\_result\.parameter\.vm\_name | string |  `vm management virtual machine` 
action\_result\.data | string | 
action\_result\.status | string | 
action\_result\.message | string | 
action\_result\.summary\.status | string | 
summary\.total\_objects | numeric | 
summary\.total\_objects\_successful | numeric |   

## action: 'list tags'
Get the names and values of all resource tags that are defined in the subscription

Type: **investigate**  
Read only: **True**

#### Action Parameters
No parameters are required for this action

#### Action Output
DATA PATH | TYPE | CONTAINS
--------- | ---- | --------
action\_result\.data\.\*\.count\.type | string | 
action\_result\.data\.\*\.count\.value | numeric | 
action\_result\.data\.\*\.id | string | 
action\_result\.data\.\*\.tagName | string |  `vm management tag name` 
action\_result\.data\.\*\.values\.\*\.count\.type | string | 
action\_result\.data\.\*\.values\.\*\.count\.value | numeric | 
action\_result\.data\.\*\.values\.\*\.id | string | 
action\_result\.data\.\*\.values\.\*\.tagValue | string | 
action\_result\.status | string | 
action\_result\.message | string | 
action\_result\.summary\.num\_tags | numeric | 
summary\.total\_objects | numeric | 
summary\.total\_objects\_successful | numeric |   

## action: 'create tag'
Create or update a tag

Type: **generic**  
Read only: **False**

#### Action Parameters
PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**tag\_name** |  required  | The name of the tag | string |  `vm management tag name` 
**tag\_value** |  optional  | The value of the tag to create or update | string | 

#### Action Output
DATA PATH | TYPE | CONTAINS
--------- | ---- | --------
action\_result\.parameter\.tag\_name | string |  `vm management tag name` 
action\_result\.parameter\.tag\_value | string | 
action\_result\.data | string | 
action\_result\.data\.\*\.count\.type | string | 
action\_result\.data\.\*\.count\.value | numeric | 
action\_result\.data\.\*\.id | string | 
action\_result\.data\.\*\.tagName | string | 
action\_result\.status | string | 
action\_result\.message | string | 
action\_result\.summary\.status | string | 
summary\.total\_objects | numeric | 
summary\.total\_objects\_successful | numeric |   

## action: 'list resource groups'
Get the list of resource groups for the subscription

Type: **investigate**  
Read only: **True**

#### Action Parameters
No parameters are required for this action

#### Action Output
DATA PATH | TYPE | CONTAINS
--------- | ---- | --------
action\_result\.data\.\*\.id | string | 
action\_result\.data\.\*\.location | string | 
action\_result\.data\.\*\.name | string |  `vm management resource group` 
action\_result\.data\.\*\.properties\.provisioningState | string | 
action\_result\.data\.\*\.tags\.company | string | 
action\_result\.data\.\*\.tags\.\{"keyname"\: "keyvalue"\} | string | 
action\_result\.status | string | 
action\_result\.message | string | 
action\_result\.summary\.num\_resource\_groups | numeric | 
summary\.total\_objects | numeric | 
summary\.total\_objects\_successful | numeric |   

## action: 'list snapshots'
Get the list of snapshots under the subscription

Type: **investigate**  
Read only: **True**

#### Action Parameters
PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**resource\_group\_name** |  optional  | The name of the resource group | string |  `vm management resource group` 

#### Action Output
DATA PATH | TYPE | CONTAINS
--------- | ---- | --------
action\_result\.parameter\.resource\_group\_name | string |  `vm management resource group` 
action\_result\.data\.\*\.id | string | 
action\_result\.data\.\*\.location | string | 
action\_result\.data\.\*\.name | string |  `vm management tag name` 
action\_result\.data\.\*\.properties\.creationData\.createOption | string | 
action\_result\.data\.\*\.properties\.creationData\.sourceResourceId | string | 
action\_result\.data\.\*\.properties\.creationData\.sourceUri | string | 
action\_result\.data\.\*\.properties\.diskSizeGB | numeric | 
action\_result\.data\.\*\.properties\.diskState | string | 
action\_result\.data\.\*\.properties\.osType | string | 
action\_result\.data\.\*\.properties\.provisioningState | string | 
action\_result\.data\.\*\.properties\.timeCreated | string | 
action\_result\.data\.\*\.sku\.name | string | 
action\_result\.data\.\*\.sku\.tier | string | 
action\_result\.data\.\*\.tags\.author | string | 
action\_result\.data\.\*\.tags\.type | string | 
action\_result\.data\.\*\.type | string | 
action\_result\.status | string | 
action\_result\.message | string | 
action\_result\.summary\.num\_snapshots | numeric | 
summary\.total\_objects | numeric | 
summary\.total\_objects\_successful | numeric |   

## action: 'list security groups'
Get the list of all security groups in a resource group

Type: **investigate**  
Read only: **True**

API limitation\: Network Security Group \(classic\) is not part of the response\.

#### Action Parameters
PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**resource\_group\_name** |  required  | The name of the resource group | string |  `vm management resource group` 
**group\_type** |  required  | Type of security group to query | string | 

#### Action Output
DATA PATH | TYPE | CONTAINS
--------- | ---- | --------
action\_result\.parameter\.group\_type | string | 
action\_result\.parameter\.resource\_group\_name | string |  `vm management resource group` 
action\_result\.data\.\*\.etag | string | 
action\_result\.data\.\*\.id | string | 
action\_result\.data\.\*\.location | string | 
action\_result\.data\.\*\.name | string |  `vm management group name` 
action\_result\.data\.\*\.properties\.defaultSecurityRules\.\*\.etag | string | 
action\_result\.data\.\*\.properties\.defaultSecurityRules\.\*\.id | string | 
action\_result\.data\.\*\.properties\.defaultSecurityRules\.\*\.name | string | 
action\_result\.data\.\*\.properties\.defaultSecurityRules\.\*\.properties\.access | string | 
action\_result\.data\.\*\.properties\.defaultSecurityRules\.\*\.properties\.description | string | 
action\_result\.data\.\*\.properties\.defaultSecurityRules\.\*\.properties\.destinationAddressPrefix | string | 
action\_result\.data\.\*\.properties\.defaultSecurityRules\.\*\.properties\.destinationPortRange | string | 
action\_result\.data\.\*\.properties\.defaultSecurityRules\.\*\.properties\.direction | string | 
action\_result\.data\.\*\.properties\.defaultSecurityRules\.\*\.properties\.priority | numeric | 
action\_result\.data\.\*\.properties\.defaultSecurityRules\.\*\.properties\.protocol | string | 
action\_result\.data\.\*\.properties\.defaultSecurityRules\.\*\.properties\.provisioningState | string | 
action\_result\.data\.\*\.properties\.defaultSecurityRules\.\*\.properties\.sourceAddressPrefix | string | 
action\_result\.data\.\*\.properties\.defaultSecurityRules\.\*\.properties\.sourcePortRange | string | 
action\_result\.data\.\*\.properties\.defaultSecurityRules\.\*\.type | string | 
action\_result\.data\.\*\.properties\.networkInterfaces\.\*\.id | string | 
action\_result\.data\.\*\.properties\.provisioningState | string | 
action\_result\.data\.\*\.properties\.resourceGuid | string | 
action\_result\.data\.\*\.properties\.securityRules\.\*\.id | string | 
action\_result\.data\.\*\.properties\.securityRules\.\*\.etag | string | 
action\_result\.data\.\*\.properties\.securityRules\.\*\.name | string | 
action\_result\.data\.\*\.properties\.securityRules\.\*\.type | string | 
action\_result\.data\.\*\.properties\.securityRules\.\*\.properties\.access | string | 
action\_result\.data\.\*\.properties\.securityRules\.\*\.properties\.priority | numeric | 
action\_result\.data\.\*\.properties\.securityRules\.\*\.properties\.protocol | string | 
action\_result\.data\.\*\.properties\.securityRules\.\*\.properties\.direction | string | 
action\_result\.data\.\*\.properties\.securityRules\.\*\.properties\.sourcePortRange | string | 
ction\_result\.data\.\*\.properties\.securityRules\.\*\.properties\.provisioningState | string | 
action\_result\.data\.\*\.properties\.securityRules\.\*\.properties\.sourceAddressPrefix | string | 
action\_result\.data\.\*\.properties\.securityRules\.\*\.properties\.destinationPortRange | string | 
action\_result\.data\.\*\.properties\.securityRules\.\*\.properties\.destinationAddressPrefix | string | 
action\_result\.data\.\*\.tags\.author | string | 
action\_result\.data\.\*\.type | string | 
action\_result\.status | string | 
action\_result\.message | string | 
action\_result\.summary\.num\_security\_groups | numeric | 
summary\.total\_objects | numeric | 
summary\.total\_objects\_successful | numeric |   

## action: 'add network group'
Add a network security group in a resource group

Type: **generic**  
Read only: **False**

The 'security\_rules' parameter accept JSON format value\. For non\-JSON values, the parameter values will be ignored\. Refer to <a href='https\://docs\.microsoft\.com/en\-us/rest/api/virtualnetwork/networksecuritygroups/createorupdate' target='\_blank'>API Docs</a> for more information on adding a network security group\.

#### Action Parameters
PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**resource\_group\_name** |  required  | The name of the resource group | string |  `vm management resource group` 
**group\_name** |  required  | Name of security group to add | string |  `vm management group name` 
**location** |  required  | Resource location | string | 
**tags** |  optional  | String object of resource tags | string | 
**default\_security\_rules** |  optional  | Comma separated list of default security rules for the network security group | string | 
**provisioning\_state** |  optional  | The provisioning state of the public IP resource | string | 
**resource\_guid** |  optional  | The resource GUID property of the network security group resource | string | 
**security\_rules** |  optional  | Comma separated list of security rules of the network security group | string | 

#### Action Output
DATA PATH | TYPE | CONTAINS
--------- | ---- | --------
action\_result\.parameter\.default\_security\_rules | string | 
action\_result\.parameter\.group\_name | string |  `vm management group name` 
action\_result\.parameter\.location | string | 
action\_result\.parameter\.provisioning\_state | string | 
action\_result\.parameter\.resource\_group\_name | string |  `vm management resource group` 
action\_result\.parameter\.resource\_guid | string | 
action\_result\.parameter\.security\_rules | string | 
action\_result\.parameter\.tags | string | 
action\_result\.data\.\*\.etag | string | 
action\_result\.data\.\*\.id | string | 
action\_result\.data\.\*\.location | string | 
action\_result\.data\.\*\.name | string | 
action\_result\.data\.\*\.properties\.defaultSecurityRules\.\*\.etag | string | 
action\_result\.data\.\*\.properties\.defaultSecurityRules\.\*\.id | string | 
action\_result\.data\.\*\.properties\.defaultSecurityRules\.\*\.name | string | 
action\_result\.data\.\*\.properties\.defaultSecurityRules\.\*\.properties\.access | string | 
action\_result\.data\.\*\.properties\.defaultSecurityRules\.\*\.properties\.description | string | 
action\_result\.data\.\*\.properties\.defaultSecurityRules\.\*\.properties\.destinationAddressPrefix | string | 
action\_result\.data\.\*\.properties\.defaultSecurityRules\.\*\.properties\.destinationPortRange | string | 
action\_result\.data\.\*\.properties\.defaultSecurityRules\.\*\.properties\.direction | string | 
action\_result\.data\.\*\.properties\.defaultSecurityRules\.\*\.properties\.priority | numeric | 
action\_result\.data\.\*\.properties\.defaultSecurityRules\.\*\.properties\.protocol | string | 
action\_result\.data\.\*\.properties\.defaultSecurityRules\.\*\.properties\.provisioningState | string | 
action\_result\.data\.\*\.properties\.defaultSecurityRules\.\*\.properties\.sourceAddressPrefix | string | 
action\_result\.data\.\*\.properties\.defaultSecurityRules\.\*\.properties\.sourcePortRange | string | 
action\_result\.data\.\*\.properties\.defaultSecurityRules\.\*\.type | string | 
action\_result\.data\.\*\.properties\.provisioningState | string | 
action\_result\.data\.\*\.properties\.resourceGuid | string | 
action\_result\.data\.\*\.tags\.author | string | 
action\_result\.data\.\*\.type | string | 
action\_result\.status | string | 
action\_result\.message | string | 
action\_result\.summary\.status | string | 
summary\.total\_objects | numeric | 
summary\.total\_objects\_successful | numeric |   

## action: 'add application group'
Add an application security groups in a resource group

Type: **generic**  
Read only: **False**

#### Action Parameters
PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**resource\_group\_name** |  required  | The name of the resource group | string |  `vm management resource group` 
**group\_name** |  required  | Name of security group to add | string |  `vm management group name` 
**location** |  required  | Resource location | string | 
**tags** |  optional  | String object of resource tags\. It should be in JSON format | string | 

#### Action Output
DATA PATH | TYPE | CONTAINS
--------- | ---- | --------
action\_result\.parameter\.group\_name | string |  `vm management group name` 
action\_result\.parameter\.location | string | 
action\_result\.parameter\.resource\_group\_name | string |  `vm management resource group` 
action\_result\.parameter\.tags | string | 
action\_result\.data\.\*\.etag | string | 
action\_result\.data\.\*\.id | string | 
action\_result\.data\.\*\.location | string | 
action\_result\.data\.\*\.name | string |  `vm management group name` 
action\_result\.data\.\*\.properties\.provisioningState | string | 
action\_result\.data\.\*\.tags\.author | string | 
action\_result\.data\.\*\.type | string | 
action\_result\.status | string | 
action\_result\.message | string | 
action\_result\.summary\.status | string | 
summary\.total\_objects | numeric | 
summary\.total\_objects\_successful | numeric |   

## action: 'list virtual networks'
Get the list of virtual networks

Type: **investigate**  
Read only: **True**

#### Action Parameters
PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**resource\_group\_name** |  optional  | The name of the resource group | string |  `vm management resource group` 

#### Action Output
DATA PATH | TYPE | CONTAINS
--------- | ---- | --------
action\_result\.parameter\.resource\_group\_name | string |  `vm management resource group` 
action\_result\.data\.\*\.etag | string | 
action\_result\.data\.\*\.id | string | 
action\_result\.data\.\*\.location | string | 
action\_result\.data\.\*\.name | string |  `vm management virtual network` 
action\_result\.data\.\*\.properties\.addressSpace\.addressPrefixes | string | 
action\_result\.data\.\*\.properties\.enableDdosProtection | boolean | 
action\_result\.data\.\*\.properties\.enableVmProtection | boolean | 
action\_result\.data\.\*\.properties\.provisioningState | string | 
action\_result\.data\.\*\.properties\.resourceGuid | string | 
action\_result\.data\.\*\.properties\.subnets\.\*\.etag | string | 
action\_result\.data\.\*\.properties\.subnets\.\*\.id | string | 
action\_result\.data\.\*\.properties\.subnets\.\*\.name | string | 
action\_result\.data\.\*\.properties\.subnets\.\*\.properties\.addressPrefix | string | 
action\_result\.data\.\*\.properties\.subnets\.\*\.properties\.ipConfigurations\.\*\.id | string | 
action\_result\.data\.\*\.properties\.subnets\.\*\.properties\.provisioningState | string | 
action\_result\.data\.\*\.properties\.subnets\.\*\.type | string | 
action\_result\.data\.\*\.tags\.author | string | 
action\_result\.data\.\*\.type | string | 
action\_result\.status | string | 
action\_result\.message | string | 
action\_result\.summary\.num\_virtual\_networks | numeric | 
summary\.total\_objects | numeric | 
summary\.total\_objects\_successful | numeric |   

## action: 'list subnets'
Get the list of subnets

Type: **investigate**  
Read only: **True**

#### Action Parameters
PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**resource\_group\_name** |  required  | The name of the resource group | string |  `vm management resource group` 
**virtual\_network\_name** |  required  | The name of the virtual network | string |  `vm management virtual network` 

#### Action Output
DATA PATH | TYPE | CONTAINS
--------- | ---- | --------
action\_result\.parameter\.resource\_group\_name | string |  `vm management resource group` 
action\_result\.parameter\.virtual\_network\_name | string |  `vm management virtual network` 
action\_result\.data\.\*\.etag | string | 
action\_result\.data\.\*\.id | string | 
action\_result\.data\.\*\.name | string | 
action\_result\.data\.\*\.properties\.addressPrefix | string | 
action\_result\.data\.\*\.properties\.ipConfigurations\.\*\.id | string | 
action\_result\.data\.\*\.properties\.provisioningState | string | 
action\_result\.data\.\*\.type | string | 
action\_result\.status | string | 
action\_result\.message | string | 
action\_result\.summary\.num\_subnets | numeric | 
summary\.total\_objects | numeric | 
summary\.total\_objects\_successful | numeric |   

## action: 'get ip availability'
Check if a private IP address is available for use

Type: **investigate**  
Read only: **True**

#### Action Parameters
PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**resource\_group\_name** |  required  | The name of the resource group | string |  `vm management resource group` 
**virtual\_network\_name** |  required  | The name of the virtual network | string |  `vm management virtual network` 
**ip\_address** |  required  | The private IP address to be verified | string |  `ip`  `ipv6` 

#### Action Output
DATA PATH | TYPE | CONTAINS
--------- | ---- | --------
action\_result\.parameter\.ip\_address | string |  `ip`  `ipv6` 
action\_result\.parameter\.resource\_group\_name | string |  `vm management resource group` 
action\_result\.parameter\.virtual\_network\_name | string |  `vm management virtual network` 
action\_result\.data\.\*\.availableAddress | string |  `ip`  `ipv6` 
action\_result\.summary\.available | boolean | 
action\_result\.status | string | 
action\_result\.message | string | 
action\_result\.summary\.num\_ips\_available | numeric | 
summary\.total\_objects | numeric | 
summary\.total\_objects\_successful | numeric |   

## action: 'generalize vm'
Set the state of the virtual machine to be generalized

Type: **generic**  
Read only: **False**

#### Action Parameters
PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**resource\_group\_name** |  required  | The name of the resource group | string |  `vm management resource group` 
**vm\_name** |  required  | The name of the virtual machine | string |  `vm management virtual machine` 

#### Action Output
DATA PATH | TYPE | CONTAINS
--------- | ---- | --------
action\_result\.parameter\.resource\_group\_name | string |  `vm management resource group` 
action\_result\.parameter\.vm\_name | string |  `vm management virtual machine` 
action\_result\.data | string | 
action\_result\.status | string | 
action\_result\.message | string | 
action\_result\.summary\.status | string | 
summary\.total\_objects | numeric | 
summary\.total\_objects\_successful | numeric |   

## action: 'redeploy vm'
Redeploy a virtual machine

Type: **generic**  
Read only: **False**

#### Action Parameters
PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**resource\_group\_name** |  required  | The name of the resource group | string |  `vm management resource group` 
**vm\_name** |  required  | The name of the virtual machine | string |  `vm management virtual machine` 

#### Action Output
DATA PATH | TYPE | CONTAINS
--------- | ---- | --------
action\_result\.parameter\.resource\_group\_name | string |  `vm management resource group` 
action\_result\.parameter\.vm\_name | string |  `vm management virtual machine` 
action\_result\.data | string | 
action\_result\.status | string | 
action\_result\.message | string | 
action\_result\.summary\.status | string | 
summary\.total\_objects | numeric | 
summary\.total\_objects\_successful | numeric |   

## action: 'run command'
Run a command on the virtual machine

Type: **generic**  
Read only: **False**

Run a command or a script in an Azure Windows or Linux VM\. Refer to <a href='https\://docs\.microsoft\.com/en\-us/rest/api/compute/virtual%20machines%20run%20commands/runcommand' target='\_blank'>API Docs</a> for more information\.

#### Action Parameters
PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**resource\_group\_name** |  required  | The name of the resource group | string |  `vm management resource group` 
**vm\_name** |  required  | The name of the virtual machine | string |  `vm management virtual machine` 
**command\_id** |  required  | The command to run against the VM | string |  `vm management command id` 
**script** |  optional  | The script to be executed\. When this value is given, the given script will override the default script of the command | string | 
**script\_parameters** |  optional  | The run command parameters | string | 

#### Action Output
DATA PATH | TYPE | CONTAINS
--------- | ---- | --------
action\_result\.parameter\.resource\_group\_name | string |  `vm management resource group` 
action\_result\.parameter\.vm\_name | string |  `vm management virtual machine` 
action\_result\.parameter\.command\_id | string |  `vm management command id` 
action\_result\.parameter\.script | string | 
action\_result\.parameter\.script\_parameters | string | 
action\_result\.data | string | 
action\_result\.data\.\*\.results\_url | string |  `vm management results url` 
action\_result\.data\.results\.\*\.code | string | 
action\_result\.data\.results\.\*\.level | string | 
action\_result\.data\.results\.\*\.message | string | 
action\_result\.data\.\*\.displayStatus | string | 
action\_result\.status | string | 
action\_result\.message | string | 
action\_result\.summary\.status | string | 
summary\.total\_objects | numeric | 
summary\.total\_objects\_successful | numeric |   

## action: 'get results'
Fetch the results of a previously executed run\_command action

Type: **generic**  
Read only: **True**

Commands in Azure can take up to 90 minutes to execute\. This allows you to retrieve results of previously executed actions\. Refer to <a href='https\://docs\.microsoft\.com/en\-us/azure/virtual\-machines/windows/run\-command' target='\_blank'>API Docs</a> for more information\.

#### Action Parameters
PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**results\_url** |  required  | The name of the resource group | string |  `vm management results url` 

#### Action Output
DATA PATH | TYPE | CONTAINS
--------- | ---- | --------
action\_result\.parameter\.results\_url | string |  `vm management results url` 
action\_result\.data | string | 
action\_result\.data\.results\_url | string | 
action\_result\.data\.results\.\*\.code | string | 
action\_result\.data\.results\.\*\.level | string | 
action\_result\.data\.results\.\*\.message | string | 
action\_result\.data\.\*\.displayStatus | string | 
action\_result\.status | string | 
action\_result\.message | string | 
action\_result\.summary\.status | string | 
summary\.total\_objects | numeric | 
summary\.total\_objects\_successful | numeric | 