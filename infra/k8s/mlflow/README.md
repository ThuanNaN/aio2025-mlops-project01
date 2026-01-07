# MLflow with PostgreSQL and MinIO

This directory contains the MLflow tracking server configuration with PostgreSQL backend and MinIO artifact storage.

## Issue Fixed: Missing PostgreSQL Driver

The default MLflow Docker image doesn't include the PostgreSQL driver (`psycopg2`). The deployment has been configured to install required dependencies at runtime.

### Current Solution

The deployment uses an init process that installs dependencies before starting MLflow:
- `psycopg2-binary` - PostgreSQL database driver
- `boto3` - AWS SDK for S3/MinIO compatibility

### Alternative: Custom Docker Image

For production use, it's recommended to build a custom Docker image with pre-installed dependencies.

#### Build Custom Image

```bash
# Build the image locally
./build-mlflow-image.sh

# For minikube
minikube image build -t mlflow-postgres:latest -f mlflow/Dockerfile mlflow/

# For Docker Desktop with Kubernetes
docker build -t mlflow-postgres:latest -f mlflow/Dockerfile mlflow/

# Update deployment to use the custom image
kubectl set image deployment/mlflow mlflow=mlflow-postgres:latest -n mlops
```

#### Build and Push to Registry

```bash
# Build for a registry
./build-mlflow-image.sh myapp/mlflow-postgres v1.0.0 docker.io

# Push to registry
docker push docker.io/myapp/mlflow-postgres:v1.0.0

# Update mlflow-deployment.yaml
# Change: image: ghcr.io/mlflow/mlflow:v2.15.0
# To:     image: docker.io/myapp/mlflow-postgres:v1.0.0
```

## Configuration

### Environment Variables

Set via [mlflow-config.yaml](mlflow-config.yaml):
- `AWS_ACCESS_KEY_ID`: MinIO access key (minio)
- `AWS_SECRET_ACCESS_KEY`: MinIO secret key (minio123)
- `MLFLOW_S3_ENDPOINT_URL`: MinIO endpoint (http://minio:9000)

### Backend Store

PostgreSQL database connection:
```
postgresql://mlflow:mlflow123@postgres:5432/mlflow
```

### Artifact Store

MinIO S3-compatible storage:
```
s3://mlflow/
```

## Verify Installation

```bash
# Check pods
kubectl get pods -n mlops

# Check logs
kubectl logs deployment/mlflow -n mlops

# Port forward to access UI
kubectl port-forward svc/mlflow -n mlops 5000:5000

# Test health endpoint
curl http://localhost:5000/health
```

## Usage from Python

```python
import mlflow
import os

# Set tracking URI
os.environ['MLFLOW_TRACKING_URI'] = 'http://localhost:5000'

# For S3 artifact storage
os.environ['AWS_ACCESS_KEY_ID'] = 'minio'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'minio123'
os.environ['MLFLOW_S3_ENDPOINT_URL'] = 'http://localhost:9000'

# Start experiment
mlflow.set_experiment("my-experiment")
with mlflow.start_run():
    mlflow.log_param("param1", 5)
    mlflow.log_metric("metric1", 0.85)
```

## Troubleshooting

### CrashLoopBackOff

If you see `CrashLoopBackOff`:

```bash
# Check logs
kubectl logs <pod-name> -n mlops

# Common issues:
# 1. Missing psycopg2 - Fixed in current deployment
# 2. Cannot connect to PostgreSQL - Check postgres pod status
# 3. Cannot connect to MinIO - Check minio pod status
```

### Database Connection Issues

```bash
# Test PostgreSQL connection
kubectl exec -it deployment/postgres -n mlops -- psql -U mlflow -d mlflow -c "SELECT 1;"

# Check PostgreSQL logs
kubectl logs deployment/postgres -n mlops
```

### S3/MinIO Connection Issues

```bash
# Check MinIO is running
kubectl get pods -l app=minio -n mlops

# Test MinIO connectivity
kubectl run -it --rm test-minio --image=minio/mc --restart=Never -- \
  mc alias set myminio http://minio:9000 minio minio123

# List buckets
kubectl run -it --rm test-minio --image=minio/mc --restart=Never -- \
  mc ls myminio/
```

## Files

- `mlflow-config.yaml` - Environment configuration for S3/MinIO
- `mlflow-deployment.yaml` - MLflow deployment with dependency installation
- `mlflow-service.yaml` - LoadBalancer service
- `Dockerfile` - Custom image with pre-installed dependencies
- `README.md` - This file
