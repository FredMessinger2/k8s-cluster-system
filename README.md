# K8s Cluster Management System

## Project Structure
```
k8s-cluster-system/
├── java-app/               # Java Kubernetes manager (Gradle + no Spring)
├── python-apps/           # Python applications using NATS
├── ui/                   # Browser-based visualization
├── k8s-manifests/        # Kubernetes deployment files
└── scripts/              # Build and deployment scripts
```

## Prerequisites
- Java 17+
- Docker
- Minikube
- Python 3.11+ (for local testing)

## Quick Start

### 1. Start Minikube
```bash
minikube start
eval $(minikube docker-env)
```

### 2. Build and Deploy Everything
```bash
./build-and-deploy.sh
```

### 3. Access the UI
```bash
kubectl port-forward svc/k8s-manager-service 8080:8080 &
open ui/index.html
```

## Manual Build Steps

### Build Java App
```bash
cd java-app
./gradlew clean build
docker build -t k8s-manager:latest .
cd ..
```

### Build Python Apps
```bash
cd python-apps/app1
docker build -t python-k8s-app1:latest .
cd ../app2
docker build -t python-k8s-app2:latest .
cd ../app3
docker build -t python-k8s-app3:latest .
cd ../..
```

### Deploy to Kubernetes
```bash
kubectl apply -f k8s-manifests/nats.yaml
kubectl apply -f k8s-manifests/java-app-rbac.yaml
kubectl apply -f k8s-manifests/java-app-deployment.yaml
kubectl apply -f k8s-manifests/python-app1-deployment.yaml
kubectl apply -f k8s-manifests/python-app2-deployment.yaml
kubectl apply -f k8s-manifests/python-app3-deployment.yaml
```

## Verification
```bash
kubectl get pods
kubectl get services
kubectl logs -l app=k8s-manager
```

## Troubleshooting
- If Java app can't connect to K8s API, check RBAC permissions
- If Python apps can't connect to NATS, check NATS service status
- If UI shows no data, check Java app logs and port forwarding
