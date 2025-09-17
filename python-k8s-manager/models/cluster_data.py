from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
from datetime import datetime

@dataclass
class PodInfo:
    name: str
    namespace: str
    status: str
    creation_timestamp: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class DeploymentInfo:
    name: str
    namespace: str
    replicas: Optional[int] = None
    ready_replicas: Optional[int] = None
    creation_timestamp: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class ClusterData:
    pods: List[PodInfo]
    deployments: List[DeploymentInfo]
    pod_count: int
    deployment_count: int
    fetch_timestamp: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "pods": [pod.to_dict() for pod in self.pods],
            "deployments": [deployment.to_dict() for deployment in self.deployments],
            "podCount": self.pod_count,
            "deploymentCount": self.deployment_count,
            "fetchTimestamp": self.fetch_timestamp
        }
