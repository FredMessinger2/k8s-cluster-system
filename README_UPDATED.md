# K8s Cluster Management System

A distributed system for monitoring and visualizing Kubernetes clusters with Java-based cluster management, Python applications communicating via NATS, and a web-based UI.

## Project Structure
```
k8s-cluster-system/
├── java-app/               # Java Kubernetes manager (Gradle + no Spring)
│   ├── build.gradle        # Build configuration
│   ├── quick-build.sh      # Docker-based build script
│   └── src/main/java/      # Java source code
├── python-apps/            # Python applications using NATS
│   ├── app1/               # Python application 1
│   ├── app2/               # Python application 2
│   └── app3/               # Python application 3
├── ui/                     # Browser-based visualization
│   └── index.html          # D3.js cluster visualization
├── k8s-manifests/          # Kubernetes deployment files
│   ├── nats.yaml
│   ├── java-app-rbac.yaml
│   ├── java-app-deployment.yaml
│   └── python-app*.yaml
└── scripts/                # Build and deployment scripts
```

## Prerequisites

**Required:**
- Docker
- Minikube
- kubectl

**Notes:**
- Java 17+ NOT required locally (uses Docker for builds)
- Python 3.11+ NOT required locally (uses containerized builds)
- Gradle NOT required locally (uses Docker-based builds)

## Quick Start (Fresh Machine)

### 1. Start Infrastructure
```bash
# Start minikube with adequate resources
minikube start --driver=docker --cpus=4 --memory=4096

# CRITICAL: Configure Docker to use minikube's daemon
eval $(minikube docker-env)

# Verify cluster is ready
kubectl get nodes
```

### 2. Navigate to Project and Build Applications
```bash
# Go to project directory
cd /path/to/k8s-cluster-system

# Build Java application (Docker-based, no local Java needed)
cd java-app
./quick-build.sh
cd ..

# Build Python applications
cd python-apps/app1
docker build -t python-k8s-app1:latest .
cd ../app2
docker build -t python-k8s-app2:latest .
cd ../app3
docker build -t python-k8s-app3:latest .
cd ../..
```

### 3. Deploy to Kubernetes (In Order)
```bash
# Deploy NATS message bus first
kubectl apply -f k8s-manifests/nats.yaml

# Deploy RBAC for Java app
kubectl apply -f k8s-manifests/java-app-rbac.yaml

# Deploy Java application
kubectl apply -f k8s-manifests/java-app-deployment.yaml

# Deploy Python applications
kubectl apply -f k8s-manifests/python-app1-deployment.yaml
kubectl apply -f k8s-manifests/python-app2-deployment.yaml
kubectl apply -f k8s-manifests/python-app3-deployment.yaml
```

### 4. Wait for Deployments
```bash
# Wait for all pods to be ready
kubectl wait --for=condition=Ready pod --all --timeout=300s

# Verify all pods are running
kubectl get pods
```

### 5. Access the System
```bash
# Start port forwarding
kubectl port-forward svc/k8s-manager-service 8080:8080 &

# Wait for connection to establish
sleep 5

# Test API endpoints
curl http://localhost:8080/health
curl -s http://localhost:8080/api/cluster/info | python3 -m json.tool
```

### 6. Open Web UI
```bash
# Serve UI via HTTP (recommended over file:// protocol)
cd ui
python3 -m http.server 3000 &
cd ..

# Open browser to: http://localhost:3000
```

## One-Line Quick Start
```bash
cd /path/to/k8s-cluster-system && minikube start --driver=docker --cpus=4 --memory=4096 && eval $(minikube docker-env) && cd java-app && ./quick-build.sh && cd ../python-apps/app1 && docker build -t python-k8s-app1:latest . && cd ../app2 && docker build -t python-k8s-app2:latest . && cd ../app3 && docker build -t python-k8s-app3:latest . && cd ../.. && kubectl apply -f k8s-manifests/ && kubectl wait --for=condition=Ready pod --all --timeout=300s && kubectl port-forward svc/k8s-manager-service 8080:8080 &
```

## System Access Points

Once running, access the system via:

- **API Health Check**: http://localhost:8080/health
- **Cluster Info API**: http://localhost:8080/api/cluster/info  
- **Web UI**: http://localhost:3000 (if using python HTTP server)
- **Direct UI**: file:///path/to/k8s-cluster-system/ui/index.html

## Verification Commands

```bash
# Check all resources
kubectl get all

# Check pod status
kubectl get pods

# View Java manager logs
kubectl logs -l app=k8s-manager

# View Python app logs
kubectl logs -l app=python-app1

# Test API responses
curl http://localhost:8080/health
curl http://localhost:8080/api/cluster/info
```

## Common Issues and Solutions

### ImagePullBackOff Errors
**Cause**: Docker images built on host instead of minikube
**Solution**: Always run `eval $(minikube docker-env)` before building

### Port Forward Connection Refused
**Cause**: Port forwarding not active or stopped
**Solution**: 
```bash
pkill -f port-forward
kubectl port-forward svc/k8s-manager-service 8080:8080 &
```

### Pod Won't Start - ServiceAccount Not Found
**Cause**: RBAC resources missing
**Solution**: 
```bash
kubectl apply -f k8s-manifests/java-app-rbac.yaml
```

### Java App Startup Errors
**Cause**: Various issues (check logs for specifics)
**Solution**: 
```bash
kubectl logs -l app=k8s-manager
kubectl describe pods -l app=k8s-manager
```

### Build Failures
**Cause**: Missing dependencies or wrong environment
**Solution**: Use Docker-based builds (already configured in quick-build.sh)

## Development Workflow

### Making Changes to Java App
```bash
# Make code changes
# Rebuild with Docker
cd java-app
eval $(minikube docker-env)
./quick-build.sh
cd ..

# Restart deployment
kubectl rollout restart deployment/k8s-manager
```

### Making Changes to Python Apps
```bash
# Make code changes
# Rebuild specific app
cd python-apps/app1
eval $(minikube docker-env)
docker build -t python-k8s-app1:latest .
cd ../..

# Restart deployment
kubectl rollout restart deployment/python-app1
```

## Cleanup

```bash
# Delete all resources
kubectl delete -f k8s-manifests/

# Stop minikube (optional)
minikube stop

# Delete cluster (optional)
minikube delete
```

## Architecture Notes

- **Java Manager**: Runs HTTP server, queries Kubernetes API, provides REST endpoints
- **Python Apps**: Connect to NATS message bus, communicate asynchronously
- **NATS**: Message bus for inter-service communication
- **UI**: D3.js visualization consuming Java manager REST API
- **No Spring**: Uses Java's built-in HTTP server for minimal footprint
- **Docker Builds**: All builds happen in containers to eliminate local dependencies