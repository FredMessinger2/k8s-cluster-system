import threading
import time
from services.kubernetes_service import KubernetesService
from services.cache_service import ClusterDataCache
from services.nats_service import NatsService
from typing import Optional

class ClusterInterrogator:
    """Background service for periodic cluster data collection"""
    
    def __init__(self, k8s_service: KubernetesService, cache: ClusterDataCache, 
                 nats_service: Optional[NatsService] = None, interval_seconds: int = 30):
        self.k8s_service = k8s_service
        self.cache = cache
        self.nats_service = nats_service
        self.interval_seconds = interval_seconds
        self._running = False
        self._thread: Optional[threading.Thread] = None
    
    def start(self) -> None:
        """Start background data collection"""
        if self._running:
            print("ClusterInterrogator already running")
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        
        print(f"ClusterInterrogator started with {self.interval_seconds}s interval")
    
    def stop(self) -> None:
        """Stop background data collection"""
        if not self._running:
            return
        
        print("Stopping ClusterInterrogator...")
        self._running = False
        
        if self._thread:
            self._thread.join(timeout=10)
        
        print("ClusterInterrogator stopped")
    
    def force_update(self) -> None:
        """Force immediate data collection"""
        threading.Thread(target=self._collect_data, daemon=True).start()
        print("Forced cluster data update triggered")
    
    def _run(self) -> None:
        """Main background loop"""
        # Initial collection
        self._collect_data()
        
        # Periodic collection
        while self._running:
            time.sleep(self.interval_seconds)
            if self._running:  # Check again after sleep
                self._collect_data()
    
    def _collect_data(self) -> None:
        """Collect cluster data and update cache"""
        try:
            start_time = time.time()
            print("Collecting cluster data...")
            
            # Fetch data from Kubernetes
            cluster_data = self.k8s_service.fetch_cluster_data()
            
            # Update cache
            self.cache.update_data(cluster_data)
            
            # Publish metrics to NATS
            if self.nats_service:
                metrics = {
                    "podCount": cluster_data.pod_count,
                    "deploymentCount": cluster_data.deployment_count,
                    "timestamp": int(time.time() * 1000),
                    "source": "python-k8s-manager"
                }
                self.nats_service.publish_sync("k8s.metrics", metrics)
            
            duration = time.time() - start_time
            print(f"Cluster data collection completed in {duration:.2f}s")
            
        except Exception as e:
            print(f"Error collecting cluster data: {e}")
    
    def is_running(self) -> bool:
        """Check if interrogator is running"""
        return self._running
    
    def get_status(self) -> dict:
        """Get interrogator status"""
        cache_stats = self.cache.get_stats()
        cache_stats.update({
            "interrogatorRunning": self._running,
            "intervalSeconds": self.interval_seconds
        })
        return cache_stats
