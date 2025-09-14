#!/bin/bash
# BLUEPRINT: Launch UI Script - Starts port forwarding and opens the web interface

echo "🌐 Launching K8s Cluster Visualizer..."

# Step 1: Check if pods are running
echo "🔍 Checking system status..."
if ! kubectl get pods -l app=k8s-manager | grep -q "Running"; then
    echo "❌ k8s-manager pod is not running!"
    echo "💡 Try running: ./complete-deploy.sh"
    exit 1
fi

echo "✅ k8s-manager pod is running"

# Step 2: Check if port forwarding is already running
if pgrep -f "kubectl port-forward.*k8s-manager-service.*8080" > /dev/null; then
    echo "✅ Port forwarding already active on port 8080"
else
    echo "🔗 Starting port forwarding..."
    kubectl port-forward svc/k8s-manager-service 8080:8080 > /dev/null 2>&1 &
    PORT_FORWARD_PID=$!
    
    # Wait for port forwarding to establish
    sleep 3
    
    # Verify port forwarding worked
    if curl -s http://localhost:8080/health > /dev/null 2>&1; then
        echo "✅ Port forwarding established (PID: $PORT_FORWARD_PID)"
    else
        echo "⚠️  Port forwarding may be starting - wait a moment..."
    fi
fi

# Step 3: Test API endpoints
echo "🧪 Testing API..."
if curl -s http://localhost:8080/health | grep -q "healthy"; then
    echo "✅ API health check passed"
else
    echo "⚠️  API not responding yet - may need a moment to start"
fi

# Step 4: Start UI server
echo "🖥️  Starting UI server..."

# Check if UI server is already running on port 3000
if lsof -Pi :3000 -sTCP:LISTEN -t > /dev/null 2>&1; then
    echo "✅ UI server already running on port 3000"
else
    cd ui
    python3 -m http.server 3000 > /dev/null 2>&1 &
    UI_SERVER_PID=$!
    cd ..
    sleep 2
    echo "✅ UI server started on port 3000 (PID: $UI_SERVER_PID)"
fi

# Step 5: Open browser
echo "🚀 Opening web browser..."

if command -v xdg-open &> /dev/null; then
    # Linux
    xdg-open http://localhost:3000 > /dev/null 2>&1 &
    echo "✅ Browser opened via xdg-open"
elif command -v open &> /dev/null; then
    # macOS
    open http://localhost:3000
    echo "✅ Browser opened via open command"
else
    echo "💡 Please manually open your browser to: http://localhost:3000"
fi

# Step 6: Show status and instructions
echo ""
echo "🎯 SYSTEM READY!"
echo "================"
echo ""
echo "🌐 Access Points:"
echo "   • Web UI:        http://localhost:3000"
echo "   • API Health:    http://localhost:8080/health"
echo "   • Cluster Info:  http://localhost:8080/api/cluster/info"
echo ""
echo "🔍 Monitor Commands:"
echo "   • Watch pods:    kubectl get pods -w"
echo "   • View logs:     kubectl logs -l app=k8s-manager -f"
echo "   • Check all:     kubectl get all"
echo ""
echo "🛑 To stop services:"
echo "   • Stop port forward: pkill -f 'kubectl port-forward.*k8s-manager'"
echo "   • Stop UI server:    pkill -f 'python3.*http.server.*3000'"
echo "   • Or just close this terminal"
echo ""
echo "✨ Your Kubernetes cluster visualization is now running!"