# Microservices Architecture Migration Guide

## New Architecture

```
Azure Container Apps Environment
│
├── medhavii-api (FastAPI + LLM + orchestration)
│   - Port: 8000
│   - Handles: HTTP API, LLM calls, presentation generation, image generation, TTS
│   - Dockerfile: Dockerfile.api
│
├── medhavii-manim-worker (Manim + MCP server)
│   - Handles: Video generation via Manim MCP
│   - Scalable: Can run multiple replicas
│   - Dockerfile: Dockerfile.manim-worker
│
├── redis (queue / semaphore)
│   - Port: 6379
│   - Handles: Task queue, worker coordination, rate limiting
│   - Image: redis:7-alpine
│
├── medhavii-frontend (Next.js)
│   - Port: 3000
│   - Dockerfile: Dockerfile.frontend
│
└── nginx (reverse proxy - optional)
    - Port: 80
    - Routes: / -> frontend, /api/* -> api
    - Config: nginx.microservices.conf
```

## Files Created

1. **Dockerfile.api** - FastAPI backend service
2. **Dockerfile.manim-worker** - Manim video generation worker
3. **Dockerfile.frontend** - Next.js frontend service
4. **docker-compose.microservices.yml** - Local development orchestration
5. **nginx.microservices.conf** - Reverse proxy configuration
6. **servers/fastapi/workers/manim_worker.py** - Worker script for processing video tasks

## Benefits

✅ **Independent Scaling**
- Scale Manim workers independently (CPU-intensive)
- Scale API separately from workers
- Frontend scaled independently

✅ **Better Resource Utilization**
- Manim workers use different resource profile than API
- Can use cheaper/spot instances for workers

✅ **Improved Reliability**
- Video generation failures don't crash API
- Can restart services independently
- Better fault isolation

✅ **Faster Deployments**
- Update only changed services
- Smaller Docker images per service
- Faster CI/CD pipelines

## Local Development

### Start all services:
```bash
docker-compose -f docker-compose.microservices.yml up --build
```

### Start specific service:
```bash
docker-compose -f docker-compose.microservices.yml up api
```

### Scale Manim workers:
```bash
docker-compose -f docker-compose.microservices.yml up --scale manim-worker=4
```

## Code Changes Required

### 1. Update ManimService to use Redis Queue

**File:** `servers/fastapi/services/manim_service.py`

Add queue-based video generation:

```python
import redis.asyncio as redis
import uuid
import json

class ManimService:
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.use_queue = os.getenv("USE_MANIM_QUEUE", "false").lower() == "true"
        
    async def queue_video_generation(self, prompt: str, user_id: str) -> str:
        """Queue video generation task"""
        task_id = str(uuid.uuid4())
        
        redis_client = await redis.from_url(self.redis_url, encoding="utf-8")
        
        task_data = {
            "task_id": task_id,
            "prompt": prompt,
            "user_id": user_id
        }
        
        await redis_client.rpush("manim:video:queue", json.dumps(task_data))
        await redis_client.close()
        
        return task_id
        
    async def get_video_result(self, task_id: str) -> Optional[dict]:
        """Check task result"""
        redis_client = await redis.from_url(self.redis_url, encoding="utf-8")
        
        result_key = f"manim:video:result:{task_id}"
        result_json = await redis_client.get(result_key)
        
        await redis_client.close()
        
        if result_json:
            return json.loads(result_json)
        return None
```

### 2. Add Redis dependency

**File:** `servers/fastapi/pyproject.toml`

```toml
dependencies = [
    # ... existing deps ...
    "redis>=5.0.0",
]
```

### 3. Environment Variables

Add to Azure Container Apps configuration:

```bash
# API Service
REDIS_URL=redis://medhavii-redis:6379
USE_MANIM_QUEUE=true

# Manim Worker
REDIS_URL=redis://medhavii-redis:6379
DATABASE_URL=<your-postgres-url>
MANIM_SERVER_PATH=/opt/manim-mcp-server/src/manim_server.py
```

## Azure Container Apps Deployment

### 1. Create Container Apps Environment

```bash
az containerapp env create \
  --name medhavii-env \
  --resource-group medhavii-rg \
  --location eastus
```

### 2. Deploy Redis (Azure Cache for Redis recommended)

```bash
az redis create \
  --name medhavii-redis \
  --resource-group medhavii-rg \
  --location eastus \
  --sku Basic \
  --vm-size c0
```

### 3. Build and Push Images

```bash
# API
docker build -f Dockerfile.api -t krvatsal/medhavii-api:latest .
docker push krvatsal/medhavii-api:latest

# Manim Worker
docker build -f Dockerfile.manim-worker -t krvatsal/medhavii-manim-worker:latest .
docker push krvatsal/medhavii-manim-worker:latest

# Frontend
docker build -f Dockerfile.frontend -t krvatsal/medhavii-frontend:latest .
docker push krvatsal/medhavii-frontend:latest
```

### 4. Deploy Container Apps

```bash
# API
az containerapp create \
  --name medhavii-api \
  --resource-group medhavii-rg \
  --environment medhavii-env \
  --image krvatsal/medhavii-api:latest \
  --target-port 8000 \
  --ingress external \
  --min-replicas 1 \
  --max-replicas 5

# Manim Worker (no ingress, internal only)
az containerapp create \
  --name medhavii-manim-worker \
  --resource-group medhavii-rg \
  --environment medhavii-env \
  --image krvatsal/medhavii-manim-worker:latest \
  --ingress internal \
  --min-replicas 2 \
  --max-replicas 10 \
  --cpu 2 \
  --memory 4Gi

# Frontend
az containerapp create \
  --name medhavii-frontend \
  --resource-group medhavii-rg \
  --environment medhavii-env \
  --image krvatsal/medhavii-frontend:latest \
  --target-port 3000 \
  --ingress external \
  --min-replicas 1 \
  --max-replicas 3
```

## Migration Steps

1. **Test locally** with docker-compose.microservices.yml
2. **Update code** to use Redis queue for Manim
3. **Build images** for each service
4. **Deploy to Azure** Container Apps
5. **Monitor** and adjust scaling rules
6. **Switch traffic** from monolith to microservices

## Rollback Plan

Keep the original Dockerfile as backup. If issues arise:

```bash
# Revert to monolith
docker build -t krvatsal/medhavii:latest .
docker push krvatsal/medhavii:latest
```

## Cost Optimization

- Use Azure Cache for Redis (Basic tier: ~$15/month)
- Manim workers: Scale to zero when idle (KEDA integration)
- API: Min 1 replica, scale based on HTTP requests
- Frontend: Min 1 replica, scale based on HTTP requests

## Monitoring

Add health checks to each service:

```python
# API - servers/fastapi/api/v1/health.py
@router.get("/health")
async def health():
    return {"status": "healthy", "service": "api"}
```

## Next Steps

1. Test locally with `docker-compose -f docker-compose.microservices.yml up`
2. Implement Redis queue in ManimService
3. Deploy to Azure Container Apps
4. Set up monitoring and alerts
5. Configure autoscaling rules
