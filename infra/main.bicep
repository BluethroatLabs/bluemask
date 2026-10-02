@description('Azure region for the storage account')
param location string = resourceGroup().location

@description('Name prefix for Azure resources')
param prefix string = 'bluemask'

@description('Create a dedicated Azure Front Door profile (opt-in; shared edge is managed separately)')
param deployFrontDoor bool = false

@description('Hostname Front Door serves in addition to its azurefd.net endpoint')
param customDomainHostName string = 'bluemask.bluethroatlabs.com'

var tags = {
  project: 'bluemask'
  environment: 'sandbox'
  managedBy: 'bluethroat'
  owner: 'wehi'
  costCenter: 'bluemask-experiments'
  purpose: 'bluemask-sandbox'
}

var storageName = take('st${prefix}${uniqueString(resourceGroup().id)}', 24)
var endpointName = take('${prefix}-${uniqueString(resourceGroup().id)}', 50)
var customDomainName = replace(customDomainHostName, '.', '-')
var staticHost = replace(replace(storage.properties.primaryEndpoints.web, 'https://', ''), '/', '')

resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: storageName
  location: location
  tags: tags
  kind: 'StorageV2'
  sku: {
    name: 'Standard_LRS'
  }
  properties: {
    allowBlobPublicAccess: true
    allowSharedKeyAccess: true
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    publicNetworkAccess: 'Enabled'
  }
}

resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2025-08-01' = {
  parent: storage
  name: 'default'
  properties: {
    staticWebsite: {
      enabled: true
      indexDocument: 'index.html'
    }
  }
}

resource profile 'Microsoft.Cdn/profiles@2021-06-01' = if (deployFrontDoor) {
  name: '${prefix}-fd'
  location: 'global'
  tags: tags
  sku: {
    name: 'Standard_AzureFrontDoor'
  }
}

resource endpoint 'Microsoft.Cdn/profiles/afdEndpoints@2021-06-01' = if (deployFrontDoor) {
  parent: profile
  name: endpointName
  location: 'global'
  properties: {
    enabledState: 'Enabled'
  }
}

resource originGroup 'Microsoft.Cdn/profiles/originGroups@2021-06-01' = if (deployFrontDoor) {
  parent: profile
  name: 'web'
  properties: {
    loadBalancingSettings: {
      sampleSize: 4
      successfulSamplesRequired: 3
      additionalLatencyInMilliseconds: 50
    }
    healthProbeSettings: {
      probePath: '/'
      probeRequestType: 'HEAD'
      probeProtocol: 'Https'
      probeIntervalInSeconds: 120
    }
  }
}

resource origin 'Microsoft.Cdn/profiles/originGroups/origins@2021-06-01' = if (deployFrontDoor) {
  parent: originGroup
  name: 'blob'
  properties: {
    hostName: staticHost
    originHostHeader: staticHost
    httpPort: 80
    httpsPort: 443
    priority: 1
    weight: 1000
    enabledState: 'Enabled'
  }
}

resource ruleSet 'Microsoft.Cdn/profiles/ruleSets@2021-06-01' = if (deployFrontDoor) {
  parent: profile
  name: 'security'
}

resource headersRule 'Microsoft.Cdn/profiles/ruleSets/rules@2021-06-01' = if (deployFrontDoor) {
  parent: ruleSet
  name: 'headers'
  properties: {
    order: 1
    matchProcessingBehavior: 'Continue'
    conditions: []
    actions: [
      {
        name: 'ModifyResponseHeader'
        parameters: {
          typeName: 'DeliveryRuleHeaderActionParameters'
          headerAction: 'Overwrite'
          headerName: 'Referrer-Policy'
          value: 'no-referrer'
        }
      }
      {
        name: 'ModifyResponseHeader'
        parameters: {
          typeName: 'DeliveryRuleHeaderActionParameters'
          headerAction: 'Overwrite'
          headerName: 'X-Content-Type-Options'
          value: 'nosniff'
        }
      }
      {
        name: 'ModifyResponseHeader'
        parameters: {
          typeName: 'DeliveryRuleHeaderActionParameters'
          headerAction: 'Overwrite'
          headerName: 'X-Frame-Options'
          value: 'DENY'
        }
      }
      {
        name: 'ModifyResponseHeader'
        parameters: {
          typeName: 'DeliveryRuleHeaderActionParameters'
          headerAction: 'Overwrite'
          headerName: 'Permissions-Policy'
          value: 'camera=(), microphone=(), geolocation=()'
        }
      }
      {
        name: 'ModifyResponseHeader'
        parameters: {
          typeName: 'DeliveryRuleHeaderActionParameters'
          headerAction: 'Overwrite'
          headerName: 'Content-Security-Policy'
          value: 'frame-ancestors \'none\''
        }
      }
    ]
  }
}

