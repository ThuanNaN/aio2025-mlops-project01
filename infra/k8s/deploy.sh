#!/bin/bash

# Deploy MLOps Infrastructure to Kubernetes
# This script deploys PostgreSQL, MinIO, MLflow tracking server, and Kubernetes Dashboard

set -e

echo "🚀 Starting MLOps Infrastructure Deployment..."

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl is not installed. Please install kubectl first."
    exit 1
fi

# Create namespace
echo "📦 Creating namespace..."
kubectl apply -f namespace.yaml

# Deploy PostgreSQL
echo "🐘 Deploying PostgreSQL..."
kubectl apply -f postgres/postgres-secret.yaml
kubectl apply -f postgres/postgres-pvc.yaml
kubectl apply -f postgres/postgres-deployment.yaml
kubectl apply -f postgres/postgres-service.yaml

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
kubectl wait --for=condition=ready pod -l app=postgres -n mlops --timeout=120s

# Deploy MinIO
echo "📦 Deploying MinIO..."
kubectl apply -f minio/minio-secret.yaml
kubectl apply -f minio/minio-pvc.yaml
kubectl apply -f minio/minio-deployment.yaml
kubectl apply -f minio/minio-service.yaml

# Wait for MinIO to be ready
echo "⏳ Waiting for MinIO to be ready..."
kubectl wait --for=condition=ready pod -l app=minio -n mlops --timeout=120s

# Create MinIO bucket
echo "🪣 Creating MinIO bucket..."
kubectl apply -f minio/minio-bucket-job.yaml
kubectl wait --for=condition=complete job/minio-create-bucket -n mlops --timeout=60s

# Deploy MLflow
echo "📊 Deploying MLflow tracking server..."
kubectl apply -f mlflow/mlflow-config.yaml
kubectl apply -f mlflow/mlflow-deployment.yaml
kubectl apply -f mlflow/mlflow-service.yaml

# Wait for MLflow to be ready
echo "⏳ Waiting for MLflow to be ready..."
kubectl wait --for=condition=ready pod -l app=mlflow -n mlops --timeout=180s

# Deploy Kafka Cluster
echo "📨 Deploying Kafka cluster (3 brokers)..."
kubectl apply -f kafka/kafka-config.yaml
kubectl apply -f kafka/kafka-statefulset.yaml
kubectl apply -f kafka/kafka-service.yaml

# Wait for Kafka to be ready
echo "⏳ Waiting for Kafka cluster to be ready..."
kubectl wait --for=condition=ready pod -l app=kafka -n mlops --timeout=180s

# Deploy Kafka UI
echo "🖥️  Deploying Kafka UI..."
kubectl apply -f kafka/kafka-ui-deployment.yaml
kubectl apply -f kafka/kafka-ui-service.yaml

# Wait for Kafka UI to be ready
echo "⏳ Waiting for Kafka UI to be ready..."
kubectl wait --for=condition=ready pod -l app=kafka-ui -n mlops --timeout=120s

# Deploy Kubernetes Dashboard
echo "🎛️  Deploying Kubernetes Dashboard..."
kubectl apply -f dashboard/dashboard-namespace.yaml
kubectl apply -f dashboard/dashboard-serviceaccount.yaml
kubectl apply -f dashboard/dashboard-rbac.yaml
kubectl apply -f dashboard/dashboard-secret.yaml
kubectl apply -f dashboard/dashboard-configmap.yaml
kubectl apply -f dashboard/dashboard-deployment.yaml
kubectl apply -f dashboard/dashboard-service.yaml

# Wait for Dashboard to be ready
echo "⏳ Waiting for Kubernetes Dashboard to be ready..."
kubectl wait --for=condition=ready pod -l k8s-app=kubernetes-dashboard -n kubernetes-dashboard --timeout=120s

# Create admin token
echo ""
echo "🔑 Creating dashboard admin token..."
TOKEN=$(kubectl -n kubernetes-dashboard create token admin-user --duration=87600h 2>/dev/null || echo "")

if [ -z "$TOKEN" ]; then
    echo "⚠️  Token creation failed. Creating token using Secret method..."
    
    cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Secret
