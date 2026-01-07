# Azure Container Apps Deployment Guide

## Prerequisites

✅ Docker Desktop running
✅ Azure CLI installed: `az --version`
✅ Docker Hub account (or Azure Container Registry)
✅ Azure subscription

## Step 1: Test Locally

First, make sure everything works locally:

```powershell
# Build and start all services
docker-compose -f docker-compose.microservices.yml up --build

# Test endpoints
# Frontend: http://localhost:80
# API: http://localhost:80/api/v1/ppt/health
# Redis: localhost:6379
```

**What to verify:**
- ✅ Frontend loads
- ✅ API responds
- ✅ Can create presentations
- ✅ Check logs for errors

Stop with `Ctrl+C` when done testing.

## Step 2: Build & Push Images to Docker Hub

```powershell
# Login to Docker Hub
docker login

# Build images with your Docker Hub username
docker build -f Dockerfile.api -t krvatsal/medhavii-api:latest .
docker build -f Dockerfile.manim-worker -t krvatsal/medhavii-manim-worker:latest .
docker build -f Dockerfile.frontend -t krvatsal/medhavii-frontend:latest .

# Push to Docker Hub
docker push krvatsal/medhavii-api:latest
docker push krvatsal/medhavii-manim-worker:latest
docker push krvatsal/medhavii-frontend:latest
```

## Step 3: Login to Azure

```powershell
# Login
az login

# Set subscription (if you have multiple)
az account set --subscription "Your Subscription Name"

# Verify
az account show
```

## Step 4: Create Azure Resources

### Create Resource Group
```powershell
az group create `
  --name medhavii-rg `
  --location eastus
```

### Create Container Apps Environment
```powershell
az containerapp env create `
  --name medhavii-env `
  --resource-group medhavii-rg `
  --location eastus
```

### Create Azure Cache for Redis (IMPORTANT!)
```powershell
# Basic tier - cheapest option (~$15/month)
az redis create `
  --name medhavii-redis `
  --resource-group medhavii-rg `
  --location eastus `
  --sku Basic `
  --vm-size c0

# Get connection string (save this!)
az redis list-keys --name medhavii-redis --resource-group medhavii-rg
```

**Note the output:**
```
primaryKey: <YOUR_REDIS_KEY>
```

Your Redis URL will be:
```
redis://:YOUR_REDIS_KEY@medhavii-redis.redis.cache.windows.net:6380?ssl=True
```

## Step 5: Deploy Container Apps

### 1. Deploy API Service

```powershell
az containerapp create `
  --name medhavii-api `
  --resource-group medhavii-rg `
  --environment medhavii-env `
  --image krvatsal/medhavii-api:latest `
  --target-port 8000 `
  --ingress external `
  --min-replicas 1 `
  --max-replicas 5 `
  --cpu 1.0 `
  --memory 2.0Gi `
  --env-vars `
    "DATABASE_URL=<YOUR_POSTGRES_URL>" `
    "REDIS_URL=redis://:YOUR_REDIS_KEY@medhavii-redis.redis.cache.windows.net:6380?ssl=True" `
    "JWT_SECRET_KEY=<YOUR_JWT_SECRET>" `
    "GOOGLE_API_KEY=<YOUR_GOOGLE_KEY>" `
    "GROQ_API_KEY=<YOUR_GROQ_KEY>" `
    "PEXELS_API_KEY=<YOUR_PEXELS_KEY>" `
    "PIXABAY_API_KEY=<YOUR_PIXABAY_KEY>" `
    "AZURE_SPEECH_KEY=<YOUR_AZURE_SPEECH_KEY>" `
    "AZURE_REGION=eastus" `
    "ELEVENLABS_API_KEY_1=<YOUR_KEY1>" `
    "ELEVENLABS_API_KEY_2=<YOUR_KEY2>" `
    "ELEVENLABS_API_KEY_3=<YOUR_KEY3>" `
    "ELEVENLABS_API_KEY_4=<YOUR_KEY4>" `
    "BHASHINI_API_KEY=<YOUR_BHASHINI_KEY>" `
    "BHASHINI_USER_ID=<YOUR_BHASHINI_USER>" `
    "BHASHINI_UDYAT_KEY=<YOUR_BHASHINI_UDYAT>" `
    "APP_DATA_DIRECTORY=/app_data"
```

### 2. Deploy Manim Worker

```powershell
az containerapp create `
  --name medhavii-manim-worker `
  --resource-group medhavii-rg `
  --environment medhavii-env `
  --image krvatsal/medhavii-manim-worker:latest `
  --ingress internal `
  --min-replicas 1 `
  --max-replicas 5 `
  --cpu 2.0 `
  --memory 4.0Gi `
  --env-vars `
    "REDIS_URL=redis://:YOUR_REDIS_KEY@medhavii-redis.redis.cache.windows.net:6380?ssl=True" `
    "DATABASE_URL=<YOUR_POSTGRES_URL>" `
    "MANIM_SERVER_PATH=/opt/manim-mcp-server/src/manim_server.py" `
    "MANIM_EXECUTABLE=/usr/local/bin/manim" `
    "MANIM_MEDIA_DIR=/opt/manim-mcp-server/src/media"
