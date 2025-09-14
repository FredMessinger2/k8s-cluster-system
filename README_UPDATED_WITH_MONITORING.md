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
- **Cache Statistics**: http://localhost:8080/api/cache/stats
- **Cache Refresh**: POST http://localhost:8080/api/cache/refresh
- **NATS Publish**: POST http://localhost:8080/api/nats/publish
- **Web UI**: http://localhost:3000 (if using python HTTP server)
- **Direct UI**: file:///path/to/k8s-cluster-system/ui/index.html

## Dynamic Monitoring

The system includes several options for real-time monitoring of your Kubernetes cluster:

### Simple Auto-Refreshing Displays
```bash
# Basic watch command - updates every 2 seconds
watch -n 2 kubectl get pods

# With color output
watch -n 2 --color kubectl get pods

# Show more details
watch -n 2 'kubectl get pods -o wide'
```

### Continuous Streaming Updates
```bash
# Stream pod changes as they happen
kubectl get pods --watch

# With timestamps
kubectl get pods --watch --output-watch-events

# Watch all resources
kubectl get all --watch
```

### Custom Monitor Scripts

#### Basic Pod Monitor
```bash
cat > pod-monitor.sh << 'EOF'
#!/bin/bash
while true; do
    clear
    echo "=== KUBERNETES POD MONITOR ==="
    echo "Timestamp: $(date)"
    echo ""
    
    # Pod status summary
    echo "POD STATUS SUMMARY:"
    kubectl get pods --no-headers | awk '{print $3}' | sort | uniq -c
    echo ""
    
    # Detailed pod list
    kubectl get pods -o custom-columns=NAME:.metadata.name,STATUS:.status.phase,READY:.status.containerStatuses[0].ready,RESTARTS:.status.containerStatuses[0].restartCount,AGE:.metadata.creationTimestamp --sort-by=.metadata.creationTimestamp
    echo ""
    
    echo "Press Ctrl+C to exit..."
    sleep 5
done
EOF

chmod +x pod-monitor.sh
./pod-monitor.sh
```

#### Advanced Monitor with Colors
```bash
cat > advanced-pod-monitor.sh << 'EOF'
#!/bin/bash
# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

show_pods() {
    while IFS= read -r line; do
        if echo "$line" | grep -q "Running"; then
            echo -e "${GREEN}$line${NC}"
        elif echo "$line" | grep -q "Pending\|ContainerCreating"; then
            echo -e "${YELLOW}$line${NC}"
        elif echo "$line" | grep -q "Error\|CrashLoopBackOff\|Failed"; then
            echo -e "${RED}$line${NC}"
        else
            echo "$line"
        fi
    done < <(kubectl get pods)
}

while true; do
    clear
    echo -e "${BLUE}=== KUBERNETES CLUSTER MONITOR ===${NC}"
    echo "Time: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
    
    show_pods
    
    echo ""
    echo -e "${BLUE}Legend:${NC} ${GREEN}Running${NC} ${YELLOW}Starting${NC} ${RED}Failed${NC}"
    echo "Refresh every 3 seconds... (Ctrl+C to exit)"
    
    sleep 3
done
EOF

chmod +x advanced-pod-monitor.sh
./advanced-pod-monitor.sh
```

#### K8s System-Specific Monitor
```bash
cat > k8s-system-monitor.sh << 'EOF'
#!/bin/bash
while true; do
    clear
    echo "=== K8S CLUSTER MANAGEMENT SYSTEM MONITOR ==="
    echo "Time: $(date)"
    echo ""
    
    echo "SYSTEM PODS:"
    kubectl get pods -l app=k8s-manager -o wide
    kubectl get pods -l app=python-app1 -o wide
    kubectl get pods -l app=python-app2 -o wide  
    kubectl get pods -l app=python-app3 -o wide
    kubectl get pods -l app=nats -o wide
    echo ""
    
    echo "SERVICES:"
    kubectl get svc | grep -E "(k8s-manager|nats)"
    echo ""
    
    echo "API HEALTH CHECK:"
    if curl -s http://localhost:8080/health > /dev/null 2>&1; then
        echo "✅ API responding"
        curl -s http://localhost:8080/api/cache/stats | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(f'Cache: {data.get(\"entryCount\", \"unknown\")} entries, age: {data.get(\"cacheAge\", \"unknown\")}ms')
except:
    print('Cache stats unavailable')
"
    else
        echo "❌ API not responding"
    fi
    echo ""
    
    echo "RECENT LOGS:"
    kubectl logs -l app=k8s-manager --tail=3 --since=30s 2>/dev/null || echo "No recent logs"
    
    sleep 5
done
EOF

chmod +x k8s-system-monitor.sh
./k8s-system-monitor.sh
```

### Quick Monitoring Commands
```bash
# Simple continuous pod monitoring
watch -n 2 'kubectl get pods && echo "" && kubectl get svc'

# Monitor your specific apps
watch -n 3 'kubectl get pods | grep -E "(k8s-manager|python-app|nats)"'

# Stream all pod events
kubectl get events --watch --field-selector involvedObject.kind=Pod

# Monitor with resource usage
watch -n 5 'kubectl get pods && echo "" && kubectl top pods'
```

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
curl http://localhost:8080/api/cache/stats
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

# Deploy updates
cd ..
./deploy-java-updates.sh
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

- **Java Manager**: Runs HTTP server, queries Kubernetes API, provides REST endpoints with background caching
- **Python Apps**: Connect to NATS message bus, communicate asynchronously
- **NATS**: Message bus for inter-service communication
- **UI**: D3.js visualization consuming Java manager REST API
- **No Spring**: Uses Java's built-in HTTP server for minimal footprint
- **Docker Builds**: All builds happen in containers to eliminate local dependencies
- **Background Caching**: Automatic 30-second data collection with thread-safe cache access
- **Real-time Monitoring**: Multiple dynamic monitoring options for system observation