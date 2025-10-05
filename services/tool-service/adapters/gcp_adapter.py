"""
⚠️ WE DO NOT MOCK - Real Google Cloud SDK integration.

GCP Adapter for Cloud Services
Comprehensive Google Cloud Platform integration using official Python SDKs.
"""

from google.cloud import compute_v1, storage, sql_v1
from google.oauth2 import service_account
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class GCPAdapter:
    """
    Google Cloud Platform adapter for cloud infrastructure management.
    
    Documentation: https://cloud.google.com/python/docs/reference
    """
    
    def __init__(
        self,
        project_id: str,
        credentials_path: Optional[str] = None
    ):
        """
        Initialize GCP adapter.
        
        Args:
            project_id: GCP project ID
            credentials_path: Path to service account JSON file (optional)
        """
        self.project_id = project_id
        
        # Load credentials
        if credentials_path:
            self.credentials = service_account.Credentials.from_service_account_file(credentials_path)
            logger.info("GCP adapter initialized with service account")
        else:
            self.credentials = None  # Use default credentials
            logger.info("GCP adapter initialized with default credentials")
        
        # Initialize clients (lazy loading)
        self._compute_client = None
        self._storage_client = None
        self._sql_client = None
    
    @property
    def compute_client(self):
        """Lazy load compute client."""
        if not self._compute_client:
            self._compute_client = compute_v1.InstancesClient(credentials=self.credentials)
        return self._compute_client
    
    @property
    def storage_client(self):
        """Lazy load storage client."""
        if not self._storage_client:
            self._storage_client = storage.Client(
                project=self.project_id,
                credentials=self.credentials
            )
        return self._storage_client
    
    @property
    def sql_client(self):
        """Lazy load SQL admin client."""
        if not self._sql_client:
            self._sql_client = sql_v1.SqlInstancesServiceClient(credentials=self.credentials)
        return self._sql_client
    
    # ============================================================================
    # COMPUTE ENGINE (VMs)
    # ============================================================================
    
    def create_instance(
        self,
        zone: str,
        instance_name: str,
        machine_type: str = "e2-medium",
        source_image: str = "projects/debian-cloud/global/images/family/debian-11"
    ) -> Dict[str, Any]:
        """Create a Compute Engine instance."""
        machine_type_full = f"zones/{zone}/machineTypes/{machine_type}"
        
        instance = compute_v1.Instance()
        instance.name = instance_name
        instance.machine_type = machine_type_full
        
        # Boot disk
        disk = compute_v1.AttachedDisk()
        disk.boot = True
        disk.auto_delete = True
        disk.initialize_params = compute_v1.AttachedDiskInitializeParams()
        disk.initialize_params.source_image = source_image
        disk.initialize_params.disk_size_gb = 10
        instance.disks = [disk]
        
        # Network interface
        network_interface = compute_v1.NetworkInterface()
        network_interface.name = "global/networks/default"
        access_config = compute_v1.AccessConfig()
        access_config.name = "External NAT"
        access_config.type_ = "ONE_TO_ONE_NAT"
        network_interface.access_configs = [access_config]
        instance.network_interfaces = [network_interface]
        
        request = compute_v1.InsertInstanceRequest()
        request.zone = zone
        request.project = self.project_id
        request.instance_resource = instance
        
        operation = self.compute_client.insert(request=request)
        logger.info(f"Created instance: {instance_name}")
        return {"name": instance_name, "zone": zone, "operation": operation.name}
    
    def list_instances(self, zone: str) -> List[Dict[str, Any]]:
        """List all instances in a zone."""
        request = compute_v1.ListInstancesRequest()
        request.project = self.project_id
        request.zone = zone
        
        instances = []
        for instance in self.compute_client.list(request=request):
            instances.append({
                "name": instance.name,
                "status": instance.status,
                "machine_type": instance.machine_type,
                "zone": zone
            })
        return instances
    
    def stop_instance(self, zone: str, instance_name: str):
        """Stop an instance."""
        request = compute_v1.StopInstanceRequest()
        request.project = self.project_id
        request.zone = zone
        request.instance = instance_name
        
        self.compute_client.stop(request=request)
        logger.info(f"Stopped instance: {instance_name}")
    
    def start_instance(self, zone: str, instance_name: str):
        """Start an instance."""
        request = compute_v1.StartInstanceRequest()
        request.project = self.project_id
        request.zone = zone
        request.instance = instance_name
        
        self.compute_client.start(request=request)
        logger.info(f"Started instance: {instance_name}")
    
    def delete_instance(self, zone: str, instance_name: str):
        """Delete an instance."""
        request = compute_v1.DeleteInstanceRequest()
        request.project = self.project_id
        request.zone = zone
        request.instance = instance_name
        
        self.compute_client.delete(request=request)
        logger.info(f"Deleted instance: {instance_name}")
    
    # ============================================================================
    # CLOUD STORAGE
    # ============================================================================
    
    def create_bucket(self, bucket_name: str, location: str = "US") -> Dict[str, Any]:
        """Create a Cloud Storage bucket."""
        bucket = self.storage_client.bucket(bucket_name)
        bucket.storage_class = "STANDARD"
        bucket.location = location
        
        new_bucket = self.storage_client.create_bucket(bucket)
        logger.info(f"Created bucket: {bucket_name}")
        return {"name": new_bucket.name, "location": new_bucket.location}
    
    def list_buckets(self) -> List[Dict[str, Any]]:
        """List all buckets."""
        buckets = []
        for bucket in self.storage_client.list_buckets():
            buckets.append({
                "name": bucket.name,
                "location": bucket.location,
                "storage_class": bucket.storage_class
            })
        return buckets
    
    def upload_blob(self, bucket_name: str, source_file: str, destination_blob_name: str):
        """Upload a file to Cloud Storage."""
        bucket = self.storage_client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_filename(source_file)
        logger.info(f"Uploaded {source_file} to {bucket_name}/{destination_blob_name}")
    
    def download_blob(self, bucket_name: str, source_blob_name: str, destination_file: str):
        """Download a file from Cloud Storage."""
        bucket = self.storage_client.bucket(bucket_name)
        blob = bucket.blob(source_blob_name)
        blob.download_to_filename(destination_file)
        logger.info(f"Downloaded {bucket_name}/{source_blob_name} to {destination_file}")
    
    def delete_bucket(self, bucket_name: str):
        """Delete a bucket."""
        bucket = self.storage_client.bucket(bucket_name)
        bucket.delete()
        logger.info(f"Deleted bucket: {bucket_name}")
    
    # ============================================================================
    # CLOUD SQL
    # ============================================================================
    
    def create_sql_instance(
        self,
        instance_name: str,
        region: str = "us-central1",
        tier: str = "db-f1-micro",
        database_version: str = "POSTGRES_14"
    ) -> Dict[str, Any]:
        """Create a Cloud SQL instance."""
        instance = sql_v1.DatabaseInstance()
        instance.name = instance_name
        instance.database_version = database_version
        instance.region = region
        
        settings = sql_v1.Settings()
        settings.tier = tier
        instance.settings = settings
        
        request = sql_v1.InsertInstanceRequest()
        request.project = self.project_id
        request.body = instance
        
        operation = self.sql_client.insert(request=request)
        logger.info(f"Created SQL instance: {instance_name}")
        return {"name": instance_name, "region": region, "tier": tier}
    
    def list_sql_instances(self) -> List[Dict[str, Any]]:
        """List all SQL instances."""
        request = sql_v1.ListInstancesRequest()
        request.project = self.project_id
        
        instances = []
        for instance in self.sql_client.list(request=request):
            instances.append({
                "name": instance.name,
                "state": instance.state,
                "database_version": instance.database_version
            })
        return instances
    
    def delete_sql_instance(self, instance_name: str):
        """Delete a SQL instance."""
        request = sql_v1.DeleteInstanceRequest()
        request.project = self.project_id
        request.instance = instance_name
        
        self.sql_client.delete(request=request)
        logger.info(f"Deleted SQL instance: {instance_name}")
    
    # ============================================================================
    # UTILITIES
    # ============================================================================
    
    def bootstrap_infrastructure(
        self,
        project_name: str,
        region: str = "us-central1",
        zone: str = "us-central1-a"
    ) -> Dict[str, Any]:
        """Bootstrap complete GCP infrastructure for a project."""
        bucket_name = f"{self.project_id}-{project_name}-storage"
        
        # Create storage bucket
        bucket = self.create_bucket(bucket_name, location=region.upper())
        
        logger.info(f"Bootstrapped GCP infrastructure for '{project_name}'")
        
        return {
            "bucket": bucket,
            "region": region,
            "zone": zone
        }
