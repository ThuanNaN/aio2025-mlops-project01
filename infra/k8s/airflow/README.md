# Apache Airflow Deployment

This directory contains Kubernetes manifests for deploying Apache Airflow 2.8.1 with KubernetesExecutor.

## Architecture

- **Executor**: KubernetesExecutor (no Celery or Redis required)
- **Database**: PostgreSQL 15 for metadata storage
- **Storage**: Persistent volumes for DAGs and logs
- **Components**:
  - Airflow Webserver (UI and API)
  - Airflow Scheduler (orchestration)
  - PostgreSQL (metadata database)
  - Dynamic worker pods (created per task)

## Files

- `airflow-secret.yaml` - Credentials for PostgreSQL, Airflow admin, and encryption keys
- `airflow-config.yaml` - Airflow configuration settings
- `airflow-pvc.yaml` - Persistent volume claims for DAGs, logs, and database
- `airflow-postgres.yaml` - PostgreSQL database deployment and service
- `airflow-webserver.yaml` - Airflow webserver deployment and LoadBalancer service
- `airflow-scheduler.yaml` - Airflow scheduler deployment
- `airflow-rbac.yaml` - ServiceAccount, Role, and RoleBinding for Kubernetes access

## Deployment

### Quick Start

```bash
# From the infra/k8s directory
./deploy-airflow.sh
```

### Manual Deployment

```bash
# Apply in order
kubectl apply -f airflow/airflow-rbac.yaml
kubectl apply -f airflow/airflow-secret.yaml
kubectl apply -f airflow/airflow-config.yaml
kubectl apply -f airflow/airflow-pvc.yaml
kubectl apply -f airflow/airflow-postgres.yaml

# Wait for PostgreSQL
kubectl wait --for=condition=ready pod -l app=airflow-postgres -n mlops --timeout=300s

# Deploy Airflow components
kubectl apply -f airflow/airflow-scheduler.yaml
kubectl apply -f airflow/airflow-webserver.yaml

# Wait for webserver
kubectl wait --for=condition=ready pod -l app=airflow-webserver -n mlops --timeout=300s
```

## Access

### Get Service Information

```bash
kubectl get svc airflow-webserver -n mlops
```

### Access Web UI

**Option 1: LoadBalancer (if available)**
```bash
# Get external IP
EXTERNAL_IP=$(kubectl get svc airflow-webserver -n mlops -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
echo "Airflow UI: http://${EXTERNAL_IP}:8080"
```

**Option 2: Port Forward**
```bash
kubectl port-forward svc/airflow-webserver -n mlops 8080:8080
# Access at http://localhost:8080
```

### Login Credentials

- **Username**: `admin`
- **Password**: `admin123`

## Adding DAGs

### Method 1: Copy from Local to Pod

```bash
# Get webserver pod name
POD_NAME=$(kubectl get pod -l app=airflow-webserver -n mlops -o jsonpath='{.items[0].metadata.name}')

# Copy DAGs directory
kubectl cp ../../../data_pipeline/airflow/dags/ $POD_NAME:/opt/airflow/dags/ -n mlops

# Verify
kubectl exec -it $POD_NAME -n mlops -- ls -la /opt/airflow/dags/
```

### Method 2: Mount from Local (Development)

For development, you can modify the PVC to use a local path or NFS:

```bash
# Edit airflow-pvc.yaml to add hostPath or NFS configuration
# Then redeploy the PVC and pods
```

### Method 3: Git-sync Sidecar (Production)

Add a git-sync sidecar container to sync DAGs from a Git repository (see example below).

## Configuration

### Environment Variables

All configuration is managed through:
- `airflow-config.yaml` - ConfigMap for Airflow settings
- `airflow-secret.yaml` - Secret for credentials and keys

### Key Settings

- **Executor**: KubernetesExecutor (tasks run in dynamic pods)
- **Namespace**: mlops (worker pods created here)
- **Worker Image**: apache/airflow:2.8.1-python3.11
- **Worker Pod Cleanup**: Enabled (successful pods deleted)
- **Failed Pod Retention**: Enabled (for debugging)

### Database Connection

PostgreSQL connection string:
```
postgresql+psycopg2://airflow:airflow123@airflow-postgres:5432/airflow
```

## Monitoring

### Check Component Status

```bash
# All Airflow components
kubectl get all -l app.kubernetes.io/component=airflow -n mlops

# Webserver
kubectl get pods -l app=airflow-webserver -n mlops

# Scheduler
kubectl get pods -l app=airflow-scheduler -n mlops

# Database
kubectl get pods -l app=airflow-postgres -n mlops

# Worker pods (dynamic)
kubectl get pods -l airflow-worker=true -n mlops
```

### View Logs

```bash
# Webserver logs
kubectl logs -l app=airflow-webserver -n mlops -f

# Scheduler logs
kubectl logs -l app=airflow-scheduler -n mlops -f

# Specific worker logs
kubectl logs <worker-pod-name> -n mlops
```

### Access Database

```bash
# Port forward to PostgreSQL
kubectl port-forward svc/airflow-postgres -n mlops 5432:5432

# Connect with psql
PGPASSWORD=airflow123 psql -h localhost -U airflow -d airflow
```

## Troubleshooting

