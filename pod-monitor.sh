#!/bin/bash
# Dynamic pod monitor with statistics

while true; do
    clear
    echo "=== KUBERNETES POD MONITOR ==="
    echo "Timestamp: $(date)"
    echo "Cluster: $(kubectl config current-context)"
    echo ""
    
    # Pod status summary
    echo "POD STATUS SUMMARY:"
    kubectl get pods --no-headers | awk '{print $3}' | sort | uniq -c
    echo ""
    
    # Detailed pod list
    echo "DETAILED POD STATUS:"
    kubectl get pods -o custom-columns=NAME:.metadata.name,STATUS:.status.phase,READY:.status.containerStatuses[0].ready,RESTARTS:.status.containerStatuses[0].restartCount,AGE:.metadata.creationTimestamp --sort-by=.metadata.creationTimestamp
    echo ""
    
    # Resource usage if metrics available
    echo "RESOURCE USAGE:"
    kubectl top pods 2>/dev/null || echo "Metrics not available"
    echo ""
    
    echo "Press Ctrl+C to exit..."
    sleep 5
done
