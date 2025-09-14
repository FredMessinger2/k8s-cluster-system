#!/bin/bash
# Advanced pod monitor with colors and filtering

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

show_pods() {
    local filter="$1"
    
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
    done < <(kubectl get pods $filter)
}

while true; do
    clear
    echo -e "${BLUE}=== KUBERNETES CLUSTER MONITOR ===${NC}"
    echo "Time: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "Namespace: $(kubectl config view --minify --output 'jsonpath={..namespace}' 2>/dev/null || echo 'default')"
    echo ""
    
    # Show all pods with color coding
    show_pods ""
    
    echo ""
    echo -e "${BLUE}Legend:${NC} ${GREEN}Running${NC} ${YELLOW}Starting${NC} ${RED}Failed${NC}"
    echo "Refresh every 3 seconds... (Ctrl+C to exit)"
    
    sleep 3
done
