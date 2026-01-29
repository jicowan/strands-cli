# Session Backend Helm Deployment

Complete Helm chart for deploying the Session Backend API with PostgreSQL to Kubernetes.

## 📁 What Was Created

A production-ready Helm chart in `session_backend/helm/` with:

- **14 Kubernetes manifest templates**
- **3 environment configurations** (default, dev, prod)
- **Complete documentation** (4 guides)
- **Validation script**

## 🚀 Quick Start

### 1. Validate the Chart

```bash
cd session_backend/helm
./validate-chart.sh
```

### 2. Install to Kubernetes

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

### 3. Verify Deployment

```bash
kubectl get pods -n session-backend
kubectl port-forward svc/session-backend 8001:8001 -n session-backend
curl http://localhost:8001/health
```

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [helm/README.md](helm/README.md) | Overview and quick start |
| [helm/DEPLOYMENT_GUIDE.md](helm/DEPLOYMENT_GUIDE.md) | Complete deployment instructions |
| [helm/QUICK_REFERENCE.md](helm/QUICK_REFERENCE.md) | Command reference |
| [helm/HELM_CHART_SUMMARY.md](helm/HELM_CHART_SUMMARY.md) | Technical summary |
| [helm/session-backend/README.md](helm/session-backend/README.md) | Chart documentation |

## 🎯 Key Features

### High Availability
- ✅ Multiple replicas (2-3+)
- ✅ Horizontal Pod Autoscaler
- ✅ Pod Disruption Budget
- ✅ Anti-affinity rules
- ✅ Health checks

### Security
- ✅ Non-root containers
- ✅ Security contexts
- ✅ Network policies
- ✅ Secrets management
- ✅ TLS support

### Persistence
- ✅ PostgreSQL StatefulSet
- ✅ Persistent volumes
- ✅ Automatic schema init
- ✅ Backup procedures

### Flexibility
- ✅ Multiple environments
- ✅ External database support
- ✅ Configurable ingress
- ✅ Custom storage classes

## 📦 Chart Structure

```
helm/
├── session-backend/              # Main chart
│   ├── Chart.yaml               # Metadata
│   ├── values.yaml              # Default config
│   ├── values-development.yaml  # Dev config
│   ├── values-production.yaml   # Prod config
│   └── templates/               # 14 manifest templates
│       ├── deployment.yaml      # API deployment
│       ├── service.yaml         # API service
│       ├── postgresql-*.yaml    # PostgreSQL resources
│       ├── hpa.yaml            # Autoscaling
│       ├── ingress.yaml        # External access
│       └── ...                 # More templates
├── DEPLOYMENT_GUIDE.md          # Complete guide
├── QUICK_REFERENCE.md           # Commands
└── validate-chart.sh            # Validation script
```

## ⚙️ Configuration

### Default (values.yaml)
- 2 API replicas
- 10Gi PostgreSQL storage
- ClusterIP service
- No ingress

### Development (values-development.yaml)
- 1 API replica
- Minimal resources
- 5Gi storage
- Debug logging

### Production (values-production.yaml)
- 3 API replicas
- Autoscaling (3-10)
- 50Gi gp3 storage
- Ingress with TLS
- Network policies

## 🔧 Common Operations

### Install
```bash
helm install session-backend ./session-backend -n session-backend --create-namespace
```

### Upgrade
```bash
helm upgrade session-backend ./session-backend -f values-production.yaml
```

### Rollback
```bash
helm rollback session-backend
```

### Uninstall
```bash
helm uninstall session-backend -n session-backend
```

### Scale
```bash
kubectl scale deployment session-backend --replicas=5 -n session-backend
```

## 🧪 Testing

### Validate Chart
```bash
cd helm
./validate-chart.sh
```

### Lint Chart
```bash
helm lint ./session-backend
```

### Dry Run
```bash
helm install session-backend ./session-backend --dry-run --debug
```

### Test API
```bash
kubectl port-forward svc/session-backend 8001:8001 -n session-backend

# Health check
curl http://localhost:8001/health

# Create session
curl -X POST http://localhost:8001/api/v1/sessions \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test-123", "session_type": "AGENT"}'
```

## 🔐 Security Checklist

Before production deployment:

- [ ] Change PostgreSQL password
- [ ] Use specific image tags (not `latest`)
- [ ] Configure image pull secrets (if private registry)
- [ ] Enable network policies
- [ ] Configure TLS for ingress
- [ ] Set resource limits
- [ ] Review security contexts
- [ ] Enable pod security policies

## 📊 Resource Requirements

### Minimum (Development)
- 1 node: 2 CPU, 4Gi memory
- 5Gi persistent storage

### Recommended (Production)
- 3+ nodes: 4 CPU, 8Gi memory each
- 50Gi+ persistent storage (gp3 on AWS)
- Ingress controller
- Cert-manager (optional)

## 🚨 Troubleshooting

### Pods Not Starting
```bash
kubectl get pods -n session-backend
kubectl describe pod <pod-name> -n session-backend
kubectl logs <pod-name> -n session-backend
```

### Database Connection Issues
```bash
kubectl logs session-backend-postgresql-0 -n session-backend
kubectl exec -it <api-pod> -n session-backend -- nc -zv session-backend-postgresql 5432
```

### PVC Pending
```bash
kubectl get pvc -n session-backend
kubectl describe pvc <pvc-name> -n session-backend
kubectl get storageclass
```

## 📈 Monitoring

### View Logs
```bash
kubectl logs -f -l app.kubernetes.io/name=session-backend -n session-backend
```

### Check Resources
```bash
kubectl top pods -n session-backend
kubectl top nodes
```

### Check HPA
```bash
kubectl get hpa -n session-backend
```

## 💾 Backup & Restore

### Backup Database
```bash
kubectl exec session-backend-postgresql-0 -n session-backend -- \
  pg_dump -U postgres sessions > backup-$(date +%Y%m%d).sql
```

### Restore Database
```bash
kubectl exec -i session-backend-postgresql-0 -n session-backend -- \
  psql -U postgres sessions < backup-20260114.sql
```

## 🎓 Next Steps

1. **Review Documentation**
   - Read [DEPLOYMENT_GUIDE.md](helm/DEPLOYMENT_GUIDE.md)
   - Check [QUICK_REFERENCE.md](helm/QUICK_REFERENCE.md)

2. **Build Docker Image**
   ```bash
   cd session_backend
   docker build -t your-registry/session-backend-api:v1.0.0 .
   docker push your-registry/session-backend-api:v1.0.0
   ```

3. **Customize Values**
   - Copy and edit values file
   - Update image repository
   - Change passwords
   - Configure ingress

4. **Deploy to Staging**
   - Test in non-production environment
   - Verify all features
   - Run API tests

5. **Deploy to Production**
   - Use production values
   - Enable monitoring
   - Set up backups
   - Configure alerts

## 📞 Support

- **Documentation**: https://strandsagents.com/documentation
- **Issues**: https://github.com/your-org/strands-cli/issues
- **Chart Version**: 0.1.0
- **App Version**: 1.0.0

## ✅ Validation Results

Run `./validate-chart.sh` to verify:
- ✅ Helm lint passes
- ✅ Template generation works
- ✅ All required files present
- ✅ Development config valid
- ✅ Production config valid
- ✅ Chart packages successfully

---

**Ready for deployment!** 🚀
