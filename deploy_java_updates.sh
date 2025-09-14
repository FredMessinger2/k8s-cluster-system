#!/bin/bash
# BLUEPRINT: Deploy Updated Java App with Cache System

echo "🔄 DEPLOYING UPDATED JAVA APPLICATION"
echo "===================================="

# Step 1: Update Kubernetes Deployment
echo "📦 Step 1: Updating Kubernetes deployment..."
kubectl delete pods -l app=k8s-manager

echo "⏳ Waiting for new pod to start..."
if kubectl wait --for=condition=Ready pod -l app=k8s-manager --timeout=120s; then
    echo "✅ New pod is ready"
else
    echo "❌ Pod failed to start within timeout"
    echo "🔍 Pod status:"
    kubectl get pods -l app=k8s-manager
    echo "🔍 Pod describe:"
    kubectl describe pods -l app=k8s-manager
    exit 1
fi

# Step 2: Check Cache System Startup
echo ""
echo "📊 Step 2: Checking cache system startup..."
sleep 5
kubectl logs -l app=k8s-manager --tail=20

# Step 3: Restart Port Forwarding
echo ""
echo "🔗 Step 3: Setting up port forwarding..."
pkill -f "kubectl port-forward.*k8s-manager" 2>/dev/null || true

kubectl port-forward svc/k8s-manager-service 8080:8080 > /dev/null 2>&1 &
PORT_FORWARD_PID=$!

sleep 3

# Verify port forwarding is working
if curl -s http://localhost:8080/health > /dev/null 2>&1; then
    echo "✅ Port forwarding established (PID: $PORT_FORWARD_PID)"
else
    echo "⚠️  Port forwarding may be starting - checking in a moment..."
    sleep 5
    if curl -s http://localhost:8080/health > /dev/null 2>&1; then
        echo "✅ Port forwarding now working"
    else
        echo "❌ Port forwarding failed"
        exit 1
    fi
fi

# Step 4: Test New Cache Endpoints
echo ""
echo "🧪 Step 4: Testing new cache endpoints..."

echo "  Testing health endpoint..."
HEALTH_RESPONSE=$(curl -s http://localhost:8080/health)
echo "  Health: $HEALTH_RESPONSE"

echo ""
echo "  Testing cache statistics..."
curl -s http://localhost:8080/api/cache/stats | python3 -m json.tool

echo ""
echo "  Testing cluster info (cache-enabled)..."
CLUSTER_INFO=$(curl -s http://localhost:8080/api/cluster/info)
if echo "$CLUSTER_INFO" | python3 -m json.tool > /dev/null 2>&1; then
    echo "  ✅ Cluster info endpoint working"
    echo "$CLUSTER_INFO" | python3 -m json.tool | head -10
    echo "  ..."
else
    echo "  ❌ Cluster info endpoint failed"
    echo "  Response: $CLUSTER_INFO"
fi

echo ""
echo "  Testing cache refresh..."
REFRESH_RESPONSE=$(curl -s -X POST http://localhost:8080/api/cache/refresh)
echo "  Refresh: $REFRESH_RESPONSE"

echo ""
echo "  Cache stats after refresh:"
curl -s http://localhost:8080/api/cache/stats | python3 -m json.tool

# Step 5: Monitor Cache Behavior
echo ""
echo "📈 Step 5: Monitoring cache behavior..."
echo "  Watching logs for 30 seconds to see cache activity..."

timeout 30s kubectl logs -l app=k8s-manager -f &
LOG_PID=$!

sleep 30
kill $LOG_PID 2>/dev/null || true

# Final Status
echo ""
echo "✅ DEPLOYMENT COMPLETE!"
echo "======================"
echo ""
echo "🔍 System Status:"
kubectl get pods -l app=k8s-manager

echo ""
echo "🌐 Available Endpoints:"
echo "  • Health:         http://localhost:8080/health"
echo "  • Cluster Info:   http://localhost:8080/api/cluster/info"
echo "  • Cache Stats:    http://localhost:8080/api/cache/stats"
echo "  • Cache Refresh:  POST http://localhost:8080/api/cache/refresh"
echo "  • NATS Publish:   POST http://localhost:8080/api/nats/publish"
echo ""
echo "📊 Cache Features:"
echo "  • Background data collection every 30 seconds"
echo "  • Cache-first API responses with automatic fallback"
echo "  • Manual cache refresh capability"
echo "  • Thread-safe concurrent access"
echo ""
echo "🔧 Monitor Commands:"
echo "  • Watch cache logs: kubectl logs -l app=k8s-manager -f"
echo "  • Check cache stats: curl -s http://localhost:8080/api/cache/stats | python3 -m json.tool"
echo "  • Force refresh: curl -X POST http://localhost:8080/api/cache/refresh"