#!/bin/bash

set -e

# Configuration
IMAGE_NAME="airflow-mlops"
IMAGE_TAG="3.1.5-custom"
REGISTRY="${DOCKER_REGISTRY:-localhost:5000}"  # Change to your registry

FULL_IMAGE="${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"

echo "======================================"
echo "Building Custom Airflow Image"
echo "======================================"
echo "Image: ${FULL_IMAGE}"
echo ""

# Build the image
echo "Building Docker image..."
docker build -t ${FULL_IMAGE} -f airflow/Dockerfile airflow/

echo ""
echo "======================================"
echo "Build complete!"
echo "======================================"
echo ""
echo "To push to registry:"
echo "  docker push ${FULL_IMAGE}"
echo ""
echo "To use in Kubernetes:"
echo "  Update airflow-config.yaml:"
echo "    AIRFLOW__KUBERNETES_EXECUTOR__WORKER_CONTAINER_REPOSITORY: \"${REGISTRY}/${IMAGE_NAME}\""
echo "    AIRFLOW__KUBERNETES_EXECUTOR__WORKER_CONTAINER_TAG: \"${IMAGE_TAG}\""
echo ""
echo "  Update airflow-webserver.yaml and airflow-scheduler.yaml:"
echo "    image: ${FULL_IMAGE}"
echo ""
