# Session Backend Helm Chart - Quick Reference

## Installation Commands

### Development
```bash
helm install session-backend ./session-backend \
  -f session-backend/values-development.yaml \
  -n session-backend --create-namespace
```

### Production
```bash
helm install session-backend ./session-backend \
  -f session-backend/values-production.yaml \
  -n session-backend --create-namespace
```

### Custom Values
```bash
helm install session-backend ./session-backend \
  --set postgresql.auth.password=mysecretpassword \
  --set sessionBackend.image.tag=v1.0.0 \
  -n session-backend --create-namespace
```

## Common Operations

### Upgrade
```bash
helm upgrade session-backend ./session-backend \
  -f session-backend/values-production.yaml \
  -n session-backend
```

### Rollback
```bash
helm rollback session-backend -n session-backend
```

### Uninstall
```bash
helm uninstall session-backend -n session-backend
```

### Status
```bash
helm status session-backend -n session-backend
helm list -n session-backend
```

## Verification Commands

### Check Pods
```bash
kubectl get pods -n session-backend
kubectl describe pod <pod-name> -n session-backend
kubectl logs -f <pod-name> -n session-backend
```

### Check Services
```bash
kubectl get svc -n session-backend
kubectl describe svc session-backend -n session-backend
```

### Port Forward
```bash
kubectl port-forward svc/session-backend 8001:8001 -n session-backend
```

### Health Checks
```bash
curl http://localhost:8001/health
curl http://localhost:8001/health/db
curl http://localhost:8001/docs
```

## Database Operations

### Connect to PostgreSQL
```bash
kubectl exec -it session-backend-postgresql-0 -n session-backend -- \
  psql -U postgres -d sessions
```

### Backup Database
```bash
kubectl exec session-backend-postgresql-0 -n session-backend -- \
  pg_dump -U postgres sessions > backup.sql
```

### Restore Database
```bash
kubectl exec -i session-backend-postgresql-0 -n session-backend -- \
  psql -U postgres sessions < backup.sql
```

### Check Database Size
```bash
kubectl exec session-backend-postgresql-0 -n session-backend -- \
  psql -U postgres -d sessions -c "SELECT pg_size_pretty(pg_database_size('sessions'));"
```

## Scaling

### Manual Scale
```bash
kubectl scale deployment session-backend --replicas=5 -n session-backend
```

### Check HPA
```bash
kubectl get hpa -n session-backend
kubectl describe hpa session-backend -n session-backend
```

## Troubleshooting

### View All Resources
```bash
kubectl get all -n session-backend
```

### Check Events
```bash
kubectl get events -n session-backend --sort-by='.lastTimestamp'
```

### Check Resource Usage
```bash
kubectl top pods -n session-backend
kubectl top nodes
```

### Check PVC
```bash
kubectl get pvc -n session-backend
kubectl describe pvc <pvc-name> -n session-backend
```

### Debug Pod
```bash
kubectl run debug --rm -it --image=busybox -n session-backend -- sh
```

## Configuration Examples

### Change Password
```bash
helm upgrade session-backend ./session-backend \
  --set postgresql.auth.password=newpassword \
  -n session-backend
```

### Enable Ingress
```bash
helm upgrade session-backend ./session-backend \
  --set ingress.enabled=true \
  --set ingress.hosts[0].host=session-backend.example.com \
  -n session-backend
```

### Enable Autoscaling
```bash
helm upgrade session-backend ./session-backend \
  --set sessionBackend.autoscaling.enabled=true \
  --set sessionBackend.autoscaling.minReplicas=3 \
  --set sessionBackend.autoscaling.maxReplicas=10 \
  -n session-backend
```

### Update Image
```bash
helm upgrade session-backend ./session-backend \
  --set sessionBackend.image.tag=v1.1.0 \
  -n session-backend
```

## Useful kubectl Aliases

Add to your `~/.bashrc` or `~/.zshrc`:

```bash
alias k='kubectl'
alias kgp='kubectl get pods -n session-backend'
alias kgs='kubectl get svc -n session-backend'
alias kl='kubectl logs -f -n session-backend'
alias kd='kubectl describe -n session-backend'
alias ke='kubectl exec -it -n session-backend'
```

## API Testing

### Create Session
```bash
curl -X POST http://localhost:8001/api/v1/sessions \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test-123", "session_type": "AGENT"}'
```

### Get Session
```bash
curl http://localhost:8001/api/v1/sessions/test-123
```

### Create Agent
```bash
curl -X POST http://localhost:8001/api/v1/sessions/test-123/agents \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "agent-1",
    "state": {},
    "conversation_manager_state": {"__name__": "SlidingWindowConversationManager"},
    "internal_state": {}
  }'
```

### Create Message
```bash
curl -X POST http://localhost:8001/api/v1/sessions/test-123/agents/agent-1/messages \
  -H "Content-Type: application/json" \
  -d '{
    "message_id": 0,
    "message": {"role": "user", "content": [{"text": "Hello"}]},
    "redact_message": null
  }'
```

### List Messages
```bash
curl http://localhost:8001/api/v1/sessions/test-123/agents/agent-1/messages
```

## Monitoring Queries

### Check API Response Time
```bash
time curl -s http://localhost:8001/health > /dev/null
```

### Watch Pod Status
```bash
watch kubectl get pods -n session-backend
```

### Stream Logs
```bash
kubectl logs -f -l app.kubernetes.io/name=session-backend -n session-backend
```

## Emergency Procedures

### Force Delete Pod
```bash
kubectl delete pod <pod-name> -n session-backend --force --grace-period=0
```

### Restart Deployment
```bash
kubectl rollout restart deployment session-backend -n session-backend
```

### Check Rollout Status
```bash
kubectl rollout status deployment session-backend -n session-backend
```

### Pause Rollout
```bash
kubectl rollout pause deployment session-backend -n session-backend
```

### Resume Rollout
```bash
kubectl rollout resume deployment session-backend -n session-backend
```
