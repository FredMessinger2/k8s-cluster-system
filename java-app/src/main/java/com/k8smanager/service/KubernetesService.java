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
import com.k8smanager.service.datacaches.ClusterDataCache;

import java.util.List;
import java.util.Map;
import java.util.HashMap;
import java.util.ArrayList;

public class KubernetesService {
    private final CoreV1Api coreApi;
    private final AppsV1Api appsApi;
    private final ClusterDataCache cache;
    private ClusterInterrogator interrogator;
    
    // Cache validity period (30 seconds)
    private static final long CACHE_MAX_AGE_MS = 30000;
    
    public KubernetesService() throws Exception {
        ApiClient client = Config.defaultClient();
        Configuration.setDefaultApiClient(client);
        this.coreApi = new CoreV1Api();
        this.appsApi = new AppsV1Api();
        this.cache = new ClusterDataCache();
        
        // Start background data collection
        this.interrogator = new ClusterInterrogator(this, cache, 30);
        this.interrogator.start();
    }
    
    /**
     * Get cluster info - uses cache if valid, otherwise fetches fresh data
     */
    public Map<String, Object> getClusterInfo() throws ApiException {
        return getClusterInfo(false);
    }
    
    /**
     * Get cluster info with option to bypass cache
     */
    public Map<String, Object> getClusterInfo(boolean forceRefresh) throws ApiException {
        // If forcing refresh or cache is stale, fetch fresh data
        if (forceRefresh || cache.isStale(CACHE_MAX_AGE_MS)) {
            Map<String, Object> freshData = fetchClusterDataFromK8s();
            cache.updateClusterData(freshData);
            System.out.println("Returned fresh cluster data (cache " + 
                (forceRefresh ? "bypassed" : "stale") + ")");
            return freshData;
        }
        
        // Return cached data if valid
        if (cache.isValid()) {
            System.out.println("Returned cached cluster data (age: " + cache.getCacheAge() + "ms)");
            return cache.getCachedClusterData();
        }
        
        // Fallback to fresh data if cache is invalid
        Map<String, Object> freshData = fetchClusterDataFromK8s();
        cache.updateClusterData(freshData);
        System.out.println("Returned fresh cluster data (cache invalid)");
        return freshData;
    }
    
    /**
     * Actually fetch data from Kubernetes API
     */
    public Map<String, Object> fetchClusterDataFromK8s() throws ApiException {
        Map<String, Object> clusterInfo = new HashMap<>();
        
        // Get all pods
        V1PodList podList = coreApi.listPodForAllNamespaces(
            null, null, null, null, null, null, null, null, null, null, null);
        
        // Get all deployments
        V1DeploymentList deploymentList = appsApi.listDeploymentForAllNamespaces(
            null, null, null, null, null, null, null, null, null, null, null);
        
        // Convert to simple data structures for JSON serialization
        List<Map<String, Object>> pods = new ArrayList<>();
        for (V1Pod pod : podList.getItems()) {
            Map<String, Object> podInfo = new HashMap<>();
            podInfo.put("name", pod.getMetadata().getName());
            podInfo.put("namespace", pod.getMetadata().getNamespace());
            podInfo.put("status", pod.getStatus().getPhase());
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
            if (deployment.getMetadata().getCreationTimestamp() != null) {
                deploymentInfo.put("creationTimestamp", deployment.getMetadata().getCreationTimestamp().toString());
            }
            deployments.add(deploymentInfo);
        }
            
        clusterInfo.put("pods", pods);
        clusterInfo.put("deployments", deployments);
        clusterInfo.put("podCount", pods.size());
        clusterInfo.put("deploymentCount", deployments.size());
        clusterInfo.put("fetchTimestamp", System.currentTimeMillis());
        
        return clusterInfo;
    }
    
    /**
     * Get cache statistics
     */
    public Map<String, Object> getCacheStats() {
        return cache.getCacheStats();
    }
    
    /**
     * Get interrogator status
     */
    public Map<String, Object> getInterrogatorStatus() {
        return interrogator.getStatus();
    }
    
    /**
     * Force cache refresh
     */
    public void refreshCache() {
        if (interrogator != null) {
            interrogator.forceUpdate();
        }
    }
    
    /**
     * Cleanup resources
     */
    public void shutdown() {
        if (interrogator != null) {
            interrogator.stop();
        }
    }
}
