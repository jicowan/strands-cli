# Session Backend Helm Chart

A Helm chart for deploying the Session Backend API with PostgreSQL to Kubernetes.

## Overview

This chart deploys:
- **Session Backend API**: FastAPI-based REST API for Strands agent session management
- **PostgreSQL Database**: Persistent storage for sessions, agents, and messages
- **Optional Components**: Ingress, HPA, Network Policies, Pod Disruption Budget

## Prerequisites

- Kubernetes 1.19+
- Helm 3.0+
- PV provisioner support in the underlying infrastructure (for PostgreSQL persistence)

## Installing the Chart

### Basic Installation

```bash
helm install session-backend ./session-backend
```

### Installation with Custom Values

```bash
helm install session-backend ./session-backend \
  --set postgresql.auth.password=your-secure-password \
  --set sessionBackend.image.repository=your-registry/session-backend-api \
  --set sessionBackend.image.tag=v1.0.0
```

### Installation from Values File

```bash
helm install session-backend ./session-backend -f custom-values.yaml
```

## Uninstalling the Chart

```bash
helm uninstall session-backend
```

This removes all Kubernetes components associated with the chart and deletes the release.

## Configuration

### Key Configuration Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `sessionBackend.replicaCount` | Number of API replicas | `2` |
| `sessionBackend.image.repository` | API image repository | `session-backend-api` |
| `sessionBackend.image.tag` | API image tag | `latest` |
| `sessionBackend.service.type` | Kubernetes service type | `ClusterIP` |
| `sessionBackend.service.port` | Service port | `8001` |
| `sessionBackend.resources.limits.cpu` | CPU limit | `500m` |
| `sessionBackend.resources.limits.memory` | Memory limit | `512Mi` |
| `sessionBackend.autoscaling.enabled` | Enable HPA | `false` |
| `postgresql.enabled` | Deploy PostgreSQL | `true` |
| `postgresql.auth.password` | PostgreSQL password | `changeme` |
| `postgresql.auth.database` | Database name | `sessions` |
| `postgresql.primary.persistence.enabled` | Enable persistence | `true` |
| `postgresql.primary.persistence.size` | PVC size | `10Gi` |
| `ingress.enabled` | Enable ingress | `false` |
| `ingress.className` | Ingress class | `nginx` |

### Full Configuration

See [values.yaml](values.yaml) for all available configuration options.

## Examples

### Production Deployment with Ingress

```yaml
# production-values.yaml
sessionBackend:
  replicaCount: 3
  image:
    repository: your-registry/session-backend-api
    tag: v1.0.0
  resources:
    limits:
      cpu: 1000m
      memory: 1Gi
    requests:
      cpu: 500m
      memory: 512Mi
  autoscaling:
    enabled: true
    minReplicas: 3
    maxReplicas: 10

postgresql:
  auth:
    password: "your-secure-password"
  primary:
    persistence:
      size: 50Gi
      storageClass: "gp3"
    resources:
      limits:
        cpu: 2000m
        memory: 2Gi

ingress:
  enabled: true
  className: nginx
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
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

Deploy:
```bash
helm install session-backend ./session-backend -f production-values.yaml
```

### Development Deployment

```yaml
# dev-values.yaml
sessionBackend:
  replicaCount: 1
  resources:
    limits:
      cpu: 250m
      memory: 256Mi
    requests:
      cpu: 100m
      memory: 128Mi

postgresql:
  auth:
    password: "devpassword"
  primary:
    persistence:
      size: 5Gi
```

Deploy:
```bash
helm install session-backend ./session-backend -f dev-values.yaml
```

### Using External PostgreSQL

```yaml
# external-db-values.yaml
postgresql:
  enabled: false

externalPostgresql:
  host: "postgres.example.com"
  port: 5432
  database: "sessions"
  existingSecret: "external-postgres-secret"

sessionBackend:
  env:
    - name: POSTGRES_HOST
      value: "postgres.example.com"
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

## Accessing the Application

### Port Forward (Development)

```bash
kubectl port-forward svc/session-backend 8001:8001
```

Then access:
- API: http://localhost:8001
- Health: http://localhost:8001/health
- Docs: http://localhost:8001/docs

### Via Ingress (Production)

If ingress is enabled, access via the configured hostname:
```
https://session-backend.example.com
```

## Monitoring

### Health Checks

The chart includes liveness and readiness probes:

- **Liveness**: `GET /health` - Checks if API is running
- **Readiness**: `GET /health/db` - Checks database connectivity

### Logs

View API logs:
```bash
kubectl logs -l app.kubernetes.io/name=session-backend,app.kubernetes.io/component=api
```

View PostgreSQL logs:
```bash
kubectl logs -l app.kubernetes.io/name=session-backend,app.kubernetes.io/component=database
```

## Backup and Restore

### Backup PostgreSQL

```bash
kubectl exec -it session-backend-postgresql-0 -- pg_dump -U postgres sessions > backup.sql
```

### Restore PostgreSQL

```bash
kubectl exec -i session-backend-postgresql-0 -- psql -U postgres sessions < backup.sql
```

## Troubleshooting

### API Not Starting

Check logs:
```bash
kubectl logs -l app.kubernetes.io/name=session-backend,app.kubernetes.io/component=api
```

Common issues:
- Database connection failure (check PostgreSQL is running)
- Image pull errors (check image repository and credentials)

### Database Connection Issues

Check PostgreSQL status:
```bash
kubectl get pods -l app.kubernetes.io/component=database
kubectl logs session-backend-postgresql-0
```

Test connection from API pod:
```bash
kubectl exec -it <api-pod-name> -- nc -zv session-backend-postgresql 5432
```

### Persistence Issues

Check PVC status:
```bash
kubectl get pvc
```

If PVC is pending, check storage class:
```bash
kubectl get storageclass
```

## Upgrading

### Upgrade Release

```bash
helm upgrade session-backend ./session-backend -f values.yaml
```

### Rollback

```bash
helm rollback session-backend
```

## Security Considerations

1. **Change Default Password**: Always change `postgresql.auth.password` in production
2. **Use Secrets**: Store sensitive data in Kubernetes secrets
3. **Enable Network Policies**: Set `networkPolicy.enabled=true` for network isolation
4. **Use TLS**: Enable ingress with TLS certificates
5. **Resource Limits**: Set appropriate resource limits to prevent resource exhaustion
6. **Security Context**: The chart uses non-root users and drops capabilities

## Support

For issues and questions:
- Documentation: https://strandsagents.com/documentation
- GitHub: https://github.com/your-org/strands-cli

## License

Copyright © 2026 Strands Team
