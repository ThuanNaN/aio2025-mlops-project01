# MLOps Kubernetes Infrastructure

This directory contains Kubernetes manifests for deploying the MLOps infrastructure including:
- **PostgreSQL**: Backend store for MLflow tracking server metadata and Airflow metadata
- **MinIO**: S3-compatible object storage for MLflow artifacts
- **MLflow**: Machine learning tracking server
- **Kafka**: 3-node streaming platform cluster (KRaft mode)
- **Apache Airflow**: Workflow orchestration platform (Airflow 3.x)
- **Kubernetes Dashboard**: Web-based UI for managing the Kubernetes cluster

## Architecture

```
┌───────────────────────────────────────────────┐
│                MLOps Namespace                │
├───────────────────────────────────────────────┤
│                                               │
│  ┌──────────────┐      ┌──────────────┐       │
│  │              │      │              │       │
│  │  PostgreSQL  │◄─────┤    MLflow    │       │
│  │              │      │    Server    │       │
│  │  Port: 5432  │      │              │       │
│  │              │      │  Port: 5000  │       │
│  └──────────────┘      └──────┬───────┘       │
│         ▲                     │               │
│         │                     │               │
│         │                     ▼               │
│    [PVC: 5Gi]          ┌──────────────┐       │
│                        │              │       │
│                        │    MinIO     │       │
│                        │              │       │
│                        │  API: 9000   │       │
│                        │  Console:    │       │
│                        │  9001        │       │
│                        └──────┬───────┘       │
│                               │               │
│                               ▼               │
│                          [PVC: 10Gi]          │
│                                               │
└───────────────────────────────────────────────┘
```

## Prerequisites

- Kubernetes cluster (minikube, kind, GKE, EKS, AKS, etc.)
- kubectl configured to access your cluster
- Sufficient cluster resources:
  - At least 2GB RAM available
  - At least 15Gi storage for PVCs

## Quick Start

### Deploy Everything

```bash
cd infra/k8s
chmod +x deploy.sh
./deploy.sh
```

### Access Services

**MLflow UI:**
```bash
kubectl port-forward svc/mlflow -n mlops 5000:5000
```
Then open http://localhost:5000

**MinIO Console:**
```bash
kubectl port-forward svc/minio -n mlops 9001:9001
```
Then open http://localhost:9001 (login: minio / minio123)

**MinIO API:**
```bash
kubectl port-forward svc/minio -n mlops 9000:9000
```

**Kubernetes Dashboard:**
```bash
# Deploy dashboard first
./deploy-dashboard.sh

# Access via kubectl proxy
kubectl proxy
# Then open: http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/

# OR via port-forward
kubectl port-forward -n kubernetes-dashboard service/kubernetes-dashboard 8443:443
# Then open: https://localhost:8443
```

**Apache Airflow UI:**
```bash
kubectl port-forward svc/airflow-webserver -n mlops 8080:8080
```
Then open http://localhost:8080 (login: admin / admin123)

**Kafka UI:**
```bash
kubectl port-forward svc/kafka-ui -n mlops 8080:8080
```
Then open http://localhost:8080

### Deploy Kubernetes Dashboard

```bash
./deploy-dashboard.sh
```

This will:
- Deploy the Kubernetes Dashboard
- Create an admin user with cluster-admin privileges
- Generate and display an access token
- Save the token to `dashboard-token.txt`

### Teardown Everything

```bash
./teardown.sh
./teardown-dashboard.sh  # If dashboard is deployed
```

## Manual Deployment

If you prefer to deploy components step by step:

### 1. Create Namespace
```bash
kubectl apply -f namespace.yaml
```

### 2. Deploy PostgreSQL
```bash
kubectl apply -f postgres/postgres-secret.yaml
kubectl apply -f postgres/postgres-pvc.yaml
kubectl apply -f postgres/postgres-deployment.yaml
kubectl apply -f postgres/postgres-service.yaml
```

Wait for PostgreSQL to be ready:
```bash
kubectl wait --for=condition=ready pod -l app=postgres -n mlops --timeout=120s
```

### 3. Deploy MinIO
```bash
kubectl apply -f minio/minio-secret.yaml
kubectl apply -f minio/minio-pvc.yaml
kubectl apply -f minio/minio-deployment.yaml
kubectl apply -f minio/minio-service.yaml
```

Wait for MinIO to be ready:
```bash
kubectl wait --for=condition=ready pod -l app=minio -n mlops --timeout=120s
```

Create the MLflow bucket:
```bash
kubectl apply -f minio/minio-bucket-job.yaml
```

