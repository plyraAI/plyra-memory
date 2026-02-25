# Azure Container Apps Deployment

The public plyra-memory-server runs at:

```
https://plyra-memory-server.politedesert-a99b9eaf.centralindia.azurecontainerapps.io
```

Get a key at [plyra-keys.vercel.app](https://plyra-keys.vercel.app).

## Self-host on Azure

To run your own instance:

### Prerequisites

```bash
az extension add --name containerapp --upgrade
az login
```

### Deploy

```bash
RESOURCE_GROUP="plyra-rg"
LOCATION="centralindia"

# Resource group
az group create --name $RESOURCE_GROUP --location $LOCATION

# Container Apps environment
az containerapp env create \
  --name plyra-env \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION

# Persistent storage
az storage account create \
  --name plyrastorage \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku Standard_LRS

STORAGE_KEY=$(az storage account keys list \
  --resource-group $RESOURCE_GROUP \
  --account-name plyrastorage \
  --query "[0].value" -o tsv)

az storage share create \
  --name plyra-data \
  --account-name plyrastorage \
  --account-key $STORAGE_KEY

# Deploy container with secrets
az containerapp create \
  --name plyra-memory-server \
  --resource-group $RESOURCE_GROUP \
  --environment plyra-env \
  --image ghcr.io/plyraai/plyra-memory-server:latest \
  --target-port 7700 \
  --ingress external \
  --min-replicas 0 \
  --max-replicas 3 \
  --secrets \
    admin-key="your_admin_key" \
    groq-key="your_groq_key" \
  --env-vars \
    PLYRA_ADMIN_API_KEY=secretref:admin-key \
    GROQ_API_KEY=secretref:groq-key \
    PLYRA_STORE_URL="/data/memory.db" \
    PLYRA_ENV="production"
```

### Get your URL

```bash
az containerapp show \
  --name plyra-memory-server \
  --resource-group plyra-rg \
  --query "properties.configuration.ingress.fqdn" \
  --output tsv
```

→ [Full server docs](https://plyraai.github.io/plyra-memory-server)

← [Connect to server](quickstart.md) · [Guides](../guides/production.md) →
