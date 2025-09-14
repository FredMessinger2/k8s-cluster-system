#!/bin/bash
# BLUEPRINT: Final Deployment - Image is Ready!

echo "🎯 FINAL DEPLOYMENT - IMAGE IS READY!"
echo "===================================="

# Step 1: Deploy the working image to Kubernetes
echo "🚀 Deploying working image to Kubernetes..."
kubectl delete pods -l app=k8s-manager

# Step 2: Wait for new pod to start
echo "⏳ Waiting for new pod to start..."
kubectl wait --for=condition=Ready pod -l app=k8s-manager --timeout=120s

if [ $? -eq 0 ]; then
    echo "✅ Pod is ready!"
else
    echo "⚠️  Pod taking longer than expected, checking status..."
    kubectl get pods -l app=k8s-manager
    kubectl describe pods -l app=k8s-manager
fi

# Step 3: Check application logs
echo "📝 Checking application logs..."
kubectl logs -l app=k8s-manager --tail=10

# Step 4: Ensure all deployments are ready
echo "⏳ Ensuring all deployments are ready..."
kubectl get deployments

# Step 5: Set up port forwarding
echo "🔗 Setting up port forwarding..."
if pgrep -f "kubectl port-forward.*k8s-manager-service" > /dev/null; then
    echo "✅ Port forwarding already running"
else
    kubectl port-forward svc/k8s-manager-service 8080:8080 > /dev/null 2>&1 &
    sleep 3
    echo "✅ Port forwarding started on port 8080"
fi

# Step 6: Test the API
echo "🧪 Testing the API..."
echo "Health check:"
curl -s http://localhost:8080/health || echo "API not ready yet, wait a moment..."

echo ""
echo "Cluster info:"
curl -s http://localhost:8080/api/cluster/info | head -c 200 || echo "API not ready yet, wait a moment..."

# Step 7: Show final status
echo ""
echo "📊 Final System Status:"
echo "======================"
kubectl get pods
echo ""
kubectl get services

# Step 8: Success message
echo ""
echo "🎉 DEPLOYMENT SUCCESSFUL!"
echo "========================"
echo ""
echo "✅ Your Kubernetes Cluster Management System is running!"
echo ""
echo "🌐 Access Points:"
echo "   • API Health:    http://localhost:8080/health"
echo "   • Cluster Info:  http://localhost:8080/api/cluster/info"
echo "   • Web UI:        file://$(pwd)/ui/index.html"
echo ""
echo "🖥️  To open the UI:"
if command -v open &> /dev/null; then
    echo "   macOS: open ui/index.html"
elif command -v xdg-open &> /dev/null; then
    echo "   Linux: xdg-open ui/index.html"
fi
echo "   Or manually open ui/index.html in your web browser"
echo ""
echo "🔍 Monitor Commands:"
echo "   • Watch pods:    kubectl get pods -w"
echo "   • View logs:     kubectl logs -l app=k8s-manager -f"
echo "   • All resources: kubectl get all"
echo ""
echo "🧹 To clean up later:"
echo "   ./scripts/cleanup.sh"