### 5. Deploy Kafka
```bash
kubectl apply -f kafka/kafka-config.yaml
kubectl apply -f kafka/kafka-statefulset.yaml
kubectl appl (MLflow):**
- User: mlflow
- Password: mlflow123
- Database: mlflow

**PostgreSQL (Airflow):**
- User: airflow
- Password: airflow123
- Database: airflow

**MinIO:**
- Access Key: minio
- Secret Key: minio123
- Bucket: mlflow

**Apache Airflow:**
- Username: admin
- Password: a(MLflow) PVC: 5Gi
- PostgreSQL (Airflow) PVC: 5Gi
- MinIO PVC: 10Gi
- Airflow DAGs PVC: 1Gi
- Airflow Logs PVC: 2Gi

Adjust storage sizes in:
- [postgres/postgres-pvc.yaml](postgres/postgres-pvc.yaml)
- [minio/minio-pvc.yaml](minio/minio-pvc.yaml)
- [airflow/airflow-pvc.yaml](airflow/airflow
- [postgres/postgres-secret.yaml](postgres/postgres-secret.yaml)
- [minio/minio-secret.yaml](minio/minio-secret.yaml)
- [mlflow/mlflow-config.yaml](mlflow/mlflow-config.yaml)
- [airflow/airflow-secret.yaml](airflow/airflow-secret.yaml)
- [airflow/airflow-passwords.yaml](airflow/airflow-passwords
kubectl apply -f airflow/airflow-passwords.yaml
kubectl apply -f airflow/airflow-config.yaml
kubectl apply -f airflow/airflow-pvc.yaml
kubectl apply -f airflow/airflow-postgres.yaml
kubectl apply -f airflow/airflow-scheduler.yaml
kubectl apply -f airflow/airflow-webserver.yaml
```

Wait for Airflow to be ready:
- **Kafka**: Headless + ClusterIP (internal only)
- **Airflow**: LoadBalancer (external access)
```bash
kubectl wait --for=condition=ready pod -l app=airflow-webserver -n mlops --timeout=300s
```

### 4. Deploy MLflow
```bash
kubectl apply -f mlflow/mlflow-config.yaml
kubectl apply -f mlflow/mlflow-deployment.yaml
kubectl apply -f mlflow/mlflow-service.yaml
```

Wait for MLflow to be ready:
```bash
kubectl wait --for=condition=ready pod -l app=mlflow -n mlops --timeout=180s
```

## Configuration

### Default Credentials

**PostgreSQL:**
- User: mlflow
- Password: mlflow123
- Database: mlflow

**MinIO:**
- Access Key: minio
- Secret Key: minio123
- Bucket: mlflow

**Change credentials** by editing:
- [postgres/postgres-secret.yaml](postgres/postgres-secret.yaml)
- [minio/minio-secret.yaml](minio/minio-secret.yaml)
- [mlflow/mlflow-config.yaml](mlflow/mlflow-config.yaml)

### Storage

- PostgreSQL PVC: 5Gi
- MinIO PVC: 10Gi

Adjust storage sizes in:
- [postgres/postgres-pvc.yaml](postgres/postgres-pvc.yaml)
- [minio/minio-pvc.yaml](minio/minio-pvc.yaml)

### Service Types

- **PostgreSQL**: ClusterIP (internal only)
- **MinIO**: ClusterIP (internal only)
- **MLflow**: LoadBalancer (external access)

# Kafka logs
kubectl logs -f kafka-0 -n mlops

# Airflow webserver logs
kubectl logs -f deployment/airflow-webserver -n mlops

# Airflow scheduler logs
kubectl logs -f deployment/airflow-scheduler -n mlops

For production, consider using Ingress for external access instead of LoadBalancer.

## Monitoring

Check all pods:
```bash
kubectl get pods -n mlops
```

View logs:
```bash
# MLflow logs
kubectl logs -f deployment/mlflow -n mlops

# PostgreSQL logs
kubectl logs -f deployment/postgres -n mlops

# MinIO logs
kubectl logs -f deployment/minio -n mlops
```

Check services:
```bash
kubectl get svc -n mlops
```

Check persistent volumes:
```bash
kubectl get pvc -n mlops
```

## Troubleshooting

### Pods not starting
```bash
kubectl describe pod <pod-name> -n mlops
kubectl logs <pod-name> -n mlops
```

### Connection issues
Ensure all services are running:
```bash
kubectl get all -n mlops
```

### Storage issues
Check if PVCs are bound:
```bash
kubectl get pvc -n mlops
```

### Reset everything
```bash
./teardown.sh
kubectl delete namespace mlops
./deploy.sh
```

## Production Considerations

1. **Security:**
   - Change default passwords
   - Use Kubernetes Secrets with encryption at rest
   - Implement RBAC
   - Use network policies

