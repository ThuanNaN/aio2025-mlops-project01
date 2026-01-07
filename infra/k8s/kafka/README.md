# Kafka Cluster (KRaft Mode) with UI

This directory contains Kubernetes manifests for deploying a 3-node Kafka cluster using KRaft mode (no Zookeeper required) with a web-based management UI.

## Architecture

```
┌─────────────────────────────────────────────┐
│           Kafka Cluster (KRaft)             │
├─────────────────────────────────────────────┤
│                                             │
│  ┌───────────┐  ┌───────────┐  ┌──────────┐ │
│  │  kafka-0  │  │  kafka-1  │  │  kafka-2 │ │
│  │  Node 1   │  │  Node 2   │  │  Node 3  │ │
│  │           │  │           │  │          │ │
│  │ Port:9092 │  │ Port:9092 │  │Port:9092 │ │
│  │ Ctrl:9093 │  │ Ctrl:9093 │  │Ctrl:9093 │ │
│  │ Int: 9094 │  │ Int: 9094 │  │Int: 9094 │ │
│  └─────┬─────┘  └─────┬─────┘  └────┬─────┘ │
│        │              │             │       │
│        └──────────────┼─────────────┘       │
│                       │                     │
│              [Quorum Communication]         │
│                       │                     │
│                  ┌────▼─────┐               │
│                  │ Kafka UI │               │ 
│                  │ Port:8080│               │
│                  └──────────┘               │
│                                             │
│  Storage: 10Gi PVC per broker               │
└─────────────────────────────────────────────┘
```

## Features

- **Kafka UI**: Web-based interface for managing Kafka (browse topics, messages, consumers, etc.)

- **KRaft Mode**: No Zookeeper dependency (Kafka 3.0+)
- **3-Node Cluster**: High availability with quorum-based consensus
- **Combined Mode**: Each node acts as both controller and broker
- **Persistent Storage**: 10Gi PVC per broker
- **Internal Communication**: Secure inter-broker communication
- **External Access**: LoadBalancer services for each broker

## Configuration

### Cluster Settings
- **Cluster ID**: 1
- **Node IDs**: 1, 2, 3 (auto-assigned via pod index)
- **Quorum**: All 3 nodes participate in controller quorum

### Listeners
- **PLAINTEXT** (9092): Client connections
- **CONTROLLER** (9093): Controller quorum communication
- **INTERNAL** (9094): Inter-broker communication

### Storage
- **10Gi** per broker
- Persistent volumes automatically created via StatefulSet

## Deployment

### Using Main Deploy Script

The Kafka cluster is included in the main deployment:

```bash
cd infra/k8s
./deploy.sh
```

### Manual Deployment

```bash
# Create ConfigMap
kubectl apply -f kafka/kafka-config.yaml

# Deploy StatefulSet
kubectl apply -f kafka/kafka-statefulset.yaml

# Create Services
kubectl apply -f kafka/kafka-service.yaml

# Deploy Kafka UI
kubectl apply -f kafka/kafka-ui-deployment.yaml
kubectl apply -f kafka/kafka-ui-service.yaml

# Wait for Kafka to be ready
kubectl wait --for=condition=ready pod -l app=kafka -n mlops --timeout=180s

# Wait for Kafka UI to be ready
kubectl wait --for=condition=ready pod -l app=kafka-ui -n mlops --timeout=120s
```

# Create Services
kubectl apply -f kafka/kafka-service.yaml

# Wait for Kafka to be ready
kubectl wait --for=condition=ready pod -l app=kafka -n mlops --timeout=180s
```

## Verify Installation

```bash
# Check pods
kubectl get pods -l app=kafka -n mlops
kubectl get pods -l app=kafka-ui -n mlops

# Check services
kubectl get svc -l app=kafka -n mlops
kubectl get svc -l app=kafka-ui -n mlops

# Check persistent volumes
kubectl get pvc -l app=kafka -n mlops

# View logs from broker 0
kubectl logs kafka-0 -n mlops

# View Kafka UI logs
kubectl logs -l app=kafka-ui -n mlops

# Check cluster status
kubectl exec -it kafka-0 -n mlops -- kafka-broker-api-versions --bootstrap-server localhost:9092
```

## Access Kafka UI

### Via Port Forward (Recommended for Local Development)

```bash
kubectl port-forward svc/kafka-ui -n mlops 8080:8080
```

Then open http://localhost:8080 in your browser.

### Via LoadBalancer (If Available)

```bash
# Get external IP
kubectl get svc kafka-ui -n mlops

# Access via external IP
# http://<EXTERNAL-IP>:8080
```

### Features Available in UI

- **Brokers**: View broker status, configurations, and metrics
- **Topics**: Browse, create, and delete topics
- **Consumers**: Monitor consumer groups and lag
- **Messages**: Browse and search messages in topics
- **Schema Registry**: Manage schemas (if configured)
- **Connect**: Manage Kafka Connect clusters (if configured)


## Access Kafka

### From Inside Cluster

```bash
# Bootstrap servers
kafka-0.kafka-headless.mlops.svc.cluster.local:9092
kafka-1.kafka-headless.mlops.svc.cluster.local:9092
kafka-2.kafka-headless.mlops.svc.cluster.local:9092
```

### From Outside Cluster

```bash
# Get external IPs
kubectl get svc kafka-0 kafka-1 kafka-2 -n mlops

