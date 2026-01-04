@description('Azure region for resources')
param location string

@description('Storage account name (must be globally unique)')
param storageAccountName string

@description('Storage account SKU')
@allowed(['Standard_LRS', 'Standard_GRS', 'Standard_RAGRS', 'Standard_ZRS', 'Premium_LRS'])
param skuName string = 'Standard_LRS'

@description('Enable hierarchical namespace (Data Lake Gen2)')
param enableHierarchicalNamespace bool = true

@description('Access tier')
@allowed(['Hot', 'Cool', 'Archive'])
param accessTier string = 'Hot'

@description('Enable lifecycle management policies')
param enableLifecycleManagement bool = true

@description('Days before moving to cool tier (0 = disabled)')
param coolTierDays int = 30

@description('Days before moving to archive tier (0 = disabled)')
param archiveTierDays int = 90

@description('Days before deletion (0 = disabled)')
param deleteDays int = 365

@description('Tags to apply to all resources')
param tags object = {}

// Storage Account with Data Lake Gen2
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageAccountName
  location: location
  kind: 'StorageV2'
  sku: {
    name: skuName
  }
  properties: {
    accessTier: accessTier
    supportsHttpsTrafficOnly: true
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
    allowSharedKeyAccess: true
    isHnsEnabled: enableHierarchicalNamespace
  }
  tags: tags
}

// Blob Service
resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-01-01' = {
  name: 'default'
  parent: storageAccount
  properties: {
    deleteRetentionPolicy: {
      enabled: true
      days: 7
    }
    containerDeleteRetentionPolicy: {
      enabled: true
      days: 7
    }
    changeFeed: {
      enabled: true
    }
    restorePolicy: {
      enabled: true
      days: 7
    }
  }
}

// Lifecycle Management Policy
resource lifecyclePolicy 'Microsoft.Storage/storageAccounts/managementPolicies@2023-01-01' = if enableLifecycleManagement {
  name: 'default'
  parent: storageAccount
  properties: {
    policy: {
      rules: [
        {
          enabled: true
          name: 'MoveToCool'
          type: 'Lifecycle'
          definition: {
            filters: {
              blobTypes: [
                'blockBlob'
              ]
            }
            actions: {
              baseBlob: {
                tierToCool: {
                  daysAfterModificationGreaterThan: coolTierDays
                }
              }
            }
          }
        }
        {
          enabled: archiveTierDays > 0
          name: 'MoveToArchive'
          type: 'Lifecycle'
          definition: {
            filters: {
              blobTypes: [
                'blockBlob'
              ]
            }
            actions: {
              baseBlob: {
                tierToArchive: {
                  daysAfterModificationGreaterThan: archiveTierDays
                }
              }
            }
          }
        }
        {
          enabled: deleteDays > 0
          name: 'DeleteOldBlobs'
          type: 'Lifecycle'
          definition: {
            filters: {
              blobTypes: [
                'blockBlob'
              ]
            }
            actions: {
              baseBlob: {
                delete: {
                  daysAfterModificationGreaterThan: deleteDays
                }
              }
            }
          }
        }
      ]
    }
  }
  dependsOn: [
    storageAccount
  ]
}

// Containers for data pipeline
var containers = [
  'raw-transcripts'
  'synthetic-outputs'
  'registry'
  'validation-results'
  'pipeline-logs'
]

resource dataContainers 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = [for container in containers: {
  name: container
  parent: blobService
  properties: {
    publicAccess: 'None'
    metadata: {}
  }
  dependsOn: [
    blobService
  ]
}]

output storageAccountId string = storageAccount.id
output storageAccountName string = storageAccount.name
output primaryEndpoints object = storageAccount.properties.primaryEndpoints
output primaryConnectionString string = 'DefaultEndpointsProtocol=https;AccountName=${storageAccount.name};AccountKey=${storageAccount.listKeys().keys[0].value};EndpointSuffix=${environment().suffixes.storage}'
output dfsEndpoint string = '${storageAccount.properties.primaryEndpoints.dfs}'

