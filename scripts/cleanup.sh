#!/bin/bash

echo "🧹 Cleaning up K8s Cluster Management System..."

kubectl delete -f k8s-manifests/python-app3-deployment.yaml --ignore-not-found
kubectl delete -f k8s-manifests/python-app2-deployment.yaml --ignore-not-found
kubectl delete -f k8s-manifests/python-app1-deployment.yaml --ignore-not-found
kubectl delete -f k8s-manifests/java-app-deployment.yaml --ignore-not-found
kubectl delete -f k8s-manifests/java-app-rbac.yaml --ignore-not-found
kubectl delete -f k8s-manifests/nats.yaml --ignore-not-found

echo "✅ Cleanup complete!"
