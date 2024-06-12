# CPEQ Infrastructure-as-Code Setup
In this documentation we describe the current Terraform setup.

## Terraform backend setup
In order to properly function, Terraform uses [a state file](https://developer.hashicorp.com/terraform/language/state) in which it persists the current state of the deployed infrastructure.

This state file contains critical data in clear text : if it is lost, destroyed or corrupted, Terraform goes blind and has no way of interacting with our current infrastructure; if it leaks, this data can be used to compromise our infrastructure. It must then be safely stored somewhere, encrypted in transit and at rest, versionned and replicated to mitigate those risks.

The place where Terraform stores its state file is called the [_backend_](https://developer.hashicorp.com/terraform/language/settings/backends/configuration). When not specified, it stores the file locally, but we need to store it in the Cloud to enable different Terraform processes to access the same state file.

This is why we configure [the AzureRM backend](https://developer.hashicorp.com/terraform/language/settings/backends/azurerm). This means the Terraform state is stored inside a Storage Account in Azure. The Storage Account in question is to be found [here](https://portal.azure.com/#@baseline.quebec/resource/subscriptions/04378d5e-acd4-4f37-9048-ab746c3e385d/resourceGroups/Baseline-Core-Resources/providers/Microsoft.Storage/storageAccounts/baseline0terraform/overview).

## Cloud Providers configuration

### Azure Resource Manager ([azurerm](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs))

The most secure way to authenticate with Azure is through the OIDC workflow, which has been setup following this [documentation](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/guides/service_principal_oidc#configure-azure-active-directory-application-to-trust-a-github-repository)).

This makes it so that no secret has to be stored on our side. The only values which need to be set in the Pipeline environment are the following :

ARM_CLIENT_ID : The Client ID of the Service Principal used to identify the Terraform process with Azure.
ARM_TENANT_ID : The ID of the Tenant (i.e. Microsoft Entra ID) in which the Service Principal is contained.
ARM_SUBSCRIPTION_ID : The ID of the Azure subscription where the Terraform will deploy resources.

Those values are currently stored as Github repository secrets. In the [pipeline](../.github/workflows/terraform.yml), we obtain those values and map them to environment variables which are automatically looked up by the AzureRM Terraform provider. This is why we don't see any provider configuration inside the Terraform code.

