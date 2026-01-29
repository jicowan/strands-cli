# Session Backend Deployment Guide

Complete guide for deploying the Session Backend to Kubernetes using Helm.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Building the Docker Image](#building-the-docker-image)
4. [Deployment Steps](#deployment-steps)
5. [Configuration](#configuration)
6. [Verification](#verification)
7. [Troubleshooting](#troubleshooting)
8. [Maintenance](#maintenance)

## Prerequisites

### Required Tools

- **Kubernetes Cluster**: v1.19 or higher
  - For AWS: EKS cluster
  - For local: minikube, kind, or k3s
- **Helm**: v3.0 or higher
- **kubectl**: Configured to access your cluster
- **Docker**: For building images

### Cluster Requirements

- Storage provisioner for persistent volumes
- Ingress controller (optional, for external access)
- cert-manager (optional, for TLS certificates)

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/your-org/strands-cli.git
cd strands-cli/session_backend
```

### 2. Build Docker Image

```bash
# Build the image
docker build -t session-backend-api:v1.0.0 -f Dockerfile .

# Tag for your registry
docker tag session-backend-api:v1.0.0 your-registry.example.com/session-backend-api:v1.0.0

# Push to registry
docker push your-registry.example.com/session-backend-api:v1.0.0
```

### 3. Deploy with Helm

```bash
cd helm

# Development deployment
helm install session-backend ./session-backend -f session-backend/values-development.yaml

# Production deployment
helm install session-backend ./session-backend -f session-backend/values-production.yaml
```

## Building the Docker Image

### Local Build

```bash
cd session_backend

# Build for local testing
docker build -t session-backend-api:latest -f Dockerfile .
```

### Multi-Architecture Build

For production deployments supporting multiple architectures:

```bash
# Create and use buildx builder
docker buildx create --name multiarch --use

# Build for multiple platforms
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t your-registry.example.com/session-backend-api:v1.0.0 \
  --push \
  -f Dockerfile .
```

### Using Docker Compose for Local Testing

Before deploying to Kubernetes, test locally:

```bash
cd session_backend
docker-compose up -d

# Test the API
curl http://localhost:8001/health
curl http://localhost:8001/docs

# Stop when done
docker-compose down
```

## Deployment Steps

### Step 1: Prepare Configuration

Create a custom values file:

```bash
cp helm/session-backend/values.yaml helm/session-backend/values-custom.yaml
```

Edit `values-custom.yaml`:

```yaml
sessionBackend:
  image:
    repository: your-registry.example.com/session-backend-api
    tag: "v1.0.0"

postgresql:
  auth:
    password: "your-secure-password"  # CHANGE THIS!
```

### Step 2: Create Namespace

```bash
kubectl create namespace session-backend
```

### Step 3: Create Image Pull Secret (if using private registry)

```bash
kubectl create secret docker-registry regcred \
  --docker-server=your-registry.example.com \
  --docker-username=your-username \
  --docker-password=your-password \
  --docker-email=your-email@example.com \
  -n session-backend
```

Update values file:

```yaml
global:
  imagePullSecrets:
    - name: regcred
```

### Step 4: Install Helm Chart

```bash
helm install session-backend ./helm/session-backend \
  -f helm/session-backend/values-custom.yaml \
  -n session-backend
```

### Step 5: Verify Deployment

```bash
# Check pods
kubectl get pods -n session-backend

# Check services
kubectl get svc -n session-backend

# Check logs
kubectl logs -l app.kubernetes.io/name=session-backend -n session-backend
```

## Configuration

### Environment-Specific Configurations

#### Development

```bash
helm install session-backend ./helm/session-backend \
  -f helm/session-backend/values-development.yaml \
  -n session-backend
```

Features:
- Single replica
- Minimal resources
- Debug logging
- No ingress
- Simple password

#### Production

```bash
helm install session-backend ./helm/session-backend \
  -f helm/session-backend/values-production.yaml \
  -n session-backend
```

Features:
- Multiple replicas (3+)
- Autoscaling enabled
- Production resources
- Ingress with TLS
- Network policies
- Pod disruption budget
- Anti-affinity rules

### AWS EKS Specific Configuration

For EKS deployments, use gp3 storage class:

```yaml
postgresql:
  primary:
    persistence:
      storageClass: "gp3"
      size: 50Gi
```

### External PostgreSQL

To use an external PostgreSQL database:

```yaml
postgresql:
  enabled: false

sessionBackend:
  env:
    - name: POSTGRES_HOST
      value: "external-postgres.example.com"
    - name: POSTGRES_PORT
      value: "5432"
    - name: POSTGRES_DB
      value: "sessions"
    - name: POSTGRES_USER
      valueFrom:
        secretKeyRef:
          name: external-postgres-secret
          key: username
    - name: POSTGRES_PASSWORD
      valueFrom:
        secretKeyRef:
          name: external-postgres-secret
          key: password
```

Create the secret:

```bash
kubectl create secret generic external-postgres-secret \
  --from-literal=username=postgres \
  --from-literal=password=your-password \
  -n session-backend
```

### Ingress Configuration

#### With cert-manager

```yaml
ingress:
  enabled: true
  className: "nginx"
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
  hosts:
    - host: session-backend.example.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: session-backend-tls
      hosts:
        - session-backend.example.com
```

#### With existing TLS certificate

```bash
kubectl create secret tls session-backend-tls \
  --cert=path/to/tls.crt \
  --key=path/to/tls.key \
  -n session-backend
```

## Verification

### Health Checks

```bash
# Port forward to access locally
kubectl port-forward svc/session-backend 8001:8001 -n session-backend

# Check API health
curl http://localhost:8001/health

# Check database connectivity
curl http://localhost:8001/health/db

# View API documentation
open http://localhost:8001/docs
```

### Test API Endpoints

```bash
# Create a session
curl -X POST http://localhost:8001/api/v1/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-session",
    "session_type": "AGENT"
  }'

# Get session
curl http://localhost:8001/api/v1/sessions/test-session

# Delete session
curl -X DELETE http://localhost:8001/api/v1/sessions/test-session
```

### Database Verification

```bash
# Connect to PostgreSQL
kubectl exec -it session-backend-postgresql-0 -n session-backend -- psql -U postgres -d sessions

# Run queries
SELECT COUNT(*) FROM sessions;
SELECT COUNT(*) FROM session_agents;
SELECT COUNT(*) FROM session_messages;
```

## Troubleshooting

### Pods Not Starting

**Check pod status:**
```bash
kubectl get pods -n session-backend
kubectl describe pod <pod-name> -n session-backend
```

**Common issues:**
- Image pull errors: Check image repository and pull secrets
- Resource constraints: Check node resources
- Init container failures: Check PostgreSQL connectivity

### Database Connection Failures

**Check PostgreSQL pod:**
```bash
kubectl logs session-backend-postgresql-0 -n session-backend
```

**Test connectivity from API pod:**
```bash
kubectl exec -it <api-pod-name> -n session-backend -- \
  nc -zv session-backend-postgresql 5432
```

### Persistence Issues

**Check PVC status:**
```bash
kubectl get pvc -n session-backend
```

**If PVC is pending:**
```bash
kubectl describe pvc <pvc-name> -n session-backend
```

Check storage class availability:
```bash
kubectl get storageclass
```

### Performance Issues

**Check resource usage:**
```bash
kubectl top pods -n session-backend
kubectl top nodes
```

**Scale up if needed:**
```bash
kubectl scale deployment session-backend --replicas=5 -n session-backend
```

## Maintenance

### Upgrading

```bash
# Update image tag in values file
helm upgrade session-backend ./helm/session-backend \
  -f helm/session-backend/values-custom.yaml \
  -n session-backend
```

### Rollback

```bash
# View release history
helm history session-backend -n session-backend

# Rollback to previous version
helm rollback session-backend -n session-backend

# Rollback to specific revision
helm rollback session-backend 2 -n session-backend
```

### Backup

**Backup PostgreSQL:**
```bash
kubectl exec session-backend-postgresql-0 -n session-backend -- \
  pg_dump -U postgres sessions > backup-$(date +%Y%m%d).sql
```

**Backup to S3 (AWS):**
```bash
kubectl exec session-backend-postgresql-0 -n session-backend -- \
  pg_dump -U postgres sessions | \
  aws s3 cp - s3://your-bucket/backups/sessions-$(date +%Y%m%d).sql
```

### Restore

```bash
kubectl exec -i session-backend-postgresql-0 -n session-backend -- \
  psql -U postgres sessions < backup-20260114.sql
```

### Monitoring

**View logs:**
```bash
# API logs
kubectl logs -f -l app.kubernetes.io/name=session-backend,app.kubernetes.io/component=api -n session-backend

# Database logs
kubectl logs -f session-backend-postgresql-0 -n session-backend
```

**Metrics (if metrics-server is installed):**
```bash
kubectl top pods -n session-backend
```

### Scaling

**Manual scaling:**
```bash
kubectl scale deployment session-backend --replicas=5 -n session-backend
```

**Enable autoscaling:**
```yaml
sessionBackend:
  autoscaling:
    enabled: true
    minReplicas: 3
    maxReplicas: 10
    targetCPUUtilizationPercentage: 70
```

### Cleanup

**Uninstall release:**
```bash
helm uninstall session-backend -n session-backend
```

**Delete namespace:**
```bash
kubectl delete namespace session-backend
```

**Note:** PVCs are not automatically deleted. Delete manually if needed:
```bash
kubectl delete pvc -n session-backend --all
```

## Best Practices

1. **Security**
   - Always change default passwords
   - Use Kubernetes secrets for sensitive data
   - Enable network policies in production
   - Use TLS for ingress

2. **High Availability**
   - Run multiple replicas (3+ in production)
   - Enable pod disruption budgets
   - Use anti-affinity rules
   - Configure autoscaling

3. **Monitoring**
   - Set up health check alerts
   - Monitor resource usage
   - Track API metrics
   - Regular log reviews

4. **Backup**
   - Schedule regular database backups
   - Test restore procedures
   - Store backups off-cluster

5. **Updates**
   - Test updates in staging first
   - Use rolling updates
   - Keep rollback plan ready
   - Monitor during updates

## Support

For issues and questions:
- Documentation: https://strandsagents.com/documentation
- GitHub Issues: https://github.com/your-org/strands-cli/issues
