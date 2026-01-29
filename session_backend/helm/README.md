# Session Backend Helm Charts

Complete Helm chart for deploying the Session Backend API with PostgreSQL to Kubernetes.

## Overview

This directory contains production-ready Helm charts for deploying the Session Backend, a FastAPI-based REST API that provides session management for Strands AI agents with PostgreSQL persistence.

## Directory Structure

```
helm/
├── session-backend/              # Main Helm chart
│   ├── Chart.yaml               # Chart metadata
│   ├── values.yaml              # Default configuration values
│   ├── values-development.yaml  # Development environment values
│   ├── values-production.yaml   # Production environment values
│   ├── README.md                # Chart documentation
│   ├── .helmignore             # Files to ignore when packaging
│   └── templates/               # Kubernetes manifest templates
│       ├── _helpers.tpl         # Template helpers
│       ├── NOTES.txt            # Post-installation notes
│       ├── deployment.yaml      # API deployment
│       ├── service.yaml         # API service
│       ├── serviceaccount.yaml  # Service account
│       ├── secret.yaml          # PostgreSQL credentials
│       ├── postgresql-statefulset.yaml  # PostgreSQL StatefulSet
│       ├── postgresql-service.yaml      # PostgreSQL service
│       ├── postgresql-configmap.yaml    # Database init scripts
│       ├── hpa.yaml             # Horizontal Pod Autoscaler
│       ├── ingress.yaml         # Ingress configuration
│       ├── poddisruptionbudget.yaml    # PDB for HA
│       └── networkpolicy.yaml   # Network policies
├── DEPLOYMENT_GUIDE.md          # Complete deployment guide
└── QUICK_REFERENCE.md           # Quick command reference
```

## Quick Start

### Prerequisites

- Kubernetes 1.19+
- Helm 3.0+
- kubectl configured
- Docker image built and pushed to registry

### Install

```bash
# Development
helm install session-backend ./session-backend \
  -f session-backend/values-development.yaml \
  -n session-backend --create-namespace

# Production
helm install session-backend ./session-backend \
  -f session-backend/values-production.yaml \
  -n session-backend --create-namespace
```

### Verify

```bash
kubectl get pods -n session-backend
kubectl port-forward svc/session-backend 8001:8001 -n session-backend
curl http://localhost:8001/health
```

## Documentation

- **[Deployment Guide](DEPLOYMENT_GUIDE.md)** - Complete step-by-step deployment instructions
- **[Quick Reference](QUICK_REFERENCE.md)** - Common commands and operations
- **[Chart README](session-backend/README.md)** - Detailed chart documentation

## Features

### High Availability
- Multiple replicas with anti-affinity rules
- Horizontal Pod Autoscaler (HPA)
- Pod Disruption Budget (PDB)
- Health checks (liveness and readiness probes)

### Security
- Non-root containers
- Security contexts with dropped capabilities
- Network policies for pod isolation
- Kubernetes secrets for sensitive data
- Optional TLS with cert-manager

### Persistence
- PostgreSQL StatefulSet with persistent volumes
- Configurable storage class and size
- Automatic database initialization
- Backup and restore procedures

### Observability
- Health check endpoints
- Structured logging
- Resource limits and requests
- Ready for metrics integration

## Configuration

### Key Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `sessionBackend.replicaCount` | Number of API replicas | `2` |
| `sessionBackend.image.repository` | API image repository | `session-backend-api` |
| `sessionBackend.image.tag` | API image tag | `latest` |
| `postgresql.auth.password` | PostgreSQL password | `changeme` |
| `postgresql.primary.persistence.size` | PVC size | `10Gi` |
| `ingress.enabled` | Enable ingress | `false` |

See [values.yaml](session-backend/values.yaml) for all options.

## Deployment Scenarios

### Local Development (Minikube/Kind)

```bash
helm install session-backend ./session-backend \
  -f session-backend/values-development.yaml
```

Features:
- Single replica
- Minimal resources
- No ingress
- Simple configuration

### AWS EKS Production

```bash
helm install session-backend ./session-backend \
  -f session-backend/values-production.yaml \
  --set postgresql.primary.persistence.storageClass=gp3 \
  --set sessionBackend.image.repository=123456789.dkr.ecr.us-east-1.amazonaws.com/session-backend-api
```

Features:
- Multiple replicas (3+)
- Autoscaling enabled
- Production resources
- Ingress with TLS
- Network policies

### External PostgreSQL

```bash
helm install session-backend ./session-backend \
  --set postgresql.enabled=false \
  --set externalPostgresql.host=postgres.example.com \
  --set externalPostgresql.database=sessions
```

## Maintenance

### Upgrade

```bash
helm upgrade session-backend ./session-backend \
  -f session-backend/values-production.yaml
```

### Rollback

```bash
helm rollback session-backend
```

### Backup Database

```bash
kubectl exec session-backend-postgresql-0 -n session-backend -- \
  pg_dump -U postgres sessions > backup.sql
```

### Scale

```bash
kubectl scale deployment session-backend --replicas=5 -n session-backend
```

## Troubleshooting

### Check Status

```bash
helm status session-backend -n session-backend
kubectl get all -n session-backend
```

### View Logs

```bash
kubectl logs -l app.kubernetes.io/name=session-backend -n session-backend
```

### Common Issues

1. **Pods not starting**: Check image pull secrets and resource availability
2. **Database connection failed**: Verify PostgreSQL pod is running
3. **PVC pending**: Check storage class availability

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed troubleshooting.

## Testing

### API Health Check

```bash
kubectl port-forward svc/session-backend 8001:8001 -n session-backend
curl http://localhost:8001/health
curl http://localhost:8001/health/db
```

### Create Test Session

```bash
curl -X POST http://localhost:8001/api/v1/sessions \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test-123", "session_type": "AGENT"}'
```

## Best Practices

1. **Always change default passwords** in production
2. **Use specific image tags** instead of `latest`
3. **Enable autoscaling** for production workloads
4. **Configure resource limits** to prevent resource exhaustion
5. **Enable network policies** for security
6. **Set up regular backups** for PostgreSQL
7. **Use ingress with TLS** for external access
8. **Monitor resource usage** and adjust limits

## Support

- **Documentation**: https://strandsagents.com/documentation
- **Issues**: https://github.com/your-org/strands-cli/issues
- **Chart Version**: 0.1.0
- **App Version**: 1.0.0

## License

Copyright © 2026 Strands Team
