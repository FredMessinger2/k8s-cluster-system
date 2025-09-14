package com.k8smanager.service;

import com.k8smanager.service.datacaches.ClusterDataCache;
import java.util.Map;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;

public class ClusterInterrogator {
    private final KubernetesService kubernetesService;
    private final ClusterDataCache cache;
    private final ScheduledExecutorService executor;
    private final AtomicBoolean isRunning;
    private final long intervalSeconds;
    
    // Default to 30 second intervals
    public ClusterInterrogator(KubernetesService kubernetesService, ClusterDataCache cache) {
        this(kubernetesService, cache, 30);
    }
    
    public ClusterInterrogator(KubernetesService kubernetesService, ClusterDataCache cache, long intervalSeconds) {
        this.kubernetesService = kubernetesService;
        this.cache = cache;
        this.intervalSeconds = intervalSeconds;
        this.executor = Executors.newSingleThreadScheduledExecutor(r -> {
            Thread t = new Thread(r, "ClusterInterrogator");
            t.setDaemon(true); // Don't prevent JVM shutdown
            return t;
        });
        this.isRunning = new AtomicBoolean(false);
    }
    
    /**
     * Start periodic cluster data collection
     */
    public void start() {
        if (isRunning.compareAndSet(false, true)) {
            System.out.println("Starting ClusterInterrogator with " + intervalSeconds + " second intervals");
            
            // Run initial collection immediately
            executor.submit(this::collectClusterData);
            
            // Schedule periodic collection
            executor.scheduleAtFixedRate(
                this::collectClusterData,
                intervalSeconds,
                intervalSeconds,
                TimeUnit.SECONDS
            );
            
            System.out.println("ClusterInterrogator started successfully");
        } else {
            System.out.println("ClusterInterrogator is already running");
        }
    }
    
    /**
     * Stop periodic collection
     */
    public void stop() {
        if (isRunning.compareAndSet(true, false)) {
            System.out.println("Stopping ClusterInterrogator...");
            executor.shutdown();
            try {
                if (!executor.awaitTermination(10, TimeUnit.SECONDS)) {
                    executor.shutdownNow();
                    if (!executor.awaitTermination(5, TimeUnit.SECONDS)) {
                        System.err.println("ClusterInterrogator did not terminate cleanly");
                    }
                }
                System.out.println("ClusterInterrogator stopped");
            } catch (InterruptedException e) {
                executor.shutdownNow();
                Thread.currentThread().interrupt();
            }
        }
    }
    
    /**
     * Force immediate data collection
     */
    public void forceUpdate() {
        if (isRunning.get()) {
            executor.submit(this::collectClusterData);
            System.out.println("Forced cluster data update requested");
        } else {
            System.out.println("Cannot force update - ClusterInterrogator is not running");
        }
    }
    
    /**
     * Collect cluster data and update cache
     */
    private void collectClusterData() {
        try {
            long startTime = System.currentTimeMillis();
            System.out.println("Collecting cluster data...");
            
            Map<String, Object> clusterData = kubernetesService.getClusterInfo();
            cache.updateClusterData(clusterData);
            
            long duration = System.currentTimeMillis() - startTime;
            System.out.println("Cluster data collection completed in " + duration + "ms");
            
        } catch (Exception e) {
            System.err.println("Error collecting cluster data: " + e.getMessage());
            e.printStackTrace();
        }
    }
    
    /**
     * Check if interrogator is running
     */
    public boolean isRunning() {
        return isRunning.get();
    }
    
    /**
     * Get interrogator status
     */
    public Map<String, Object> getStatus() {
        Map<String, Object> status = cache.getCacheStats();
        status.put("interrogatorRunning", isRunning.get());
        status.put("intervalSeconds", intervalSeconds);
        return status;
    }
}
