package com.k8smanager.service;

import io.kubernetes.client.openapi.ApiClient;
import io.kubernetes.client.openapi.ApiException;
import io.kubernetes.client.openapi.Configuration;
import io.kubernetes.client.openapi.apis.AppsV1Api;
import io.kubernetes.client.openapi.apis.CoreV1Api;
import io.kubernetes.client.openapi.models.V1Pod;
import io.kubernetes.client.openapi.models.V1PodList;
import io.kubernetes.client.openapi.models.V1Deployment;
import io.kubernetes.client.openapi.models.V1DeploymentList;
import io.kubernetes.client.util.Config;

import java.util.List;
import java.util.Map;
import java.util.HashMap;
import java.util.ArrayList;

public class KubernetesService {
    private final CoreV1Api coreApi;
    private final AppsV1Api appsApi;
    
    public KubernetesService() throws Exception {
        ApiClient client = Config.defaultClient();
        Configuration.setDefaultApiClient(client);
        this.coreApi = new CoreV1Api();
        this.appsApi = new AppsV1Api();
    }
    
    public Map<String, Object> getClusterInfo() throws ApiException {
        Map<String, Object> clusterInfo = new HashMap<>();
        
        // Get all pods - fixed method signature with 11 parameters
        V1PodList podList = coreApi.listPodForAllNamespaces(
            null, null, null, null, null, null, null, null, null, null, null);
        
        // Get all deployments - fixed method signature with 11 parameters  
        V1DeploymentList deploymentList = appsApi.listDeploymentForAllNamespaces(
            null, null, null, null, null, null, null, null, null, null, null);
        
        // Convert to simple data structures for JSON serialization
        List<Map<String, Object>> pods = new ArrayList<>();
        for (V1Pod pod : podList.getItems()) {
            Map<String, Object> podInfo = new HashMap<>();
            podInfo.put("name", pod.getMetadata().getName());
            podInfo.put("namespace", pod.getMetadata().getNamespace());
            podInfo.put("status", pod.getStatus().getPhase());
            // Convert timestamp to string to avoid serialization issues
            if (pod.getMetadata().getCreationTimestamp() != null) {
                podInfo.put("creationTimestamp", pod.getMetadata().getCreationTimestamp().toString());
            }
            pods.add(podInfo);
        }
        
        List<Map<String, Object>> deployments = new ArrayList<>();
        for (V1Deployment deployment : deploymentList.getItems()) {
            Map<String, Object> deploymentInfo = new HashMap<>();
            deploymentInfo.put("name", deployment.getMetadata().getName());
            deploymentInfo.put("namespace", deployment.getMetadata().getNamespace());
            deploymentInfo.put("replicas", deployment.getSpec().getReplicas());
            deploymentInfo.put("readyReplicas", deployment.getStatus().getReadyReplicas());
            // Convert timestamp to string
            if (deployment.getMetadata().getCreationTimestamp() != null) {
                deploymentInfo.put("creationTimestamp", deployment.getMetadata().getCreationTimestamp().toString());
            }
            deployments.add(deploymentInfo);
        }
            
        clusterInfo.put("pods", pods);
        clusterInfo.put("deployments", deployments);
        clusterInfo.put("podCount", pods.size());
        clusterInfo.put("deploymentCount", deployments.size());
        
        return clusterInfo;
    }
}
