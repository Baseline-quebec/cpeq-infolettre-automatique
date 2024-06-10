environment = "dev"

# Azure Resource Manager variables.
# See this Service Principal : https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationMenuBlade/~/Overview/appId/5d4b2afb-db8e-41af-9f75-643e05ac688b/isMSAApp~/false
ARM_CLIENT_ID       = "5d4b2afb-db8e-41af-9f75-643e05ac688b"
ARM_SUBSCRIPTION_ID = "04378d5e-acd4-4f37-9048-ab746c3e385d"
ARM_TENANT_ID       = "3c727278-0e10-4e9e-90f7-16c681aa16de"

# The following value should be put in a local.tfvars file when used for local development.
# This value should NEVER be committed to source control.
# If credentials leak, inform emile.turcotte@baseline.quebec.
# For programmatic use, the secret is stored in the following Key Vault and should be accessed through CI/CD only :
# https://portal.azure.com/#@baseline.quebec/resource/subscriptions/04378d5e-acd4-4f37-9048-ab746c3e385d/resourceGroups/Baseline-Core-Resources/providers/Microsoft.KeyVault/vaults/baselinecore/overview
ARM_CLIENT_SECRET = ""
