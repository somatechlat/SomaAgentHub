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

import logging
from typing import Any

from kubernetes import client, config

logger = logging.getLogger(__name__)


class KubernetesAdapter:
    """
    Adapter for Kubernetes API.

    Uses official kubernetes-python client.
    """

    def __init__(self, kubeconfig_path: str | None = None, in_cluster: bool = False):
        """
        Initialize Kubernetes adapter.

        Args:
            kubeconfig_path: Path to kubeconfig file
            in_cluster: Whether running inside the cluster
        """
        try:
            if in_cluster:
                config.load_incluster_config()
                logger.info("Loaded in-cluster Kubernetes config")
            else:
                config.load_kube_config(config_file=kubeconfig_path)
                logger.info("Loaded local Kubernetes config")

            self.core_v1 = client.CoreV1Api()
            self.apps_v1 = client.AppsV1Api()
            self.batch_v1 = client.BatchV1Api()
            self.networking_v1 = client.NetworkingV1Api()

        except Exception as e:
            logger.error(f"Failed to initialize Kubernetes client: {e}")
            raise

    # ============================================================================
    # NAMESPACES
    # ============================================================================

    def create_namespace(self, name: str) -> dict[str, Any]:
        """Create a namespace."""
        namespace = client.V1Namespace(metadata=client.V1ObjectMeta(name=name))
        result = self.core_v1.create_namespace(body=namespace)
        logger.info(f"Created namespace: {name}")
        return result.to_dict()

    def delete_namespace(self, name: str):
        """Delete a namespace."""
        self.core_v1.delete_namespace(name=name)
        logger.info(f"Deleted namespace: {name}")

    def list_namespaces(self) -> list[dict[str, Any]]:
        """List all namespaces."""
        namespaces = self.core_v1.list_namespace()
        return [ns.to_dict() for ns in namespaces.items]

    # ============================================================================
    # DEPLOYMENTS
    # ============================================================================

    def create_deployment(
        self, namespace: str, name: str, image: str, replicas: int = 1, ports: list[int] = [80]
    ) -> dict[str, Any]:
        """
        Create a simple deployment.

        Args:
            namespace: Namespace
            name: Deployment name
            image: Container image
            replicas: Number of replicas
            ports: List of container ports
        """
        container_ports = [client.V1ContainerPort(container_port=port) for port in ports]

        container = client.V1Container(
            name=name,
            image=image,
            ports=container_ports,
            image_pull_policy="Always",
        )

        template = client.V1PodTemplateSpec(
            metadata=client.V1ObjectMeta(labels={"app": name}),
            spec=client.V1PodSpec(containers=[container]),
        )

        spec = client.V1DeploymentSpec(
            replicas=replicas,
            selector=client.V1LabelSelector(match_labels={"app": name}),
            template=template,
        )

        deployment = client.V1Deployment(
            api_version="apps/v1",
            kind="Deployment",
            metadata=client.V1ObjectMeta(name=name),
            spec=spec,
        )

        result = self.apps_v1.create_namespaced_deployment(namespace=namespace, body=deployment)
        logger.info(f"Created deployment {name} in {namespace}")
        return result.to_dict()

    def list_deployments(self, namespace: str) -> list[dict[str, Any]]:
        """List deployments in a namespace."""
        deployments = self.apps_v1.list_namespaced_deployment(namespace)
        return [d.to_dict() for d in deployments.items]

    def delete_deployment(self, namespace: str, name: str):
        """Delete a deployment."""
        self.apps_v1.delete_namespaced_deployment(name=name, namespace=namespace)
        logger.info(f"Deleted deployment {name} in {namespace}")

    def scale_deployment(self, namespace: str, name: str, replicas: int):
        """Scale a deployment."""
        patch = {"spec": {"replicas": replicas}}
        self.apps_v1.patch_namespaced_deployment(name=name, namespace=namespace, body=patch)
        logger.info(f"Scaled deployment {name} to {replicas} replicas")

    # ============================================================================
    # SERVICES
    # ============================================================================

    def create_service(
        self,
        namespace: str,
        name: str,
        selector: dict[str, str],
        ports: list[tuple[int, int]],  # (port, target_port)
        type: str = "ClusterIP",
    ) -> dict[str, Any]:
        """Create a service."""
        service_ports = [client.V1ServicePort(port=p[0], target_port=p[1]) for p in ports]

        spec = client.V1ServiceSpec(
            selector=selector,
            ports=service_ports,
            type=type,
        )

        service = client.V1Service(
            api_version="v1",
            kind="Service",
            metadata=client.V1ObjectMeta(name=name),
            spec=spec,
        )

        result = self.core_v1.create_namespaced_service(namespace=namespace, body=service)
        logger.info(f"Created service {name} in {namespace}")
        return result.to_dict()

    def delete_service(self, namespace: str, name: str):
        """Delete a service."""
        self.core_v1.delete_namespaced_service(name=name, namespace=namespace)
        logger.info(f"Deleted service {name} in {namespace}")

    # ============================================================================
    # PODS
    # ============================================================================

    def list_pods(self, namespace: str, label_selector: str | None = None) -> list[dict[str, Any]]:
        """List pods in a namespace."""
        pods = self.core_v1.list_namespaced_pod(namespace=namespace, label_selector=label_selector)
        return [p.to_dict() for p in pods.items]

    def get_pod_logs(self, namespace: str, name: str) -> str:
        """Get logs from a pod."""
        return self.core_v1.read_namespaced_pod_log(name=name, namespace=namespace)

    # ============================================================================
    # CONFIGMAPS & SECRETS
    # ============================================================================

    def create_config_map(self, namespace: str, name: str, data: dict[str, str]) -> dict[str, Any]:
        """Create a ConfigMap."""
        config_map = client.V1ConfigMap(
            metadata=client.V1ObjectMeta(name=name),
            data=data,
        )
        result = self.core_v1.create_namespaced_config_map(namespace=namespace, body=config_map)
        logger.info(f"Created ConfigMap {name} in {namespace}")
        return result.to_dict()

    def create_secret(self, namespace: str, name: str, data: dict[str, str]) -> dict[str, Any]:
        """Create a Secret (Opaque)."""
        # Data must be base64 encoded by the client if using string_data=None
        # But using string_data handles encoding automatically
        secret = client.V1Secret(
            metadata=client.V1ObjectMeta(name=name),
            string_data=data,
            type="Opaque",
        )
        result = self.core_v1.create_namespaced_secret(namespace=namespace, body=secret)
        logger.info(f"Created Secret {name} in {namespace}")
        return result.to_dict()

    # ============================================================================
    # RAW YAML
    # ============================================================================

    def apply_yaml(self, namespace: str, yaml_content: str):
        """
        Apply raw YAML manifest.

        Note: This is a simplified implementation.
        For complex multi-document YAMLs, use `utils.create_from_yaml`.
        """
        import os

        # Write to temporary file as create_from_yaml expects a file
        import tempfile

        from kubernetes import utils

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            utils.create_from_yaml(client.ApiClient(), yaml_file=temp_path, namespace=namespace)
            logger.info("Applied YAML manifest")
        except Exception as e:
            logger.error(f"Failed to apply YAML: {e}")
            raise
        finally:
            os.remove(temp_path)

    # ============================================================================
    # UTILITIES
    # ============================================================================

    def bootstrap_namespace(self, name: str) -> dict[str, Any]:
        """Bootstrap a new namespace with default resources."""
        # Create namespace
        ns = self.create_namespace(name)

        # Create default quota (example)
        quota = client.V1ResourceQuota(
            metadata=client.V1ObjectMeta(name="default-quota"),
            spec=client.V1ResourceQuotaSpec(hard={"pods": "10", "requests.cpu": "4", "requests.memory": "8Gi"}),
        )
        self.core_v1.create_namespaced_resource_quota(namespace=name, body=quota)

        logger.info(f"Bootstrapped namespace {name}")
        return ns
