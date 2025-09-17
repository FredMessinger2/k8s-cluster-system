from kubernetes import client, config
from kubernetes.client.rest import ApiException
from typing import List, Optional
import time
from models.cluster_data import ClusterData, PodInfo, DeploymentInfo

class KubernetesService:
    """Service for interacting with Kubernetes API"""
    
    def __init__(self):
        try:
            # Load in-cluster config
            config.load_incluster_config()
            print("Loaded in-cluster Kubernetes config")
        except:
            try:
                # Fallback to local config for development
                config.load_kube_config()
                print("Loaded local Kubernetes config")
            except Exception as e:
                print(f"Failed to load Kubernetes config: {e}")
                raise
        
        self.core_v1 = client.CoreV1Api()
        self.apps_v1 = client.AppsV1Api()
    
    def fetch_cluster_data(self) -> ClusterData:
        """Fetch cluster data from Kubernetes API"""
        try:
            start_time = time.time()
            print("Fetching cluster data from Kubernetes API...")
            
            # Fetch pods
            pods = self._fetch_pods()
            
            # Fetch deployments
            deployments = self._fetch_deployments()
            
            duration = time.time() - start_time
            print(f"Cluster data fetch completed in {duration:.2f}s - {len(pods)} pods, {len(deployments)} deployments")
            
            return ClusterData(
                pods=pods,
                deployments=deployments,
                pod_count=len(pods),
                deployment_count=len(deployments),
                fetch_timestamp=time.time()
            )
            
        except ApiException as e:
            print(f"Kubernetes API error: {e}")
            raise
        except Exception as e:
            print(f"Error fetching cluster data: {e}")
            raise
    
    def _fetch_pods(self) -> List[PodInfo]:
        """Fetch all pods from all namespaces"""
        try:
            pod_list = self.core_v1.list_pod_for_all_namespaces()
            pods = []
            
            for pod in pod_list.items:
                pod_info = PodInfo(
                    name=pod.metadata.name,
                    namespace=pod.metadata.namespace,
                    status=pod.status.phase or "Unknown",
                    creation_timestamp=pod.metadata.creation_timestamp.isoformat() if pod.metadata.creation_timestamp else None
                )
                pods.append(pod_info)
            
            return pods
            
        except ApiException as e:
            print(f"Error fetching pods: {e}")
            raise
    
    def _fetch_deployments(self) -> List[DeploymentInfo]:
        """Fetch all deployments from all namespaces"""
        try:
            deployment_list = self.apps_v1.list_deployment_for_all_namespaces()
            deployments = []
            
            for deployment in deployment_list.items:
                deployment_info = DeploymentInfo(
                    name=deployment.metadata.name,
                    namespace=deployment.metadata.namespace,
                    replicas=deployment.spec.replicas,
                    ready_replicas=deployment.status.ready_replicas,
                    creation_timestamp=deployment.metadata.creation_timestamp.isoformat() if deployment.metadata.creation_timestamp else None
                )
                deployments.append(deployment_info)
            
            return deployments
            
        except ApiException as e:
            print(f"Error fetching deployments: {e}")
            raise