2. **High Availability:**
   - Deploy PostgreSQL with replicas or use managed database
   - Deploy MinIO in distributed mode or use S3
   - Increase MLflow replicas

3. **Backup:**
   - Implement backup strategy for PostgreSQL
   - Configure MinIO bucket versioning
   - Use volume snapshots

4. **Monitoring:**
   - Add Prometheus metrics
   - Configure alerts
   - Set up logging aggregation

5. **Ingress:**
   - Replace LoadBalancer with Ingress
   - Configure TLS/SSL certificates
   - Set up proper DNS

## Using MLflow from Applications

### Python Example
```python
import mlflow
import os

# Set tracking URI
os.environ['MLFLOW_TRACKING_URI'] = 'http://localhost:5000'

# For S3 artifact storage (when running outside cluster)
os.environ['AWS_ACCESS_KEY_ID'] = 'minio'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'minio123'
os.environ['MLFLOW_S3_ENDPOINT_URL'] = 'http://localhost:9000'

# Start MLflow run
mlflow.set_experiment("my-experiment")
with mlflow.start_run():
    mlflow.log_param("param1", 5)
    mlflow.log_metric("metric1", 0.85)
```

### From Inside Cluster
```python
import os

os.environ['MLFLOW_TRACKING_URI'] = 'http://mlflow.mlops.svc.cluster.local:5000'
os.environ['AWS_ACCESS_KEY_ID'] = 'minio'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'minio123'
os.environ['MLFLOW_S3_ENDPOINT_URL'] = 'http://minio.mlops.svc.cluster.local:9000'
```

## Directory Structure

```
k8s/
├── namespace.yaml                  # MLOps namespace definition
├── deploy.sh                       # Automated MLOps deployment script
├── teardown.sh                     # Automated MLOps teardown script
├── deploy-dashboard.sh             # Kubernetes Dashboard deployment script
├── teardown-dashboard.sh           # Kubernetes Dashboard teardown script
├── README.md                       # This file
├── postgres/
│   ├── postgres-secret.yaml        # PostgreSQL credentials
│   ├── postgres-pvc.yaml           # PostgreSQL storage
│   ├── postgres-deployment.yaml    # PostgreSQL deployment
│   └── postgres-service.yaml       # PostgreSQL service
├── minio/
│   ├── kafka-ui-deployment.yaml    # Kafka UI deployment
│   ├── kafka-ui-service.yaml       # Kafka UI service
│   └── README.md                   # Kafka documentation
├── airflow/
│   ├── airflow-rbac.yaml           # Airflow RBAC configuration
│   ├── airflow-secret.yaml         # Airflow secrets
│   ├── airflow-passwords.yaml      # Airflow user passwords (persisted)
│   ├── airflow-config.yaml         # Airflow configuration
│   ├── airflow-pvc.yaml            # Airflow storage (DAGs & logs)
│   ├── airflow-postgres.yaml       # Airflow PostgreSQL database
│   ├── airflow-scheduler.yaml      # Airflow scheduler deployment
│   ├── airflow-webserver.yaml      # Airflow webserver deployment
│   ├── Dockerfile                  # Custom Airflow 3.x image
│   ├── CREDENTIALS.md              # Airflow authentication guide
│   └── README.md                   # Airflow credentials
│   ├── minio-pvc.yaml              # MinIO storage
│   ├── minio-deployment.yaml       # MinIO deployment
│   ├── minio-service.yaml          # MinIO service
│   └── minio-bucket-job.yaml       # Job to create mlflow bucket
├── mlflow/
│   ├── mlflow-config.yaml          # MLflow configuration
│   ├── mlflow-deployment.yaml      # MLflow deployment
│   ├── mlflow-service.yaml         # MLflow service
│   ├── Dockerfile                  # Custom MLflow image with dependencies
│   └── README.md                   # MLflow documentation
├── kafka/
│   ├── kafka-config.yaml           # Kafka cluster configuration
│   ├── kafka-statefulset.yaml      # Kafka StatefulSet (3 brokers)
│   ├── kafka-service.yaml          # Kafka services
│   └── README.md                   # Kafka documentation
└── dashboard/
    ├── dashboard-namespace.yaml    # Dashboard namespace
    ├── dashboard-serviceaccount.yaml # Service accounts
    ├── dashboard-rbac.yaml         # RBAC permissions
    ├── dashboard-secret.yaml       # Dashboard secrets
    ├── dashboard-configmap.yaml    # Dashboard configuration
    ├── dashboard-deployment.yaml   # Dashboard deployment
    ├── dashboard-service.yaml      # Dashboard service
    └── README.md                   # Dashboard documentation
```
