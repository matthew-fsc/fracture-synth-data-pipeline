@description('Azure region for resources')
param location string

@description('Log Analytics workspace name')
param workspaceName string

@description('Retention period in days (30-730 days, or -1 for unlimited)')
@allowed([30, 31, 60, 90, 120, 180, 365, 730, -1])
param retentionInDays int = 90

@description('Enable data export to Storage Account for long-term archive')
param enableDataExport bool = false

@description('Storage Account resource ID for data export (required if enableDataExport is true)')
param storageAccountId string = ''

@description('Tags to apply to all resources')
param tags object = {}

// Log Analytics Workspace
resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: workspaceName
  location: location
  tags: tags
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: retentionInDays
    features: {
      enableLogAccessUsingOnlyResourcePermissions: true
    }
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
}

// Data Export Rule for long-term archive (if enabled)
resource dataExportRule 'Microsoft.OperationalInsights/workspaces/dataExports@2020-08-01' = if enableDataExport && storageAccountId != '' {
  name: '${workspaceName}-export'
  parent: logAnalyticsWorkspace
  properties: {
    destination: {
      resourceId: storageAccountId
      metaData: {
        eventHubName: ''
      }
      type: 'StorageAccount'
    }
    tableNames: [
      'Usage'
      'AzureActivity'
      'AzureMetrics'
      'Heartbeat'
      'Perf'
      'SecurityEvent'
      'WindowsEvent'
      'Syslog'
      'FunctionAppLogs'
      'AppTraces'
      'AppExceptions'
      'AppDependencies'
      'AppRequests'
      'AppPageViews'
      'AppBrowserTimings'
      'AppPerformanceCounters'
    ]
    enable: true
  }
  dependsOn: [
    logAnalyticsWorkspace
  ]
}

output workspaceId string = logAnalyticsWorkspace.id
output workspaceName string = logAnalyticsWorkspace.name
output workspaceCustomerId string = logAnalyticsWorkspace.properties.customerId
output workspaceResourceId string = logAnalyticsWorkspace.id
