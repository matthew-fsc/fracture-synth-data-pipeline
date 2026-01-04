@description('Azure region for resources')
param location string

@description('Application Insights workspace name')
param workspaceName string

@description('Log Analytics workspace resource ID (optional, will create new if not provided)')
param logAnalyticsWorkspaceId string = ''

@description('Retention period in days (30-730)')
@allowed([30, 31, 60, 90, 120, 180, 365, 730])
param retentionInDays int = 90

@description('Tags to apply to all resources')
param tags object = {}

// Application Insights Component
resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: workspaceName
  location: location
  kind: 'web'
  tags: tags
  properties: {
    Application_Type: 'web'
    IngestionMode: 'ApplicationInsights'
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
    RetentionInDays: retentionInDays
    WorkspaceResourceId: logAnalyticsWorkspaceId != '' ? logAnalyticsWorkspaceId : ''
  }
}

output instrumentationKey string = appInsights.properties.InstrumentationKey
output connectionString string = appInsights.properties.ConnectionString
output appId string = appInsights.properties.AppId
output workspaceId string = appInsights.id

