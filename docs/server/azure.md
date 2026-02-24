# Azure Container Apps Deployment

Deploy plyra-memory-server to Azure Container Apps.
Free tier available. Scales to zero when idle.

## Prerequisites

```bash
# Install Azure CLI
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
az login
az extension add --name containerapp --upgrade
```

## Deploy

```bash
# 1. Create resource group
az group create --name plyra-rg --location eastus

# 2. Create Container Apps environment
az containerapp env create \
  --name plyra-env \
  --resource-group plyra-rg \
  --location eastus

# 3. Create Azure File Share for persistent storage
az storage account create \
  --name plyrastorage \
  --resource-group plyra-rg \
  --sku Standard_LRS

az storage share create \
  --name plyra-data \
  --account-name plyrastorage

# 4. Deploy the container
az containerapp create \
  --name plyra-memory-server \
  --resource-group plyra-rg \
  --environment plyra-env \
  --image ghcr.io/plyraai/plyra-memory-server:latest \
  --target-port 7700 \
  --ingress external \
  --min-replicas 0 \
  --max-replicas 3 \
  --env-vars \
    PLYRA_ADMIN_API_KEY=secretref:admin-key \
    PLYRA_STORE_URL=/data/memory.db \
    PLYRA_VECTORS_URL=/data/memory.index \
    PLYRA_KEY_STORE_URL=/data/keys.db
```

## Get your URL

```bash
az containerapp show \
  --name plyra-memory-server \
  --resource-group plyra-rg \
  --query properties.configuration.ingress.fqdn \
  --output tsv
# → plyra-memory-server.eastus.azurecontainerapps.io
```

## Connect the library

```bash
export PLYRA_SERVER_URL=https://plyra-memory-server.eastus.azurecontainerapps.io
export PLYRA_API_KEY=plm_live_...
```

```python
from plyra_memory import Memory

async def test():
    async with Memory(agent_id="my-agent") as memory:
        await memory.remember("hello from Azure")
```

---

← [Server overview](index.md) · [Guides →](../guides/production.md)
