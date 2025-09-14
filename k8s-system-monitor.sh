#!/bin/bash
# Monitor your specific K8s cluster management system

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