### Webserver Not Starting

```bash
# Check logs
kubectl logs -l app=airflow-webserver -n mlops

# Common issues:
# - Database not ready: Wait for PostgreSQL to be healthy
# - Init container failed: Check database credentials
# - Fernet key invalid: Generate new key with Python script
```

### Scheduler Not Processing DAGs

```bash
# Check scheduler logs
kubectl logs -l app=airflow-scheduler -n mlops

# Verify DAGs are present
kubectl exec -it $(kubectl get pod -l app=airflow-scheduler -n mlops -o jsonpath='{.items[0].metadata.name}') -n mlops -- ls -la /opt/airflow/dags/

# Check for DAG parsing errors in UI or logs
```

### Worker Pods Not Starting

```bash
# Check RBAC permissions
kubectl auth can-i create pods --as=system:serviceaccount:mlops:airflow -n mlops

# Check scheduler logs for task launch errors
kubectl logs -l app=airflow-scheduler -n mlops | grep -i error

# Verify worker pod events
kubectl get events -n mlops --sort-by='.lastTimestamp'
```

### Database Connection Issues

```bash
# Test PostgreSQL connectivity
kubectl exec -it $(kubectl get pod -l app=airflow-postgres -n mlops -o jsonpath='{.items[0].metadata.name}') -n mlops -- pg_isready -U airflow

# Check service
kubectl get svc airflow-postgres -n mlops

# Test connection from webserver
kubectl exec -it $(kubectl get pod -l app=airflow-webserver -n mlops -o jsonpath='{.items[0].metadata.name}') -n mlops -- bash
# Inside pod: psql postgresql://airflow:airflow123@airflow-postgres:5432/airflow
```

## Cleanup

```bash
# From infra/k8s directory
./teardown-airflow.sh
```

Or manually:
```bash
kubectl delete -f airflow/
```

## Advanced Configuration

### Add Python Dependencies

Create a custom Dockerfile:

```dockerfile
FROM apache/airflow:2.8.1-python3.11

USER root
# Install system dependencies if needed
RUN apt-get update && apt-get install -y <packages>

USER airflow
# Install Python packages
COPY requirements.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt
```

Build and push:
```bash
docker build -t your-registry/airflow:3.1.5-custom .
docker push your-registry/airflow:3.1.5-custom
```

Update `airflow-config.yaml`:
```yaml
AIRFLOW__KUBERNETES_EXECUTOR__WORKER_CONTAINER_REPOSITORY: "your-registry/airflow"
AIRFLOW__KUBERNETES_EXECUTOR__WORKER_CONTAINER_TAG: "3.1.5-custom"
```

### Git-sync for DAGs

Add sidecar to webserver and scheduler:

```yaml
- name: git-sync
  image: registry.k8s.io/git-sync/git-sync:v4.0.0
  env:
  - name: GIT_SYNC_REPO
    value: "https://github.com/your-org/airflow-dags.git"
  - name: GIT_SYNC_BRANCH
    value: "main"
  - name: GIT_SYNC_ROOT
    value: "/opt/airflow/dags"
  - name: GIT_SYNC_DEST
    value: "repo"
  - name: GIT_SYNC_WAIT
    value: "60"
  volumeMounts:
  - name: dags
    mountPath: /opt/airflow/dags
```

## Integration with Other Services

### Connect to Kafka

Airflow DAGs can produce/consume from the Kafka cluster:

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from kafka import KafkaProducer

def send_to_kafka():
    producer = KafkaProducer(
        bootstrap_servers=[
            'kafka-0.kafka-headless.mlops.svc.cluster.local:9092',
            'kafka-1.kafka-headless.mlops.svc.cluster.local:9092',
            'kafka-2.kafka-headless.mlops.svc.cluster.local:9092'
        ]
    )
    producer.send('my-topic', b'Hello from Airflow')
    producer.flush()
```

### Connect to MLflow

Track experiments from Airflow tasks:

```python
import mlflow

mlflow.set_tracking_uri("http://mlflow.mlops.svc.cluster.local:5000")

with mlflow.start_run():
    mlflow.log_param("param1", 5)
    mlflow.log_metric("accuracy", 0.95)
```

### Use MinIO for XCom Backend

Configure Airflow to use MinIO for large XCom data:

```yaml
# In airflow-config.yaml
AIRFLOW__CORE__XCOM_BACKEND: "airflow.providers.amazon.aws.xcom_backends.s3.S3XComBackend"
AIRFLOW__CORE__XCOM_S3_BUCKET: "airflow-xcom"
AIRFLOW__CORE__XCOM_S3_ENDPOINT_URL: "http://minio.mlops.svc.cluster.local:9000"
AWS_ACCESS_KEY_ID: "minioadmin"
AWS_SECRET_ACCESS_KEY: "minioadmin"
```

## Security Notes

⚠️ **Important**: The default credentials in this deployment are for development only.

For production:
1. Change all passwords in `airflow-secret.yaml`
2. Generate new Fernet key: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
3. Generate new secret key: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
4. Use external secrets management (e.g., HashiCorp Vault)
5. Enable SSL/TLS for database connections
6. Configure authentication provider (LDAP, OAuth, etc.)
7. Use private container registry
8. Enable network policies