resource offlineHeadersRule 'Microsoft.Cdn/profiles/ruleSets/rules@2021-06-01' = if (deployFrontDoor) {
  parent: ruleSet
  name: 'offline-download-headers'
  properties: {
    order: 2
    matchProcessingBehavior: 'Continue'
    conditions: [
      {
        name: 'UrlPath'
        parameters: {
          typeName: 'DeliveryRuleUrlPathMatchConditionParameters'
          operator: 'Equal'
          negateCondition: false
          matchValues: [
            '/BlueMask.html'
          ]
          transforms: []
        }
      }
    ]
    actions: [
      {
        name: 'ModifyResponseHeader'
        parameters: {
          typeName: 'DeliveryRuleHeaderActionParameters'
          headerAction: 'Overwrite'
          headerName: 'X-Robots-Tag'
          value: 'noindex'
        }
      }
      {
        name: 'ModifyResponseHeader'
        parameters: {
          typeName: 'DeliveryRuleHeaderActionParameters'
          headerAction: 'Overwrite'
          headerName: 'Content-Disposition'
          value: 'attachment; filename="BlueMask.html"'
        }
      }
    ]
  }
}

var legacyRedirects = [
  { name: 'redirect-privacy-html', source: '/privacy.html', target: '/privacy' }
  { name: 'redirect-terms-html', source: '/terms.html', target: '/terms' }
  { name: 'redirect-support-html', source: '/support.html', target: '/support' }
]

resource legacyRedirectRules 'Microsoft.Cdn/profiles/ruleSets/rules@2021-06-01' = [for (item, i) in (deployFrontDoor ? legacyRedirects : []): {
  parent: ruleSet
  name: item.name
  properties: {
    order: 3 + i
    matchProcessingBehavior: 'Stop'
    conditions: [
      {
        name: 'UrlPath'
        parameters: {
          typeName: 'DeliveryRuleUrlPathMatchConditionParameters'
          operator: 'Equal'
          negateCondition: false
          matchValues: [
            item.source
          ]
          transforms: []
        }
      }
    ]
    actions: [
      {
        name: 'UrlRedirect'
        parameters: {
          typeName: 'DeliveryRuleUrlRedirectActionParameters'
          redirectType: 'Moved'
          destinationProtocol: 'Https'
          customPath: item.target
        }
      }
    ]
  }
}]

resource customDomain 'Microsoft.Cdn/profiles/customDomains@2023-05-01' = if (deployFrontDoor) {
  parent: profile
  name: customDomainName
  properties: {
    hostName: customDomainHostName
    tlsSettings: {
      certificateType: 'ManagedCertificate'
      minimumTlsVersion: 'TLS12'
    }
  }
}

resource route 'Microsoft.Cdn/profiles/afdEndpoints/routes@2021-06-01' = if (deployFrontDoor) {
  parent: endpoint
  name: 'web'
  dependsOn: [
    origin
    headersRule
    offlineHeadersRule
    legacyRedirectRules
  ]
  properties: {
    originGroup: {
      id: originGroup.id
    }
    supportedProtocols: [
      'Http'
      'Https'
    ]
    patternsToMatch: [
      '/*'
    ]
    forwardingProtocol: 'HttpsOnly'
    httpsRedirect: 'Enabled'
    linkToDefaultDomain: 'Enabled'
    enabledState: 'Enabled'
    cacheConfiguration: {
      queryStringCachingBehavior: 'IgnoreQueryString'
      compressionSettings: {
        isCompressionEnabled: true
        contentTypesToCompress: [
          'text/html'
          'text/css'
          'text/javascript'
          'application/javascript'
          'application/json'
          'application/manifest+json'
          'application/xml'
          'text/plain'
          'image/svg+xml'
        ]
      }
    }
    customDomains: [
      {
        id: customDomain.id
      }
    ]
    ruleSets: [
      {
        id: ruleSet.id
      }
    ]
  }
}

output storageAccountName string = storage.name
output staticWebsiteHostName string = staticHost
output staticWebsiteUrl string = storage.properties.primaryEndpoints.web
output frontDoorHostName string = deployFrontDoor ? endpoint!.properties.hostName : ''
output frontDoorUrl string = deployFrontDoor ? 'https://${endpoint!.properties.hostName}/' : ''
