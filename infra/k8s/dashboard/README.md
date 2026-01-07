# Kubernetes Dashboard

This directory contains manifests for deploying the Kubernetes Dashboard - a web-based UI for managing your Kubernetes cluster.

## Features

- **Web-based UI** for cluster management
- **Admin access** with cluster-admin privileges
- **Metrics scraper** for resource monitoring
- **Secure access** with token-based authentication

## Quick Start

### Deploy Dashboard

```bash
cd infra/k8s
./deploy-dashboard.sh
```

The script will:
1. Create the `kubernetes-dashboard` namespace
2. Deploy the dashboard and metrics scraper
3. Create an admin user with full cluster access
4. Generate and display an access token
5. Save the token to `dashboard-token.txt`

### Access Dashboard

#### Option 1: kubectl proxy (Recommended)

```bash
# Start the proxy
kubectl proxy

# Access dashboard at:
# http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/
```

#### Option 2: Port Forward

```bash
# Forward port 8443
kubectl port-forward -n kubernetes-dashboard service/kubernetes-dashboard 8443:443

# Access dashboard at:
# https://localhost:8443
# (Accept self-signed certificate warning)
```

### Login to Dashboard

1. Select **Token** as the authentication method
2. Paste the token from `dashboard-token.txt` or from the deployment output
3. Click **Sign In**

### Get Token Anytime

```bash
# Get the token from the saved file
cat dashboard-token.txt

# Or create a new token
kubectl -n kubernetes-dashboard create token admin-user --duration=87600h
```

### Teardown Dashboard

```bash
./teardown-dashboard.sh
```

## What You Can Do

The Kubernetes Dashboard provides a visual interface for:

### Cluster Management
- View cluster health and resource usage
- Monitor nodes, pods, and services
- View logs and events

### Workload Management
- Create, edit, and delete deployments
- Scale deployments up or down
- View and manage pods, jobs, and cron jobs

### Service Management
- View and manage services
- Configure ingress and load balancers
- Manage endpoints

### Configuration
- View and edit ConfigMaps
- Manage Secrets
- View and edit resource quotas

### Storage
- View persistent volumes and claims
- Manage storage classes

### Namespace Management
- Switch between namespaces
- View namespace-specific resources

## Security Considerations

⚠️ **Important Security Notes:**

1. **Admin Access**: The default setup creates an admin user with `cluster-admin` role, giving full access to the cluster.

2. **Production Use**: For production environments:
   - Use more restrictive RBAC roles
   - Implement namespace-specific access
   - Use SSO/OIDC for authentication
   - Enable audit logging
   - Use TLS certificates from a trusted CA

3. **Token Security**:
   - Store tokens securely
   - Rotate tokens regularly
   - Never commit tokens to version control
   - Use short-lived tokens when possible

### Creating Limited-Access Users

For production, create users with limited permissions:

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: read-only-user
  namespace: kubernetes-dashboard
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: read-only-user
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: view  # Read-only access
subjects:
- kind: ServiceAccount
  name: read-only-user
  namespace: kubernetes-dashboard
```

## Troubleshooting

### Dashboard pod not starting

```bash
# Check pod status
kubectl get pods -n kubernetes-dashboard

# View pod details
kubectl describe pod -l k8s-app=kubernetes-dashboard -n kubernetes-dashboard

# Check logs
kubectl logs -f deployment/kubernetes-dashboard -n kubernetes-dashboard
```

### Token not working

```bash
# Delete and recreate the admin user
kubectl delete serviceaccount admin-user -n kubernetes-dashboard
kubectl delete clusterrolebinding admin-user

# Reapply RBAC
kubectl apply -f dashboard/dashboard-rbac.yaml

# Create new token
kubectl -n kubernetes-dashboard create token admin-user --duration=87600h
```

### Cannot access dashboard

```bash
# Check if services are running
kubectl get svc -n kubernetes-dashboard

# Verify endpoints
kubectl get endpoints -n kubernetes-dashboard

# Check if proxy/port-forward is running
ps aux | grep kubectl
```

### Certificate errors

The dashboard uses self-signed certificates by default. When accessing via port-forward:
- Click "Advanced" in your browser
- Click "Proceed to localhost (unsafe)"
- This is expected behavior for local development

## Architecture

```
┌─────────────────────────────────────────────┐
│     kubernetes-dashboard namespace          │
├─────────────────────────────────────────────┤
│                                             │
│  ┌──────────────────────────────────────┐  │
│  │   Kubernetes Dashboard               │  │
│  │   - Main UI (port 8443)             │  │
│  │   - Auto-generated TLS certs        │  │
│  │   - Token-based auth                │  │
│  └─────────────┬────────────────────────┘  │
│                │                            │
│                │                            │
│  ┌─────────────▼────────────────────────┐  │
│  │   Metrics Scraper                    │  │
│  │   - Collects resource metrics       │  │
│  │   - Provides monitoring data        │  │
│  └──────────────────────────────────────┘  │
│                                             │
│  Service Accounts:                          │
│  - kubernetes-dashboard (dashboard pods)    │
│  - admin-user (full cluster access)         │
│                                             │
└─────────────────────────────────────────────┘
```

## Components

### Dashboard (v2.7.0)
- **Image**: `kubernetesui/dashboard:v2.7.0`
- **Port**: 8443 (HTTPS)
- **Resources**: 100m CPU / 200Mi RAM (request)
- **Auto-generated TLS certificates**

### Metrics Scraper (v1.0.8)
- **Image**: `kubernetesui/metrics-scraper:v1.0.8`
- **Port**: 8000 (HTTP)
- **Resources**: 50m CPU / 100Mi RAM (request)
- **Provides resource usage metrics**

## Upgrade

To upgrade to a newer version:

1. Edit [dashboard-deployment.yaml](dashboard-deployment.yaml)
2. Update the image versions
3. Apply the changes:

```bash
kubectl apply -f dashboard/dashboard-deployment.yaml
kubectl rollout status deployment/kubernetes-dashboard -n kubernetes-dashboard
```

## Useful Commands

```bash
# View all dashboard resources
kubectl get all -n kubernetes-dashboard

# Check resource usage
kubectl top pods -n kubernetes-dashboard

# View dashboard logs
kubectl logs -f deployment/kubernetes-dashboard -n kubernetes-dashboard

# Restart dashboard
kubectl rollout restart deployment/kubernetes-dashboard -n kubernetes-dashboard

# Delete and redeploy
./teardown-dashboard.sh
./deploy-dashboard.sh
```

## Additional Resources

- [Official Kubernetes Dashboard Documentation](https://kubernetes.io/docs/tasks/access-application-cluster/web-ui-dashboard/)
- [Dashboard GitHub Repository](https://github.com/kubernetes/dashboard)
- [RBAC Documentation](https://kubernetes.io/docs/reference/access-authn-authz/rbac/)