```

### 3. Deploy Frontend

```powershell
az containerapp create `
  --name medhavii-frontend `
  --resource-group medhavii-rg `
  --environment medhavii-env `
  --image krvatsal/medhavii-frontend:latest `
  --target-port 3000 `
  --ingress external `
  --min-replicas 1 `
  --max-replicas 3 `
  --cpu 0.5 `
  --memory 1.0Gi `
  --env-vars `
    "NEXT_PUBLIC_API_URL=https://medhavii-api.<YOUR_ENV_DOMAIN>" `
    "NODE_ENV=production"
```

## Step 6: Get Your App URLs

```powershell
# Get API URL
az containerapp show `
  --name medhavii-api `
  --resource-group medhavii-rg `
  --query properties.configuration.ingress.fqdn `
  --output tsv

# Get Frontend URL
az containerapp show `
  --name medhavii-frontend `
  --resource-group medhavii-rg `
  --query properties.configuration.ingress.fqdn `
  --output tsv
```

## Step 7: Update Frontend with API URL

After getting the API URL, update the frontend:

```powershell
# Get the API URL from previous step
$API_URL = "https://medhavii-api.XXXXXXXXXXX.eastus.azurecontainerapps.io"

# Update frontend with correct API URL
az containerapp update `
  --name medhavii-frontend `
  --resource-group medhavii-rg `
  --set-env-vars "NEXT_PUBLIC_API_URL=$API_URL"
```

## Step 8: Verify Deployment

```powershell
# Check API health
curl https://medhavii-api.XXXXXXXXXXX.eastus.azurecontainerapps.io/api/v1/ppt/health

# View logs
az containerapp logs show `
  --name medhavii-api `
  --resource-group medhavii-rg `
  --follow

# Check worker logs
az containerapp logs show `
  --name medhavii-manim-worker `
  --resource-group medhavii-rg `
  --follow
```

## Step 9: Scale Configuration (Optional)

### Auto-scale based on HTTP requests (API)
```powershell
az containerapp update `
  --name medhavii-api `
  --resource-group medhavii-rg `
  --min-replicas 1 `
  --max-replicas 10 `
  --scale-rule-name http-requests `
  --scale-rule-type http `
  --scale-rule-http-concurrency 50
```

### Auto-scale based on Redis queue length (Manim Worker)
```powershell
az containerapp update `
  --name medhavii-manim-worker `
  --resource-group medhavii-rg `
  --min-replicas 0 `
  --max-replicas 10 `
  --scale-rule-name redis-queue `
  --scale-rule-type azure-queue `
  --scale-rule-metadata queueLength=5
```

## Updating After Code Changes

```powershell
# 1. Build new images
docker build -f Dockerfile.api -t krvatsal/medhavii-api:v2 .

# 2. Push to Docker Hub
docker push krvatsal/medhavii-api:v2

# 3. Update Container App
az containerapp update `
  --name medhavii-api `
  --resource-group medhavii-rg `
  --image krvatsal/medhavii-api:v2
```

## Cost Optimization Tips

1. **Scale to Zero**: Set `--min-replicas 0` for manim-worker when not in use
2. **Use Consumption Plan**: Pay only for what you use
3. **Redis Basic Tier**: Sufficient for most workloads (~$15/month)
4. **Monitor Usage**: Use Azure Cost Management

## Monitoring & Debugging

### View real-time logs
```powershell
az containerapp logs show `
  --name medhavii-api `
  --resource-group medhavii-rg `
  --follow `
  --tail 50
```

### Get revision history
```powershell
az containerapp revision list `
  --name medhavii-api `
  --resource-group medhavii-rg `
  --output table
```

### Rollback to previous version
```powershell
az containerapp revision activate `
  --name medhavii-api `
  --resource-group medhavii-rg `
  --revision <REVISION_NAME>
```

## Troubleshooting

### Container won't start
```powershell
# Check logs
az containerapp logs show --name medhavii-api --resource-group medhavii-rg --tail 100

# Check environment variables
az containerapp show --name medhavii-api --resource-group medhavii-rg --query properties.template.containers[0].env
```

### Redis connection issues
```powershell
# Verify Redis is running
az redis show --name medhavii-redis --resource-group medhavii-rg

# Test connection (from local machine)
redis-cli -h medhavii-redis.redis.cache.windows.net -p 6380 -a YOUR_REDIS_KEY --tls
```

### High costs
```powershell
# Check current resource usage
az monitor metrics list `
  --resource /subscriptions/YOUR_SUB/resourceGroups/medhavii-rg/providers/Microsoft.App/containerApps/medhavii-api `
  --metric-names Requests `
  --aggregation count
```

## Next Steps

1. ✅ Set up custom domain
2. ✅ Configure SSL/TLS certificates
3. ✅ Set up monitoring alerts
4. ✅ Configure backup for PostgreSQL
5. ✅ Set up CI/CD pipeline (GitHub Actions)

## Clean Up (if needed)

```powershell
# Delete everything
az group delete --name medhavii-rg --yes --no-wait
```

---

## Quick Reference

**Your URLs after deployment:**
- Frontend: `https://medhavii-frontend.XXXXXXXXXXX.eastus.azurecontainerapps.io`
- API: `https://medhavii-api.XXXXXXXXXXX.eastus.azurecontainerapps.io`
- Redis: `medhavii-redis.redis.cache.windows.net:6380`

**Estimated Monthly Costs:**
- Container Apps: $20-100 (depends on usage)
- Azure Cache for Redis: $15 (Basic tier)
- PostgreSQL: $5-30 (depends on tier)
- **Total: ~$40-150/month**
