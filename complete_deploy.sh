#!/bin/bash
# BLUEPRINT: Complete K8s Cluster System Deployment
# Run this script from the k8s-cluster-system directory

set -e  # Exit on any error

echo "🚀 COMPLETE K8S CLUSTER SYSTEM DEPLOYMENT"
echo "=========================================="

# Step 1: Verify Prerequisites
echo "📋 Step 1: Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi
echo "✅ Docker found"

if ! command -v minikube &> /dev/null; then
    echo "❌ Minikube is not installed. Please install Minikube first."
    exit 1
fi
echo "✅ Minikube found"

if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl is not installed. Please install kubectl first."
    exit 1
fi
echo "✅ kubectl found"

# Step 2: Start and Configure Minikube
echo ""
echo "🎯 Step 2: Starting and configuring Minikube..."

# Check if minikube is already running
if minikube status | grep -q "Running"; then
    echo "✅ Minikube is already running"
else
    echo "🔄 Starting Minikube..."
    minikube start --driver=docker --cpus=4 --memory=4096
    echo "✅ Minikube started"
fi

# Configure Docker to use minikube's daemon
echo "🔧 Configuring Docker to use Minikube's daemon..."
eval $(minikube docker-env)
echo "✅ Docker environment configured"

# Verify minikube is ready
echo "⏳ Waiting for Minikube to be ready..."
kubectl wait --for=condition=Ready nodes --all --timeout=300s
echo "✅ Minikube is ready"

# Step 3: Fix Java Build Script
echo ""
echo "🛠️  Step 3: Setting up Docker-based Java build..."

cd java-app

# Create Docker-based build script (no Gradle needed)
cat > build-with-docker.sh << 'BUILD_SCRIPT'
#!/bin/bash
echo "🏗️  Building Java app using Docker (no local Gradle needed)..."

# Create multi-stage Dockerfile for building
cat > Dockerfile.build << 'DOCKER_BUILD'
# Stage 1: Build with Gradle
FROM gradle:8.4-jdk17 AS builder
WORKDIR /app
COPY . .
RUN gradle clean shadowJar --no-daemon

# Stage 2: Runtime image
FROM openjdk:17-jdk-alpine
WORKDIR /app
COPY --from=builder /app/build/libs/k8s-cluster-manager-1.0.0.jar app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "/app.jar"]
DOCKER_BUILD

# Build the Docker image
echo "📦 Building k8s-manager Docker image..."
docker build -f Dockerfile.build -t k8s-manager:latest .

# Clean up
rm Dockerfile.build

echo "✅ Java application built successfully!"
BUILD_SCRIPT

chmod +x build-with-docker.sh
cd ..

# Step 4: Build All Applications
echo ""
echo "🏗️  Step 4: Building all applications..."

# Build Java application
echo "☕ Building Java application..."
cd java-app
./build-with-docker.sh
cd ..
echo "✅ Java application built"

# Build Python applications
echo "🐍 Building Python applications..."

echo "  📦 Building python-app1..."
cd python-apps/app1
docker build -t python-k8s-app1:latest .
cd ../..

echo "  📦 Building python-app2..."
cd python-apps/app2
docker build -t python-k8s-app2:latest .
cd ../..

echo "  📦 Building python-app3..."
cd python-apps/app3
docker build -t python-k8s-app3:latest .
cd ../..

echo "✅ All Python applications built"

# Verify images were created
echo ""
echo "🔍 Verifying Docker images..."
docker images | grep -E "(k8s-manager|python-k8s-app)"

# Step 5: Deploy to Kubernetes
echo ""
echo "🚀 Step 5: Deploying to Kubernetes..."

# Deploy NATS first
echo "  📡 Deploying NATS message bus..."
kubectl apply -f k8s-manifests/nats.yaml
echo "  ✅ NATS deployed"

# Deploy Java app with RBAC
echo "  🔐 Setting up RBAC permissions..."
kubectl apply -f k8s-manifests/java-app-rbac.yaml
echo "  ✅ RBAC configured"

echo "  ☕ Deploying Java application..."
kubectl apply -f k8s-manifests/java-app-deployment.yaml
echo "  ✅ Java application deployed"

# Deploy Python applications
echo "  🐍 Deploying Python applications..."
kubectl apply -f k8s-manifests/python-app1-deployment.yaml
kubectl apply -f k8s-manifests/python-app2-deployment.yaml
kubectl apply -f k8s-manifests/python-app3-deployment.yaml
echo "  ✅ Python applications deployed"

