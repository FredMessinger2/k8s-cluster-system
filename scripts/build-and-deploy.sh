#!/bin/bash
set -e

echo "🚀 Building and deploying K8s Cluster Management System..."

# Check if minikube is running
if ! minikube status > /dev/null 2>&1; then
    echo "❌ Minikube is not running. Please start minikube first:"
    echo "   minikube start"
    echo "   eval \$(minikube docker-env)"
    exit 1
fi

echo "✅ Minikube is running"

# Deploy NATS first
echo "📦 Deploying NATS..."
kubectl apply -f k8s-manifests/nats.yaml

# Build Java application
echo "☕ Building Java application..."
cd java-app
./build-with-docker.sh
cd ..

# Build Python applications
echo "🐍 Building Python applications..."
cd python-apps/app1
docker build -t python-k8s-app1:latest .
cd ../app2
docker build -t python-k8s-app2:latest .
cd ../app3
docker build -t python-k8s-app3:latest .
cd ../..

# Deploy applications
echo "🚀 Deploying applications to Kubernetes..."
kubectl apply -f k8s-manifests/java-app-rbac.yaml
kubectl apply -f k8s-manifests/java-app-deployment.yaml
kubectl apply -f k8s-manifests/python-app1-deployment.yaml
kubectl apply -f k8s-manifests/python-app2-deployment.yaml
kubectl apply -f k8s-manifests/python-app3-deployment.yaml

# Wait for deployments
echo "⏳ Waiting for deployments to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/nats-deployment
kubectl wait --for=condition=available --timeout=300s deployment/k8s-manager
kubectl wait --for=condition=available --timeout=300s deployment/python-app1
kubectl wait --for=condition=available --timeout=300s deployment/python-app2
kubectl wait --for=condition=available --timeout=300s deployment/python-app3

echo "✅ All deployments are ready!"

# Show status
kubectl get pods
kubectl get services

echo ""
echo "🌐 To access the UI:"
echo "   1. Run: kubectl port-forward svc/k8s-manager-service 8080:8080"
echo "   2. Open: ui/index.html in your browser"
echo ""
echo "🔍 To check logs:"
echo "   kubectl logs -l app=k8s-manager"
echo "   kubectl logs -l app=python-app1"
