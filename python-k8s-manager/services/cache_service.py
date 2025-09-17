import threading
import time
from typing import Optional, Dict, Any
from models.cluster_data import ClusterData

class ClusterDataCache:
    """Thread-safe cache for cluster data with read/write locking"""
    
    def __init__(self):
        self._lock = threading.RWLock()
        self._data: Optional[ClusterData] = None
        self._last_updated: float = 0
        self._is_valid: bool = False
    
    def update_data(self, cluster_data: ClusterData) -> None:
        """Update cache with new cluster data"""
        with self._lock.gen_wlock():
            self._data = cluster_data
            self._last_updated = time.time()
            self._is_valid = True
            print(f"Cache updated with {cluster_data.pod_count} pods, {cluster_data.deployment_count} deployments")
    
    def get_data(self) -> Optional[ClusterData]:
        """Get cached cluster data"""
        with self._lock.gen_rlock():
            return self._data
    
    def is_valid(self) -> bool:
        """Check if cache contains valid data"""
        with self._lock.gen_rlock():
            return self._is_valid and self._data is not None
    
    def get_last_updated(self) -> float:
        """Get timestamp of last update"""
        with self._lock.gen_rlock():
            return self._last_updated
    
    def get_cache_age(self) -> float:
        """Get cache age in seconds"""
        with self._lock.gen_rlock():
            if not self._is_valid:
                return -1
            return time.time() - self._last_updated
    
    def is_stale(self, max_age_seconds: float) -> bool:
        """Check if cache is stale"""
        age = self.get_cache_age()
        return age < 0 or age > max_age_seconds
    
    def invalidate(self) -> None:
        """Invalidate cache"""
        with self._lock.gen_wlock():
            self._data = None
            self._is_valid = False
            self._last_updated = 0
            print("Cache invalidated")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock.gen_rlock():
            return {
                "isValid": self._is_valid,
                "entryCount": len(self._data.pods) + len(self._data.deployments) if self._data else 0,
                "lastUpdated": self._last_updated * 1000,  # Convert to milliseconds
                "cacheAge": self.get_cache_age() * 1000 if self._is_valid else -1
            }

# Simple RWLock implementation for Python
class RWLock:
    """Read-Write lock implementation"""
    
    def __init__(self):
        self._read_ready = threading.Condition(threading.RLock())
        self._readers = 0
    
    def gen_rlock(self):
        """Generate read lock context manager"""
        return ReadLock(self)
    
    def gen_wlock(self):
        """Generate write lock context manager"""
        return WriteLock(self)

class ReadLock:
    def __init__(self, rwlock):
        self._rwlock = rwlock
    
    def __enter__(self):
        self._rwlock._read_ready.acquire()
        try:
            self._rwlock._readers += 1
        finally:
            self._rwlock._read_ready.release()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self._rwlock._read_ready.acquire()
        try:
            self._rwlock._readers -= 1
            if self._rwlock._readers == 0:
                self._rwlock._read_ready.notifyAll()
        finally:
            self._rwlock._read_ready.release()

class WriteLock:
    def __init__(self, rwlock):
        self._rwlock = rwlock
    
    def __enter__(self):
        self._rwlock._read_ready.acquire()
        while self._rwlock._readers > 0:
            self._rwlock._read_ready.wait()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self._rwlock._read_ready.release()

# Monkey patch for easier use
threading.RWLock = RWLock
