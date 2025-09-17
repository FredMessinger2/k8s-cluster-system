import time
import time
from flask import Blueprint, jsonify, request
from services.kubernetes_service import KubernetesService
from services.cache_service import ClusterDataCache
from services.nats_service import NatsService
from typing import Optional

cluster_bp = Blueprint('cluster', __name__)

# Will be set by main app
k8s_service: Optional[KubernetesService] = None
cache: Optional[ClusterDataCache] = None
nats_service: Optional[NatsService] = None

CACHE_MAX_AGE_SECONDS = 30

@cluster_bp.route('/api/cluster/info', methods=['GET'])
def get_cluster_info():
    """Get cluster information from cache or fresh from API"""
    try:
        force_refresh = request.args.get('force', 'false').lower() == 'true'
        
        # Check if we should use cache or fetch fresh data
        if not force_refresh and cache.is_valid() and not cache.is_stale(CACHE_MAX_AGE_SECONDS):
            # Return cached data
            cached_data = cache.get_data()
            if cached_data:
                result = cached_data.to_dict()
                result['source'] = 'cache'
                result['cacheAge'] = cache.get_cache_age()
                
                # Publish access event
                if nats_service:
                    event = {
                        "action": "cluster_info_accessed",
                        "source": "python-k8s-manager",
                        "timestamp": int(time.time() * 1000),
                        "podCount": cached_data.pod_count,
                        "fromCache": True
                    }
                    nats_service.publish_sync("k8s.events", event)
                
                return jsonify(result)
        
        # Fetch fresh data
        cluster_data = k8s_service.fetch_cluster_data()
        cache.update_data(cluster_data)
        
        result = cluster_data.to_dict()
        result['source'] = 'fresh'
        
        # Publish access event
        if nats_service:
            event = {
                "action": "cluster_info_accessed",
                "source": "python-k8s-manager", 
                "timestamp": int(time.time() * 1000),
                "podCount": cluster_data.pod_count,
                "fromCache": False
            }
            nats_service.publish_sync("k8s.events", event)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@cluster_bp.route('/api/cluster/pods', methods=['GET'])
def get_pods():
    """Get only pod information"""
    try:
        if cache.is_valid() and not cache.is_stale(CACHE_MAX_AGE_SECONDS):
            cached_data = cache.get_data()
            if cached_data:
                return jsonify({
                    "pods": [pod.to_dict() for pod in cached_data.pods],
                    "count": len(cached_data.pods),
                    "source": "cache"
                })
        
        # Fetch fresh if cache invalid/stale
        cluster_data = k8s_service.fetch_cluster_data()
        cache.update_data(cluster_data)
        
        return jsonify({
            "pods": [pod.to_dict() for pod in cluster_data.pods],
            "count": len(cluster_data.pods),
            "source": "fresh"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@cluster_bp.route('/api/cluster/deployments', methods=['GET'])
def get_deployments():
    """Get only deployment information"""
    try:
        if cache.is_valid() and not cache.is_stale(CACHE_MAX_AGE_SECONDS):
            cached_data = cache.get_data()
            if cached_data:
                return jsonify({
                    "deployments": [dep.to_dict() for dep in cached_data.deployments],
                    "count": len(cached_data.deployments),
                    "source": "cache"
                })
        
        # Fetch fresh if cache invalid/stale
        cluster_data = k8s_service.fetch_cluster_data()
        cache.update_data(cluster_data)
        
        return jsonify({
            "deployments": [dep.to_dict() for dep in cluster_data.deployments],
            "count": len(cluster_data.deployments),
            "source": "fresh"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def init_cluster_routes(k8s_svc, cache_svc, nats_svc):
    """Initialize route dependencies"""
    global k8s_service, cache, nats_service
    k8s_service = k8s_svc
    cache = cache_svc 
    nats_service = nats_svc
