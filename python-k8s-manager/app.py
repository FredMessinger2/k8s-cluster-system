import os
from flask import Flask, jsonify
from flask_cors import CORS
import time
import os
import signal
import sys
import time

from services.kubernetes_service import KubernetesService
from services.cache_service import ClusterDataCache
from services.nats_service import NatsService
from services.interrogator_service import ClusterInterrogator
from api.cluster_routes import cluster_bp, init_cluster_routes
from api.cache_routes import cache_bp, init_cache_routes

class PythonK8sManager:
    """Main application class"""
    
    def __init__(self):
        self.app = Flask(__name__)
        CORS(self.app)
        
        # Services
        self.k8s_service = None
        self.cache = None
        self.nats_service = None
        self.interrogator = None
    
    def initialize_services(self):
        """Initialize all services"""
        try:
            print("Initializing Python K8s Manager services...")
            
            # Initialize Kubernetes service
            self.k8s_service = KubernetesService()
            
            # Initialize cache
            self.cache = ClusterDataCache()
            
            # Initialize NATS service
            nats_url = os.getenv("NATS_URL", "nats://nats-service:4222")
            self.nats_service = NatsService(nats_url)
            
            if self.nats_service.start():
                print("NATS service started successfully")
            else:
                print("Warning: NATS service failed to start")
            
            # Initialize background interrogator
            self.interrogator = ClusterInterrogator(
                self.k8s_service, 
                self.cache, 
                self.nats_service,
                interval_seconds=30
            )
            self.interrogator.start()
            
            # Initialize API routes
            init_cluster_routes(self.k8s_service, self.cache, self.nats_service)
            init_cache_routes(self.cache, self.interrogator, self.nats_service)
            
            print("All services initialized successfully")
            
        except Exception as e:
            print(f"Failed to initialize services: {e}")
            raise
    
    def setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/health', methods=['GET'])
        def health_check():
            """Health check endpoint"""
            try:
                status = {
                    "status": "healthy",
                    "service": "python-k8s-manager",
                    "timestamp": int(time.time() * 1000),
                    "services": {
                        "kubernetes": self.k8s_service is not None,
                        "cache": self.cache is not None and self.cache.is_valid(),
                        "nats": self.nats_service is not None,
                        "interrogator": self.interrogator is not None and self.interrogator.is_running()
                    }
                }
                
                # Add cache stats if available
                if self.cache:
                    status["cache_stats"] = self.cache.get_stats()
                
                return jsonify(status)
                
            except Exception as e:
                return jsonify({
                    "status": "unhealthy",
                    "error": str(e)
                }), 500
        
        @self.app.route('/api/status', methods=['GET'])
        def get_status():
            """Detailed status endpoint"""
            try:
                status = {
                    "service": "python-k8s-manager",
                    "timestamp": int(time.time() * 1000),
                    "uptime": time.time() - self.start_time,
                    "services": {}
                }
                
                if self.k8s_service:
                    status["services"]["kubernetes"] = {"status": "connected"}
                
                if self.cache:
                    status["services"]["cache"] = self.cache.get_stats()
                
                if self.interrogator:
                    status["services"]["interrogator"] = self.interrogator.get_status()
                
                if self.nats_service:
                    status["services"]["nats"] = {"status": "connected"}
                
                return jsonify(status)
                
            except Exception as e:
                return jsonify({"error": str(e)}), 500
        
        # Register blueprints
        self.app.register_blueprint(cluster_bp)
        self.app.register_blueprint(cache_bp)
    
    def setup_signal_handlers(self):
        """Setup graceful shutdown"""
        def signal_handler(signum, frame):
            print("\nShutting down Python K8s Manager...")
            self.shutdown()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def shutdown(self):
        """Graceful shutdown"""
        try:
            if self.interrogator:
                self.interrogator.stop()
            
            if self.nats_service:
                self.nats_service.stop()
            
            print("Python K8s Manager shutdown complete")
            
        except Exception as e:
            print(f"Error during shutdown: {e}")
    
    def run(self, host='0.0.0.0', port=8080, debug=False):
        """Run the application"""
        self.start_time = time.time()
        
        try:
            self.initialize_services()
            self.setup_routes()
            self.setup_signal_handlers()
            
            print(f"Python K8s Manager starting on {host}:{port}")
            print("Available endpoints:")
            print("  GET  /health - Health check")
            print("  GET  /api/status - Detailed status")
            print("  GET  /api/cluster/info - Cluster information") 
            print("  GET  /api/cluster/pods - Pod information")
            print("  GET  /api/cluster/deployments - Deployment information")
            print("  GET  /api/cache/stats - Cache statistics")
            print("  POST /api/cache/refresh - Force cache refresh")
            print("  POST /api/cache/invalidate - Invalidate cache")
            
            # Publish startup event
            if self.nats_service:
                startup_event = {
                    "action": "service_started",
                    "service": "python-k8s-manager",
                    "timestamp": int(time.time() * 1000)
                }
                self.nats_service.publish_sync("k8s.events", startup_event)
            
            self.app.run(host=host, port=port, debug=debug)
            
        except Exception as e:
            print(f"Failed to start application: {e}")
            self.shutdown()
            raise

if __name__ == '__main__':
    import os
    manager = PythonK8sManager()
    manager.run(
        host='0.0.0.0',
        port=int(os.getenv('PORT', 8080)),
        debug=os.getenv('DEBUG', 'false').lower() == 'true'
    )