# Step 6: Wait for deployments to be ready
echo ""
echo "⏳ Step 6: Waiting for all deployments to be ready..."

echo "  🔄 Waiting for NATS..."
kubectl wait --for=condition=available --timeout=300s deployment/nats-deployment

echo "  🔄 Waiting for Java manager..."
kubectl wait --for=condition=available --timeout=300s deployment/k8s-manager

echo "  🔄 Waiting for Python apps..."
kubectl wait --for=condition=available --timeout=300s deployment/python-app1
kubectl wait --for=condition=available --timeout=300s deployment/python-app2  
kubectl wait --for=condition=available --timeout=300s deployment/python-app3

echo "✅ All deployments are ready!"

# Step 7: Show cluster status
echo ""
echo "📊 Step 7: Cluster Status"
echo "========================"

echo ""
echo "🏃 Running Pods:"
kubectl get pods -o wide

echo ""
echo "🌐 Services:"
kubectl get services

echo ""
echo "🚀 Deployments:"
kubectl get deployments

# Step 8: Setup port forwarding
echo ""
echo "🌍 Step 8: Setting up access to UI..."

# Check if port-forward is already running
if pgrep -f "kubectl port-forward.*k8s-manager-service" > /dev/null; then
    echo "✅ Port forwarding already running"
else
    echo "🔗 Starting port forwarding..."
    kubectl port-forward svc/k8s-manager-service 8080:8080 > /dev/null 2>&1 &
    PORT_FORWARD_PID=$!
    sleep 3
    echo "✅ Port forwarding started (PID: $PORT_FORWARD_PID)"
fi

# Step 9: Test the API
echo ""
echo "🧪 Step 9: Testing the system..."

echo "  🔍 Testing health endpoint..."
if curl -s http://localhost:8080/health | grep -q "healthy"; then
    echo "  ✅ Health check passed"
else
    echo "  ⚠️  Health check failed - checking logs..."
    kubectl logs -l app=k8s-manager --tail=10
fi

echo "  📊 Testing cluster info endpoint..."
if curl -s http://localhost:8080/api/cluster/info | grep -q "podCount"; then
    echo "  ✅ Cluster API working"
else
    echo "  ⚠️  Cluster API not responding - checking logs..."
    kubectl logs -l app=k8s-manager --tail=10
fi

# Step 10: Final instructions
echo ""
echo "🎉 DEPLOYMENT COMPLETE!"
echo "======================"
echo ""
echo "✅ Your K8s Cluster Management System is now running!"
echo ""
echo "🌐 Access the UI:"
echo "   1. The Java API is running at: http://localhost:8080"
echo "   2. Open the UI file: file://$(pwd)/ui/index.html"
echo "   3. Or run: open ui/index.html (Mac) / xdg-open ui/index.html (Linux)"
echo ""
echo "🔍 Useful commands:"
echo "   • Check pod status: kubectl get pods"
echo "   • View Java logs:   kubectl logs -l app=k8s-manager"
echo "   • View Python logs: kubectl logs -l app=python-app1"
echo "   • Stop port forward: pkill -f 'kubectl port-forward.*k8s-manager'"
echo "   • Restart system:   kubectl rollout restart deployment/k8s-manager"
echo ""
echo "🧹 To clean up:"
echo "   ./scripts/cleanup.sh"
echo ""
echo "🎯 Everything is ready! Open ui/index.html in your browser."

# Create a simple launcher script for the UI
cat > launch-ui.sh << 'UI_LAUNCHER'
#!/bin/bash
echo "🌐 Launching K8s Cluster Visualizer..."

# Check if port forwarding is running
if ! pgrep -f "kubectl port-forward.*k8s-manager-service" > /dev/null; then
    echo "🔗 Starting port forwarding..."
    kubectl port-forward svc/k8s-manager-service 8080:8080 > /dev/null 2>&1 &
    sleep 3
fi

# Open the UI
if command -v xdg-open &> /dev/null; then
    xdg-open ui/index.html
elif command -v open &> /dev/null; then
    open ui/index.html
else
    echo "🌐 Please open ui/index.html in your browser"
    echo "API is running at: http://localhost:8080"
fi
UI_LAUNCHER

chmod +x launch-ui.sh

echo ""
echo "💡 Quick launcher created: ./launch-ui.sh"