// API helper functions for Flask UI

class K8sAPI {
    constructor() {
        this.baseURL = '';
    }
    
    async get(endpoint) {
        try {
            const response = await fetch(endpoint);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return await response.json();
        } catch (error) {
            console.error(`API GET ${endpoint} failed:`, error);
            throw error;
        }
    }
    
    async post(endpoint, data = {}) {
        try {
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error(`API POST ${endpoint} failed:`, error);
            throw error;
        }
    }
    
    async getClusterData() {
        return this.get('/api/cluster-data');
    }
    
    async getCacheStats() {
        return this.get('/api/cache-stats');
    }
    
    async refreshCache() {
        return this.post('/api/refresh-cache');
    }
    
    async healthCheck() {
        return this.get('/api/health');
    }
}

// Global API instance
window.k8sAPI = new K8sAPI();