# Connect to broker 0
kafka-console-producer --bootstrap-server <KAFKA-0-EXTERNAL-IP>:9092 --topic test
```

## Usage Examples

### Python Example (kafka-python)

```python
from kafka import KafkaProducer, KafkaConsumer

# Inside cluster
bootstrap_servers = [
    'kafka-0.kafka-headless.mlops.svc.cluster.local:9092',
    'kafka-1.kafka-headless.mlops.svc.cluster.local:9092',
    'kafka-2.kafka-headless.mlops.svc.cluster.local:9092'
]

# Producer
producer = KafkaProducer(bootstrap_servers=bootstrap_servers)
producer.send('my-topic', b'Hello Kafka!')
producer.close()

# Consumer
consumer = KafkaConsumer(
    'my-topic',
    bootstrap_servers=bootstrap_servers,
    auto_offset_reset='earliest',
    group_id='my-group'
)
for message in consumer:
    print(message.value)
```

### Create Topic

```bash
# From inside cluster
kubectl exec -it kafka-0 -n mlops -- kafka-topics \
  --create \
  --topic my-topic \
  --partitions 3 \
  --replication-factor 3 \
  --bootstrap-server localhost:9092

# List topics
kubectl exec -it kafka-0 -n mlops -- kafka-topics \
  --list \
  --bootstrap-server localhost:9092

# Describe topic
kubectl exec -it kafka-0 -n mlops -- kafka-topics \
  --describe \
  --topic my-topic \
  --bootstrap-server localhost:9092
```

### Produce Messages

```bash
kubectl exec -it kafka-0 -n mlops -- kafka-console-producer \
  --bootstrap-server localhost:9092 \
  --topic my-topic
```

### Consume Messages

```bash
kubectl exec -it kafka-0 -n mlops -- kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic my-topic \
  --from-beginning
```

## Monitoring

### Check Cluster Metadata

```bash
kubectl exec -it kafka-0 -n mlops -- kafka-metadata \
  --snapshot /var/lib/kafka/data/__cluster_metadata-0/00000000000000000000.log \
  --print
```

### View Logs

```bash
# All brokers
kubectl logs -l app=kafka -n mlops --tail=50

# Specific broker
kubectl logs kafka-0 -n mlops --tail=100 -f
```

### Check Resource Usage

```bash
kubectl top pods -l app=kafka -n mlops
```

## Scaling

To change the number of brokers:

```bash
# Scale up to 5 brokers
kubectl scale statefulset kafka --replicas=5 -n mlops

# Update quorum voters in ConfigMap
kubectl edit configmap kafka-config -n mlops
# Add: 4@kafka-3.kafka-headless.mlops.svc.cluster.local:9093,5@kafka-4.kafka-headless.mlops.svc.cluster.local:9093
```

**Note**: Scaling down requires careful consideration of data replication.

## Troubleshooting

### Pods not starting

```bash
# Check pod status
kubectl describe pod kafka-0 -n mlops

# Check logs
kubectl logs kafka-0 -n mlops

# Common issues:
# 1. Insufficient resources
# 2. PVC not bound
# 3. Network connectivity
```

### Cannot connect to broker

```bash
# Test connectivity
kubectl exec -it kafka-0 -n mlops -- nc -zv localhost 9092

# Check if broker is registered
kubectl exec -it kafka-0 -n mlops -- kafka-broker-api-versions \
  --bootstrap-server localhost:9092
```

### Controller issues

```bash
# Check controller logs
kubectl logs kafka-0 -n mlops | grep controller

# Verify quorum
kubectl logs kafka-0 -n mlops | grep quorum
```

### Storage issues

```bash
# Check PVC status
kubectl get pvc -l app=kafka -n mlops

# Check available space
kubectl exec -it kafka-0 -n mlops -- df -h /var/lib/kafka/data
```

## Production Considerations

1. **Resources**: Adjust CPU/memory based on workload
2. **Storage**: Increase PVC size for high-throughput workloads
3. **Replication**: Set appropriate replication factors for topics
4. **Monitoring**: Integrate with Prometheus/Grafana
5. **Security**: Enable TLS/SASL authentication
6. **Backup**: Implement topic backup strategy

## Clean Up

```bash
# Delete UI and services
kubectl delete -f kafka/kafka-ui-service.yaml
kubectl delete -f kafka/kafka-ui-deployment.yaml
kubectl delete -f kafka/kafka-service.yaml
kubectl delete -f kafka/kafka-statefulset.yaml
kubectl delete -f kafka/kafka-config.yaml

# Delete PVCs (data will be lost!)
kubectl delete pvc -l app=kafka -n mlops
```

## Files

- `kafka-config.yaml` - Shared configuration (Cluster ID, quorum voters)
- `kafka-statefulset.yaml` - StatefulSet with 3 replicas
- `kafka-service.yaml` - Headless service + LoadBalancer per broker
- `kafka-ui-deployment.yaml` - Kafka UI deployment
- `kafka-ui-service.yaml` - Kafka UI LoadBalancer service
- `README.md` - This file
