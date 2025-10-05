"""
⚠️ WE DO NOT MOCK - Real Kubernetes adapter using official Python client.

Provides comprehensive K8s integration:
- Deployments
- Services
- Pods
- ConfigMaps & Secrets
- Namespaces
- Ingress
- StatefulSets
- Jobs & CronJobs
"""

from kubernetes import client, config
from kubernetes.client.rest import ApiException
from typing import Dict, List, Any, Optional
import logging
import yaml

logger = logging.getLogger(__name__)


class KubernetesAdapter:
    """
    Adapter for Kubernetes operations.
    
    K8s Documentation: https://kubernetes.io/docs
    """
    
    def __init__(
        self,
        kubeconfig_path: Optional[str] = None,
        context: Optional[str] = None,
        in_cluster: bool = False
    ):
        """
        Initialize Kubernetes adapter.
        
        Args:
            kubeconfig_path: Path to kubeconfig file
            context: Kubernetes context to use
            in_cluster: Use in-cluster configuration
        """
        if in_cluster:
            config.load_incluster_config()
        else:
            config.load_kube_config(
                config_file=kubeconfig_path,
                context=context
            )
        
        # Initialize API clients
        self.core_v1 = client.CoreV1Api()
        self.apps_v1 = client.AppsV1Api()
        self.batch_v1 = client.BatchV1Api()
        self.networking_v1 = client.NetworkingV1Api()
        self.rbac_v1 = client.RbacAuthorizationV1Api()
    
    # Namespace Operations
    
    def create_namespace(self, name: str, labels: Optional[Dict[str, str]] = None) -> Any:
        """Create namespace."""
        logger.info(f"Creating namespace: {name}")
        
        metadata = client.V1ObjectMeta(name=name, labels=labels or {})
        namespace = client.V1Namespace(metadata=metadata)
        
        return self.core_v1.create_namespace(body=namespace)
    
    def list_namespaces(self) -> List[Any]:
        """List all namespaces."""
        response = self.core_v1.list_namespace()
        return response.items
    
    def delete_namespace(self, name: str) -> Any:
        """Delete namespace."""
        logger.warning(f"Deleting namespace: {name}")
        return self.core_v1.delete_namespace(name=name)
    
    # Deployment Operations
    
    def create_deployment(
        self,
        name: str,
        namespace: str,
        image: str,
        replicas: int = 1,
        labels: Optional[Dict[str, str]] = None,
        env_vars: Optional[Dict[str, str]] = None,
        ports: Optional[List[int]] = None,
        resources: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Create deployment.
        
        Args:
            name: Deployment name
            namespace: Namespace
            image: Container image
            replicas: Number of replicas
            labels: Pod labels
            env_vars: Environment variables
            ports: Container ports
            resources: Resource requests/limits
            
        Returns:
            Created deployment
        """
        logger.info(f"Creating deployment: {name} in {namespace}")
        
        labels = labels or {"app": name}
        
        # Build container spec
        container = client.V1Container(
            name=name,
            image=image,
            ports=[client.V1ContainerPort(container_port=p) for p in (ports or [])],
        )
        
        # Add environment variables
        if env_vars:
            container.env = [
                client.V1EnvVar(name=k, value=v)
                for k, v in env_vars.items()
            ]
        
        # Add resources
        if resources:
            container.resources = client.V1ResourceRequirements(**resources)
        
        # Build pod template
        template = client.V1PodTemplateSpec(
            metadata=client.V1ObjectMeta(labels=labels),
            spec=client.V1PodSpec(containers=[container])
        )
        
        # Build deployment spec
        spec = client.V1DeploymentSpec(
            replicas=replicas,
            selector=client.V1LabelSelector(match_labels=labels),
            template=template
        )
        
        # Build deployment
        deployment = client.V1Deployment(
            api_version="apps/v1",
            kind="Deployment",
            metadata=client.V1ObjectMeta(name=name),
            spec=spec
        )
        
        return self.apps_v1.create_namespaced_deployment(
            namespace=namespace,
            body=deployment
        )
    
    def list_deployments(self, namespace: str) -> List[Any]:
        """List deployments in namespace."""
        response = self.apps_v1.list_namespaced_deployment(namespace=namespace)
        return response.items
    
    def scale_deployment(
        self,
        name: str,
        namespace: str,
        replicas: int
    ) -> Any:
        """Scale deployment."""
        logger.info(f"Scaling deployment {name} to {replicas} replicas")
        
        # Get current deployment
        deployment = self.apps_v1.read_namespaced_deployment(name, namespace)
        
        # Update replicas
        deployment.spec.replicas = replicas
        
        return self.apps_v1.patch_namespaced_deployment(
            name=name,
            namespace=namespace,
            body=deployment
        )
    
    def delete_deployment(self, name: str, namespace: str) -> Any:
        """Delete deployment."""
        logger.warning(f"Deleting deployment: {name}")
        return self.apps_v1.delete_namespaced_deployment(
            name=name,
            namespace=namespace
        )
    
    # Service Operations
    
    def create_service(
        self,
        name: str,
        namespace: str,
        selector: Dict[str, str],
        ports: List[Dict[str, Any]],
        service_type: str = "ClusterIP"
    ) -> Any:
        """
        Create service.
        
        Args:
            name: Service name
            namespace: Namespace
            selector: Pod selector
            ports: Service ports (list of {port, targetPort, protocol})
            service_type: Service type (ClusterIP, NodePort, LoadBalancer)
        """
        logger.info(f"Creating service: {name}")
        
        service_ports = [
            client.V1ServicePort(
                port=p.get("port"),
                target_port=p.get("targetPort"),
                protocol=p.get("protocol", "TCP"),
                name=p.get("name")
            )
            for p in ports
        ]
        
        spec = client.V1ServiceSpec(
            selector=selector,
            ports=service_ports,
            type=service_type
        )
        
        service = client.V1Service(
            api_version="v1",
            kind="Service",
            metadata=client.V1ObjectMeta(name=name),
            spec=spec
        )
        
        return self.core_v1.create_namespaced_service(
            namespace=namespace,
            body=service
        )
    
    def list_services(self, namespace: str) -> List[Any]:
        """List services in namespace."""
        response = self.core_v1.list_namespaced_service(namespace=namespace)
        return response.items
    
    def delete_service(self, name: str, namespace: str) -> Any:
        """Delete service."""
        return self.core_v1.delete_namespaced_service(name=name, namespace=namespace)
    
    # Pod Operations
    
    def list_pods(
        self,
        namespace: str,
        label_selector: Optional[str] = None
    ) -> List[Any]:
        """List pods in namespace."""
        kwargs = {"namespace": namespace}
        if label_selector:
            kwargs["label_selector"] = label_selector
        
        response = self.core_v1.list_namespaced_pod(**kwargs)
        return response.items
    
    def get_pod_logs(
        self,
        name: str,
        namespace: str,
        container: Optional[str] = None,
        tail_lines: Optional[int] = None
    ) -> str:
        """Get pod logs."""
        kwargs = {"name": name, "namespace": namespace}
        
        if container:
            kwargs["container"] = container
        if tail_lines:
            kwargs["tail_lines"] = tail_lines
        
        return self.core_v1.read_namespaced_pod_log(**kwargs)
    
    def delete_pod(self, name: str, namespace: str) -> Any:
        """Delete pod."""
        return self.core_v1.delete_namespaced_pod(name=name, namespace=namespace)
    
    # ConfigMap Operations
    
    def create_configmap(
        self,
        name: str,
        namespace: str,
        data: Dict[str, str]
    ) -> Any:
        """Create ConfigMap."""
        logger.info(f"Creating ConfigMap: {name}")
        
        configmap = client.V1ConfigMap(
            api_version="v1",
            kind="ConfigMap",
            metadata=client.V1ObjectMeta(name=name),
            data=data
        )
        
        return self.core_v1.create_namespaced_config_map(
            namespace=namespace,
            body=configmap
        )
    
    def update_configmap(
        self,
        name: str,
        namespace: str,
        data: Dict[str, str]
    ) -> Any:
        """Update ConfigMap."""
        configmap = self.core_v1.read_namespaced_config_map(name, namespace)
        configmap.data = data
        
        return self.core_v1.patch_namespaced_config_map(
            name=name,
            namespace=namespace,
            body=configmap
        )
    
    # Secret Operations
    
    def create_secret(
        self,
        name: str,
        namespace: str,
        data: Dict[str, str],
        secret_type: str = "Opaque"
    ) -> Any:
        """Create Secret."""
        logger.info(f"Creating Secret: {name}")
        
        # Base64 encode values
        import base64
        encoded_data = {
            k: base64.b64encode(v.encode()).decode()
            for k, v in data.items()
        }
        
        secret = client.V1Secret(
            api_version="v1",
            kind="Secret",
            metadata=client.V1ObjectMeta(name=name),
            type=secret_type,
            data=encoded_data
        )
        
        return self.core_v1.create_namespaced_secret(
            namespace=namespace,
            body=secret
        )
    
    # Ingress Operations
    
    def create_ingress(
        self,
        name: str,
        namespace: str,
        rules: List[Dict[str, Any]],
        tls: Optional[List[Dict[str, Any]]] = None
    ) -> Any:
        """Create Ingress."""
        logger.info(f"Creating Ingress: {name}")
        
        # Build ingress rules
        ingress_rules = []
        for rule in rules:
            paths = [
                client.V1HTTPIngressPath(
                    path=p.get("path", "/"),
                    path_type=p.get("pathType", "Prefix"),
                    backend=client.V1IngressBackend(
                        service=client.V1IngressServiceBackend(
                            name=p.get("serviceName"),
                            port=client.V1ServiceBackendPort(number=p.get("servicePort"))
                        )
                    )
                )
                for p in rule.get("paths", [])
            ]
            
            ingress_rules.append(
                client.V1IngressRule(
                    host=rule.get("host"),
                    http=client.V1HTTPIngressRuleValue(paths=paths)
                )
            )
        
        spec = client.V1IngressSpec(rules=ingress_rules)
        
        # Add TLS if provided
        if tls:
            spec.tls = [
                client.V1IngressTLS(
                    hosts=t.get("hosts", []),
                    secret_name=t.get("secretName")
                )
                for t in tls
            ]
        
        ingress = client.V1Ingress(
            api_version="networking.k8s.io/v1",
            kind="Ingress",
            metadata=client.V1ObjectMeta(name=name),
            spec=spec
        )
        
        return self.networking_v1.create_namespaced_ingress(
            namespace=namespace,
            body=ingress
        )
    
    # Utility Methods
    
    def apply_yaml(self, yaml_content: str, namespace: str) -> List[Any]:
        """
        Apply Kubernetes YAML configuration.
        
        Args:
            yaml_content: YAML configuration
            namespace: Target namespace
            
        Returns:
            List of created resources
        """
        logger.info("Applying YAML configuration")
        
        resources = yaml.safe_load_all(yaml_content)
        results = []
        
        for resource in resources:
            if not resource:
                continue
            
            kind = resource.get("kind")
            metadata = resource.get("metadata", {})
            name = metadata.get("name")
            
            logger.info(f"Creating {kind}: {name}")
            
            # Route to appropriate API based on kind
            if kind == "Deployment":
                result = self.apps_v1.create_namespaced_deployment(
                    namespace=namespace,
                    body=resource
                )
            elif kind == "Service":
                result = self.core_v1.create_namespaced_service(
                    namespace=namespace,
                    body=resource
                )
            elif kind == "ConfigMap":
                result = self.core_v1.create_namespaced_config_map(
                    namespace=namespace,
                    body=resource
                )
            else:
                logger.warning(f"Unsupported resource kind: {kind}")
                continue
            
            results.append(result)
        
        return results
    
    def bootstrap_namespace(
        self,
        namespace: str,
        labels: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Bootstrap a namespace with common resources.
        
        Args:
            namespace: Namespace name
            labels: Namespace labels
            
        Returns:
            Created resources
        """
        logger.info(f"Bootstrapping namespace: {namespace}")
        
        results = {}
        
        # Create namespace
        results["namespace"] = self.create_namespace(namespace, labels)
        
        logger.info(f"Namespace {namespace} ready")
        return results
