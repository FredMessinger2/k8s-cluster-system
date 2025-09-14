from flask import Flask, render_template, jsonify, request
import requests
import json
from datetime import datetime

app = Flask(__name__)

# Configuration
K8S_MANAGER_URL = "http://k8s-manager-service:8080"
LOCAL_K8S_URL = "http://localhost:8080"  # Fallback for development

def get_k8s_api_url():
    """Determine which API URL to use"""
    try:
        # Try cluster service first
        response = requests.get(f"{K8S_MANAGER_URL}/health", timeout=2)
        if response.status_code == 200:
            return K8S_MANAGER_URL
    except:
        pass
    
    # Fallback to localhost for development
    try:
        response = requests.get(f"{LOCAL_K8S_URL}/health", timeout=2)
        if response.status_code == 200:
            return LOCAL_K8S_URL
    except:
        pass
    
    return None

@app.route('/')
def index():
    """Main dashboard"""
    return render_template('index.html')

@app.route('/cluster')
def cluster_view():
    """Cluster visualization page"""
    return render_template('cluster.html')

@app.route('/api/cluster-data')
def get_cluster_data():
    """Fetch cluster data from K8s manager"""
    api_url = get_k8s_api_url()
    if not api_url:
        return jsonify({"error": "K8s manager API not available"}), 503
    
    try:
        response = requests.get(f"{api_url}/api/cluster/info", timeout=10)
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({"error": f"API returned {response.status_code}"}), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/cache-stats')
def get_cache_stats():
    """Fetch cache statistics"""
    api_url = get_k8s_api_url()
    if not api_url:
        return jsonify({"error": "K8s manager API not available"}), 503
    
    try:
        response = requests.get(f"{api_url}/api/cache/stats", timeout=5)
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({"error": f"Cache API returned {response.status_code}"}), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/refresh-cache', methods=['POST'])
def refresh_cache():
    """Trigger cache refresh"""
    api_url = get_k8s_api_url()
    if not api_url:
        return jsonify({"error": "K8s manager API not available"}), 503
    
    try:
        response = requests.post(f"{api_url}/api/cache/refresh", timeout=5)
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({"error": f"Refresh API returned {response.status_code}"}), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    api_url = get_k8s_api_url()
    status = {
        "flask_ui": "healthy",
        "timestamp": datetime.now().isoformat(),
        "k8s_manager_available": api_url is not None,
        "k8s_manager_url": api_url
    }
    return jsonify(status)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
