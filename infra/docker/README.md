# Docker Infrastructure

This directory contains Docker Compose configurations for all platform services required for the MLOps project. The infrastructure includes workflow orchestration, experiment tracking, message streaming, and monitoring capabilities.

## 📋 Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Services](#services)
- [Quick Start](#quick-start)
- [Individual Service Management](#individual-service-management)
- [Configuration](#configuration)
- [Access URLs](#access-urls)
- [Troubleshooting](#troubleshooting)

## Overview

The platform consists of four main service stacks:

1. **MLflow** - Experiment tracking and model registry
2. **Kafka** - Event streaming and message broker
3. **Monitor** - Observability stack (Prometheus, Grafana, Loki)
4. **Airflow** - Workflow orchestration

All services are managed through a unified control script (`run.sh`) that allows you to start, stop, and monitor the entire platform or individual services.

## Prerequisites

Before starting the services, ensure you have:

- Docker Engine 20.10+ installed
- Docker Compose v2.0+ installed
- At least 8GB of available RAM
- At least 20GB of free disk space
- For monitoring GPU metrics: NVIDIA Docker runtime (nvidia-docker2)

**Create the external Docker network:**

```bash
docker network create aio-network
```

This network is used by MLflow and monitoring services to communicate.

## Services

### 🔬 MLflow Stack

**Location:** `mlflow/`

Components:
- **MLflow Server** (Port 5000) - Experiment tracking UI and API
- **MySQL** (Port 3306) - Backend store for MLflow metadata
- **MinIO** (Ports 9000, 9001) - S3-compatible artifact store

**Environment Variables:** Create a `.env` file in `mlflow/`:

```env
MYSQL_DATABASE=mlflow
MYSQL_USER=mlflow
MYSQL_PASSWORD=mlflow
MYSQL_ROOT_PASSWORD=root
AWS_ACCESS_KEY_ID=minio
AWS_SECRET_ACCESS_KEY=minio123
```

**Features:**
- S3-compatible artifact storage with MinIO
- MySQL backend for scalable metadata storage
- Auto-creates MLflow bucket on startup
- CORS enabled for API access

### 📨 Kafka Cluster

**Location:** `kafka/`

Components:
- **3 Kafka Brokers** in KRaft mode (Ports 9092, 9192, 9292)
- Controller quorum for high availability
- Persistent storage volumes

**Features:**
- KRaft mode (no Zookeeper required)
- 3-node cluster for fault tolerance
- Internal and external listeners
- Persistent data storage

**Broker Endpoints:**
- Broker 1: `localhost:9092`
- Broker 2: `localhost:9192`
- Broker 3: `localhost:9292`

### 📊 Monitoring Stack

**Location:** `monitor/`

Components:
- **Grafana** (Port 3000) - Visualization and dashboards
- **Prometheus** (Port 9090) - Metrics collection and storage
- **Loki** (Port 3100) - Log aggregation
- **Node Exporter** (Port 9100) - Host metrics
- **DCGM Exporter** (Port 9400) - NVIDIA GPU metrics

**Features:**
- Centralized logging with Loki
- System metrics monitoring with Prometheus
- GPU monitoring for ML workloads
- Pre-configured Grafana with Loki plugin
- Docker container logging integration

**Default Credentials:**
- Grafana: `admin/admin` (change on first login)

### 🔄 Airflow Stack

**Location:** `airflow/`

Components:
- **Airflow Webserver** (Port 8080) - UI for workflow management
- **Airflow Scheduler** - Triggers and monitors DAGs
- **Airflow Worker** - Executes tasks (Celery executor)
- **Airflow API Server** (Port 8081) - Execution API
- **PostgreSQL** (Port 5432) - Airflow metadata database
- **Redis** (Port 6379) - Celery message broker

**Features:**
- CeleryExecutor for distributed task execution
- JWT authentication for Execution API
- Custom dependencies support
- Mounted DAGs, logs, plugins, and config directories

**Default Credentials:**
- Username: `airflow`
- Password: `airflow`

**Directory Structure:**
```
airflow/
├── dags/        # Your DAG definitions
├── logs/        # Execution logs
├── plugins/     # Custom plugins
└── config/      # Custom airflow.cfg
```

## Quick Start

### Start All Services

```bash
cd infra/docker
chmod +x run.sh
./run.sh up
```

This will start all services (MLflow, Kafka, Monitor, Airflow) in the correct order.

### Stop All Services

```bash
./run.sh down
```

### Restart All Services

```bash
./run.sh restart
```

### Check Service Status

```bash
./run.sh status
```

### Show Help

```bash
./run.sh help
```

## Individual Service Management

You can manage each service independently by navigating to its directory:

### MLflow

```bash
cd mlflow

# Start
docker compose up -d

# Stop
docker compose down

# View logs
docker compose logs -f mlflow_server
```

### Kafka

```bash
cd kafka

# Start
docker compose up -d

# Stop
docker compose down

# View broker logs
docker compose logs -f broker-1
```

### Monitoring

```bash
cd monitor

# Start
docker compose up -d

# Stop
docker compose down

# View Grafana logs
docker compose logs -f grafana
```

### Airflow

```bash
cd airflow

# Start
docker compose up -d

# Stop
docker compose down

# View scheduler logs
docker compose logs -f airflow-scheduler

# Initialize database (first time only)
docker compose run --rm airflow-init
```

## Configuration

### Airflow Customization

**Custom Python Packages:** Edit `airflow/requirements.txt` and rebuild:

```bash
cd airflow
docker compose build
docker compose up -d
```

**Custom Configuration:** Modify `airflow/config/airflow.cfg` and restart services.

### Monitoring Customization

**Prometheus Targets:** Edit `monitor/prometheus/prometheus.yml` to add scrape targets.

**Loki Configuration:** Modify `monitor/loki/config.yml` for log retention and limits.

### MLflow Customization

**Storage Backend:** Modify environment variables in `mlflow/docker-compose.yaml` or `.env` file.

### Kafka Customization

**Broker Configuration:** Add additional environment variables in `kafka/docker-compose.yaml` for tuning.

## Access URLs

After starting the services, access them at:

| Service | URL | Credentials |
|---------|-----|-------------|
| MLflow UI | http://localhost:5000 | N/A |
| MinIO Console | http://localhost:9001 | minio / minio123 |
| Grafana | http://localhost:3000 | admin / admin |
| Prometheus | http://localhost:9090 | N/A |
| Airflow UI | http://localhost:8080 | airflow / airflow |
| Kafka Brokers | localhost:9092, 9192, 9292 | N/A |

## Troubleshooting

### Services Won't Start

1. **Check Docker network exists:**
   ```bash
   docker network ls | grep aio-network
   ```

2. **Check port availability:**
   ```bash
   # Check if ports are already in use
   sudo netstat -tlnp | grep -E ':(3000|5000|8080|9090|9092)'
   ```

3. **Check Docker resources:**
   ```bash
   docker system df
   docker system prune  # Clean up if needed
   ```

### MLflow Connection Issues

1. **Verify MinIO bucket exists:**
   ```bash
   docker exec -it aio_minio_mc mc ls minio/
   ```

2. **Check MySQL connection:**
   ```bash
   docker exec -it aio_mysql mysql -u mlflow -p
   ```

### Airflow DAGs Not Loading

1. **Check DAGs directory permissions:**
   ```bash
   ls -la airflow/dags/
   ```

2. **View scheduler logs:**
   ```bash
   cd airflow
   docker compose logs -f airflow-scheduler
   ```

### Kafka Broker Issues

1. **Check broker status:**
   ```bash
   cd kafka
   docker compose ps
   ```

2. **Test connectivity:**
   ```bash
   # List topics
   docker exec broker-1 kafka-topics --bootstrap-server localhost:9092 --list
   ```

### Monitoring Stack Issues

1. **GPU metrics not showing:**
   - Verify NVIDIA Docker runtime is installed
   - Check DCGM exporter logs:
     ```bash
     docker logs dcgm-exporter
     ```

2. **Logs not appearing in Loki:**
   - Verify Docker logging driver configuration
   - Check Loki health:
     ```bash
     curl http://localhost:3100/ready
     ```

### Resource Issues

If services are consuming too many resources:

1. **Limit Airflow workers:**
   Edit `airflow/docker-compose.yaml` and scale down worker replicas.

2. **Reduce Kafka log retention:**
   Add environment variables to limit log segment retention.

3. **Adjust monitoring retention:**
   Modify Prometheus retention in `monitor/prometheus/prometheus.yml`.

### Clean Start

To completely reset all services and data:

```bash
./run.sh down

# Remove volumes (WARNING: This deletes all data)
cd mlflow && docker compose down -v && cd ..
cd kafka && docker compose down -v && cd ..
cd monitor && docker compose down -v && cd ..
cd airflow && docker compose down -v && cd ..

# Start fresh
./run.sh up
```