metadata:
  name: admin-user-token
  namespace: kubernetes-dashboard
  annotations:
    kubernetes.io/service-account.name: admin-user
type: kubernetes.io/service-account-token
EOF
    
    sleep 2
    TOKEN=$(kubectl get secret admin-user-token -n kubernetes-dashboard -o jsonpath='{.data.token}' | base64 --decode)
fi

if [ -n "$TOKEN" ]; then
    echo "$TOKEN" > dashboard-token.txt
    echo "💾 Token saved to: dashboard-token.txt"
fi

echo ""
echo "✅ MLOps Infrastructure deployed successfully!"
echo ""
echo "📋 Deployment Summary:"
echo "  - Namespace: mlops"
echo "  - PostgreSQL: postgres.mlops.svc.cluster.local:5432"
echo "  - MinIO API: minio.mlops.svc.cluster.local:9000"
echo "  - MinIO Console: minio.mlops.svc.cluster.local:9001"
echo "  - MLflow: mlflow.mlops.svc.cluster.local:5000"
echo "  - Kafka Cluster: kafka-0, kafka-1, kafka-2 (port 9092)"
echo "  - Kafka UI: kafka-ui.mlops.svc.cluster.local:8080"
echo "  - Airflow: airflow-webserver.mlops.svc.cluster.local:8080"
echo "  - Kubernetes Dashboard: kubernetes-dashboard namespace"
echo ""
echo "🔍 To check the status of all pods:"
echo "  kubectl get pods -n mlops"
echo "  kubectl get pods -n kubernetes-dashboard"
echo ""
echo "🌐 To access MLflow UI:"
echo "  kubectl port-forward svc/mlflow -n mlops 5000:5000"
echo "  Then open http://localhost:5000"
echo ""
echo "🌐 To access MinIO Console:"
echo "  kubectl port-forward svc/minio -n mlops 9001:9001"
echo "  Then open http://localhost:9001"
echo "  Login: minio / minio123"
echo ""
echo "📨 To access Kafka brokers:"
echo "  kafka-0.kafka-headless.mlops.svc.cluster.local:9092"
echo "  kafka-1.kafka-headless.mlops.svc.cluster.local:9092"
echo "  kafka-2.kafka-headless.mlops.svc.cluster.local:9092"
echo ""
echo "🖥️  To access Kafka UI:"
echo "  kubectl port-forward svc/kafka-ui -n mlops 8080:8080"
echo "  Then open http://localhost:8080"
echo ""

# Deploy Airflow
echo "✈️  Deploying Apache Airflow..."
kubectl apply -f airflow/airflow-rbac.yaml
kubectl apply -f airflow/airflow-secret.yaml
kubectl apply -f airflow/airflow-passwords.yaml
kubectl apply -f airflow/airflow-config.yaml
kubectl apply -f airflow/airflow-pvc.yaml
kubectl apply -f airflow/airflow-postgres.yaml

# Wait for Airflow PostgreSQL to be ready
echo "⏳ Waiting for Airflow PostgreSQL to be ready..."
kubectl wait --for=condition=ready pod -l app=airflow-postgres -n mlops --timeout=300s

# Deploy Airflow components
kubectl apply -f airflow/airflow-scheduler.yaml
kubectl apply -f airflow/airflow-webserver.yaml

# Wait for Airflow to be ready
echo "⏳ Waiting for Airflow to be ready..."
kubectl wait --for=condition=ready pod -l app=airflow-webserver -n mlops --timeout=300s

echo ""
echo "🎛️  To access Kubernetes Dashboard:"
echo "  kubectl proxy"
echo "  Then open: http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/"
echo "  OR use: kubectl port-forward -n kubernetes-dashboard service/kubernetes-dashboard 8443:443"
echo "  Then open: https://localhost:8443"
echo ""
if [ -f "dashboard-token.txt" ]; then
    echo "🔑 Dashboard Token (for login):"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    cat dashboard-token.txt
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
fi
echo ""
echo "✈️  To access Airflow UI:"
echo "  kubectl port-forward svc/airflow-webserver -n mlops 8080:8080"
echo "  Then open http://localhost:8080"
echo "  Login: admin / admin123"
echo ""
echo "✅ Deployment complete!"
