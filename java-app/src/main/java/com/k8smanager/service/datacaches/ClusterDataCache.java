package com.k8smanager.service.datacaches;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.locks.ReadWriteLock;
import java.util.concurrent.locks.ReentrantReadWriteLock;

public class ClusterDataCache {
    private final ConcurrentHashMap<String, Object> cache;
    private final ReadWriteLock lock;
    private volatile long lastUpdated;
    private volatile boolean isValid;
    
    public ClusterDataCache() {
        this.cache = new ConcurrentHashMap<>();
        this.lock = new ReentrantReadWriteLock();
        this.lastUpdated = 0;
        this.isValid = false;
    }
    
    /**
     * Store cluster data in cache with thread safety
     */
    public void updateClusterData(Map<String, Object> clusterData) {
        lock.writeLock().lock();
        try {
            cache.clear();
            cache.putAll(clusterData);
            this.lastUpdated = System.currentTimeMillis();
            this.isValid = true;
            System.out.println("Cache updated with " + clusterData.size() + " entries at " + lastUpdated);
        } finally {
            lock.writeLock().unlock();
        }
    }
    
    /**
     * Get cached cluster data with read lock
     */
    public Map<String, Object> getCachedClusterData() {
        lock.readLock().lock();
        try {
            // Return defensive copy to prevent external modification
            return new ConcurrentHashMap<>(cache);
        } finally {
            lock.readLock().unlock();
        }
    }
    
    /**
     * Check if cache contains valid data
     */
    public boolean isValid() {
        lock.readLock().lock();
        try {
            return isValid && !cache.isEmpty();
        } finally {
            lock.readLock().unlock();
        }
    }
    
    /**
     * Get last update timestamp
     */
    public long getLastUpdated() {
        lock.readLock().lock();
        try {
            return lastUpdated;
        } finally {
            lock.readLock().unlock();
        }
    }
    
    /**
     * Get cache age in milliseconds
     */
    public long getCacheAge() {
        lock.readLock().lock();
        try {
            return isValid ? System.currentTimeMillis() - lastUpdated : -1;
        } finally {
            lock.readLock().unlock();
        }
    }
    
    /**
     * Check if cache is stale (older than maxAge milliseconds)
     */
    public boolean isStale(long maxAgeMs) {
        long age = getCacheAge();
        return age < 0 || age > maxAgeMs;
    }
    
    /**
     * Get specific cached value
     */
    public Object getCachedValue(String key) {
        lock.readLock().lock();
        try {
            return cache.get(key);
        } finally {
            lock.readLock().unlock();
        }
    }
    
    /**
     * Invalidate cache
     */
    public void invalidate() {
        lock.writeLock().lock();
        try {
            cache.clear();
            isValid = false;
            lastUpdated = 0;
            System.out.println("Cache invalidated");
        } finally {
            lock.writeLock().unlock();
        }
    }
    
    /**
     * Get cache statistics
     */
    public Map<String, Object> getCacheStats() {
        lock.readLock().lock();
        try {
            Map<String, Object> stats = new ConcurrentHashMap<>();
            stats.put("isValid", isValid);
            stats.put("entryCount", cache.size());
            stats.put("lastUpdated", lastUpdated);
            stats.put("cacheAge", getCacheAge());
            return stats;
        } finally {
            lock.readLock().unlock();
        }
    }
}
