import time
from flask import Blueprint, jsonify
from services.cache_service import ClusterDataCache
from services.interrogator_service import ClusterInterrogator
from services.nats_service import NatsService
from typing import Optional
import time

cache_bp = Blueprint('cache', __name__)

# Will be set by main app
cache: Optional[ClusterDataCache] = None
interrogator: Optional[ClusterInterrogator] = None
nats_service: Optional[NatsService] = None

@cache_bp.route('/api/cache/stats', methods=['GET'])
def get_cache_stats():
    """Get cache statistics"""
    try:
        stats = cache.get_stats()
        if interrogator:
            stats.update({
                "interrogatorRunning": interrogator.is_running(),
                "intervalSeconds": interrogator.interval_seconds
            })
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@cache_bp.route('/api/cache/refresh', methods=['POST'])
def refresh_cache():
    """Force cache refresh"""
    try:
        if interrogator:
            interrogator.force_update()
            
            # Publish refresh event
            if nats_service:
                event = {
                    "action": "cache_refresh_triggered",
                    "source": "python-k8s-manager",
                    "timestamp": int(time.time() * 1000)
                }
                nats_service.publish_sync("k8s.events", event)
            
            return jsonify({"status": "cache refresh triggered"})
        else:
            return jsonify({"error": "interrogator not available"}), 503
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@cache_bp.route('/api/cache/invalidate', methods=['POST'])
def invalidate_cache():
    """Invalidate cache"""
    try:
        cache.invalidate()
        return jsonify({"status": "cache invalidated"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def init_cache_routes(cache_svc, interrogator_svc, nats_svc):
    """Initialize route dependencies"""
    global cache, interrogator, nats_service
    cache = cache_svc
    interrogator = interrogator_svc
    nats_service = nats_svc
