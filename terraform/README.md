# Azure VM Start/Stop – Terraform + Azure Functions Flex Consumption

This project provisions two Ubuntu VMs and the Azure Functions infrastructure in one Azure subscription and South India. A Python Timer Trigger Function starts and deallocates only VMs with matching tags in the configured target resource group.

## Important prerequisites

- Terraform CLI (the user's existing 1.15.x line is suitable; configuration requires >= 1.5).
- Azure CLI.
- AzureRM provider 4.73.x.
- Python 3.11.
- Azure Functions Core Tools v4 for optional local testing.
- Azure subscription permissions to create resources and role assignments.
- South India must be available for Flex Consumption in the target subscription. Check before apply:
  `az functionapp list-flexconsumption-locations -o table`
- Check the chosen VM SKU is available and quota exists in South India.

## 1. SSH key

On Windows PowerShell:

```powershell
ssh-keygen -t rsa -b 4096 -C "azure-terraform"
## Run below commands in powershell 
PS C:\Users\Gautam>
ssh-keygen -t rsa -b 4096 -C "$HOME\.ssh\vm-automation"
Get-Content $env:USERPROFILE\.ssh\id_rsa.pub
```

Use the contents of the `.pub` file as `admin_ssh_public_key`. Keep the private key private.

Find your public IP and supply it as a single-host CIDR such as `198.51.100.25/32`. Do not open SSH to the entire internet.

## Update the SSH source CIDR

In the selected environment's `terraform.tfvars`, replace `203.0.113.10/32` with your trusted public egress IP in CIDR notation, for example `198.51.100.25/32`.

The sample address is a documentation-only placeholder and will not permit your real connection. Do not use `0.0.0.0/0` for SSH.

The VM has **no public IP address**. The NSG rule is an additional network restriction, not an Internet access method. Reach the VM through an approved private path such as Azure Bastion, site-to-site VPN, ExpressRoute, or a peered management network. This sample does not deploy Bastion or VPN.

Your trusted IP is the public IP address from which your internet connection accesses Azure.
You can find it using PowerShell.
Step 1: Find your public IP
Run this command:
(Invoke-RestMethod -Uri "https://api.ipify.org")
It will return an IP address, for example:
Step 2: Convert it into CIDR notation
Add /32 to the IP address.

For example:
source_address_prefix = "49.207.125.100/32"
/32 means only that specific IPv4 address is allowed.
Step 3: Update your Terraform file
Open:
environments/dev/terraform.tfvars
find 
source_address_prefix = "203.0.113.10/32"
Replace it with your actual public IP and /32

Important for your Azure project
Your VM currently has no public IP address. Therefore, this NSG rule alone will not allow you to SSH into the VM over the internet.

You need Azure Bastion, VPN, or another approved private connectivity path.

One more recommendation: If you are using a broadband connection with a dynamic public IP, it may change. Recheck it before deployment if necessary.

## 2. Sign in and check region

```powershell
az login
az account list -o table
az account set --subscription "<SUBSCRIPTION-ID>"
az account show -o table
az functionapp list-flexconsumption-locations -o table
```

If South India is not listed for Flex Consumption in your subscription, stop and choose a listed region or a different hosting plan. Do not assume region availability.

## 3. Configure Terraform

```powershell
cd terraform
Copy-Item terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` with:
- Your subscription GUID.
- Your SSH public key.
- Your public IP CIDR.
- Any desired VM names or size.

The sample uses two Ubuntu 22.04 VMs, `Standard_B2s`, with public IPs and SSH restricted by NSG to `admin_source_cidr`. Confirm the VM size is offered in South India and your subscription has quota. For production, consider private access through Bastion/VPN instead of public IPs.

## 3a Update terraform/rbac.tf
# Grant Azure DevOps Service Principal permission to deploy
# applications to the Azure Function App.

resource "azurerm_role_assignment" "ado_function_app_website_contributor" {
  scope                = var.function_app_resource_id
  role_definition_name = "Website Contributor"
  principal_id         = var.ado_service_principal_object_id
  principal_type       = "ServicePrincipal"

  skip_service_principal_aad_check = true
}
# Update terraform/variables.tf 
Add these variables:
variable "ado_service_principal_object_id" {
  description = "Object ID of the Azure DevOps service principal"
  type        = string
}

variable "function_app_resource_id" {
  description = "Resource ID of the Azure Function App"
  type        = string
}

# Update your terraform.tfvars
ado_service_principal_object_id = "9492ff78-a34c-4c70-b2ca-03843427ec6d"

function_app_resource_id = "/subscriptions/cd6208f9-14cc-4d2d-a201-43ec9eeda060/resourceGroups/rg-vm-automation/providers/Microsoft.Web/sites/func-vm-auto-i3mo0bv"

# The object ID above is the service principal's Object ID, not its Application (Client) ID.

You can also retrieve the Function App resource ID using: Change the function app name as given your terraform build.
az functionapp show `
  --name "func-vm-auto-i3mo0bv" `
  --resource-group "rg-vm-automation" `
  --query id `
  --output tsv

## 4. Initialize, plan and apply

```powershell
terraform init
terraform fmt -recursive
terraform validate
terraform plan -out main.tfplan
terraform apply main.tfplan
```

Terraform creates:
- Two resource groups.
- VNet, subnet, NSG, public IPs and NICs.
- Two tagged Ubuntu VMs.
- Storage account and private deployment container.
- Log Analytics and Application Insights.
- Flex Consumption plan and Function App.
- System-assigned Function App Managed Identity.
- RBAC assignments for VM operations and identity-based Function storage.

The identity creating these resources needs permission to create role assignments, such as Owner, User Access Administrator, or Role Based Access Control Administrator at the relevant scope. Contributor alone is insufficient for RBAC role assignment creation.

## 5. Verify outputs

```powershell
terraform output
```

Record `function_app_name`, `function_resource_group`, `vm_resource_group`, `function_app_principal_id` and VM public IPs.

## 6. Managed Identity and RBAC

Terraform enables the Function App system-assigned identity and assigns:
- Virtual Machine Contributor at the VM resource group scope.
- Storage Blob Data Owner on the Function storage account.
- Storage Queue Data Contributor on the Function storage account.
- Storage Table Data Contributor on the Function storage account.

The Storage data roles support identity-based host/deployment storage. The app's `AzureWebJobsStorage` setting is intentionally empty, and `AzureWebJobsStorage__accountName` selects the storage account for identity-based host storage. The deployment storage uses `SystemAssignedIdentity`.

Allow RBAC propagation time after initial creation.

## 7. Review the Function App settings

Terraform configures:
- `TARGET_RESOURCE_GROUP`
- `TARGET_ENVIRONMENT=dev`
- `DRY_RUN=true`
- `ALLOW_PROD_AUTOMATION=false`
- Start schedule `0 30 2 * * *` (08:00 IST)
- Deallocate schedule `0 30 14 * * *` (20:00 IST)

Keep `DRY_RUN=true` until logs confirm the exact target VM list.

## 8. Deploy Function code

Copy the root `function-app` files into your Azure Repos project with the pipeline and tests. Update `azure-pipelines.yml`:
- `azureServiceConnection` to your Azure Resource Manager service connection.
- `functionAppName` to the `terraform output -raw function_app_name` value.
- `functionResourceGroup` if you changed it.

The service connection deploys code; it is distinct from the Function App managed identity. It needs permission to deploy the Function App. The pipeline uses Azure CLI package deployment with remote build because Python Flex Consumption deployments should use remote build to install Linux-compatible dependencies.

Create an Azure DevOps environment named `vm-automation-dev`, then create a pipeline from `azure-pipelines.yml`. Add approvals for QA/Production if extending this project.

## 9. Test safely

1. Confirm the VMs have `Environment=Dev` and `AutoSchedule=true` tags (Terraform applies these).
2. Keep `DRY_RUN=true`.
3. Deploy code and inspect Function App / Application Insights traces.
4. Confirm only the intended two VMs are selected.
5. Test one VM manually in a controlled maintenance window.
6. After approval, change `DRY_RUN=false` in Function App configuration.
7. Validate VM instance view after start and deallocation.
8. Restore the intended schedules after any accelerated testing.

## 10. Operational and security notes

- The Function App is in its own resource group; it can manage only VMs in the target resource group because the VM role assignment is scoped there.
- `Virtual Machine Contributor` is broader than the exact operations required. For stricter production least privilege, define and test a custom role limited to VM read, instance view, start and deallocate operations.
- Do not use production tags with this development Function App. The code blocks production unless an explicit setting is enabled, but production should have its own Function App, identity, role assignment, approval process and resource group.
- The VMs have public IPs only to make SSH lab access possible; the NSG restricts SSH to your CIDR. For production, use Azure Bastion or private connectivity and remove public IPs.
- Deallocation releases compute allocation, but disks, networking and other associated resources can still incur charges.
- Terraform local state can contain sensitive infrastructure metadata. For team/production use, configure a remote Azure Storage backend with locking, restricted access, encryption and state recovery.
- Flex Consumption region support is subscription/region dependent. Confirm South India with the CLI before applying.
- Large VM fleets need batching, retry/backoff, partial-failure handling and execution-time planning.
- Review application shutdown behaviour and workload dependencies before deallocating machines.

## 11. Destroy lab resources

Only after confirming the resources are disposable:

```powershell
terraform plan -destroy -out destroy.tfplan
terraform apply destroy.tfplan
```

This destroys the VMs and all Terraform-managed resources in both resource groups. Back up anything you need first.
