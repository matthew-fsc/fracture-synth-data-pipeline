@description('Azure region for resources')
param location string = resourceGroup().location

@description('Environment name (dev, staging, prod)')
@allowed(['dev', 'staging', 'prod'])
param environment string = 'dev'

@description('Project name prefix')
param projectName string = 'synth-data'

@description('Tags to apply to all resources')
param tags object = {
  Environment: environment
  Project: 'synthetic-data-pipeline'
  ManagedBy: 'Bicep'
}

// Generate resource names
var storageAccountName = '${projectName}${environment}${uniqueString(resourceGroup().id)}'
var keyVaultName = '${projectName}-kv-${environment}-${uniqueString(resourceGroup().id)}'
var appInsightsName = '${projectName}-ai-${environment}'
var logAnalyticsName = '${projectName}-la-${environment}'

// Key Vault (assumes it exists or is created elsewhere)
// For now, we'll just reference it
var keyVaultId = resourceId('Microsoft.KeyVault/vaults', keyVaultName)

// Log Analytics Workspace
module logAnalytics 'modules/loganalytics.bicep' = {
  name: 'logAnalytics'
  params: {
    location: location
    workspaceName: logAnalyticsName
    retentionInDays: environment == 'prod' ? 365 : 90
    tags: tags
  }
}

// Application Insights
module appInsights 'modules/appinsights.bicep' = {
  name: 'appInsights'
  params: {
    location: location
    workspaceName: appInsightsName
    logAnalyticsWorkspaceId: logAnalytics.outputs.workspaceResourceId
    retentionInDays: environment == 'prod' ? 365 : 90
    tags: tags
  }
}

// Storage Account (Data Lake Gen2)
module storage 'modules/storage.bicep' = {
  name: 'storage'
  params: {
    location: location
    storageAccountName: storageAccountName
    skuName: environment == 'prod' ? 'Standard_GRS' : 'Standard_LRS'
    enableHierarchicalNamespace: true
    accessTier: 'Hot'
    enableLifecycleManagement: true
    coolTierDays: environment == 'prod' ? 30 : 0
    archiveTierDays: environment == 'prod' ? 90 : 0
    deleteDays: environment == 'prod' ? 365 : 0
    tags: tags
  }
}

output storageAccountName string = storage.outputs.storageAccountName
output storageAccountId string = storage.outputs.storageAccountId
output storageConnectionString string = storage.outputs.primaryConnectionString
output dfsEndpoint string = storage.outputs.dfsEndpoint
output appInsightsInstrumentationKey string = appInsights.outputs.instrumentationKey
output appInsightsConnectionString string = appInsights.outputs.connectionString
output appInsightsAppId string = appInsights.outputs.appId
output logAnalyticsWorkspaceId string = logAnalytics.outputs.workspaceResourceId

