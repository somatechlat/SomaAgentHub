"""
⚠️ WE DO NOT MOCK - Real Azure SDK integration.

Azure Adapter for Cloud Services
Comprehensive Azure cloud integration using official Python SDKs.
"""

from azure.identity import DefaultAzureCredential, ClientSecretCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.sql import SqlManagementClient
from azure.storage.blob import BlobServiceClient
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class AzureAdapter:
    """
    Azure adapter for cloud infrastructure management.
    
    Provides comprehensive Azure service integration using official SDKs.
    Documentation: https://docs.microsoft.com/en-us/azure/developer/python/
    """
    
    def __init__(
        self,
        subscription_id: str,
        tenant_id: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None
    ):
        """
        Initialize Azure adapter.
        
        Args:
            subscription_id: Azure subscription ID
            tenant_id: Azure AD tenant ID (optional, uses DefaultAzureCredential if not provided)
            client_id: Service principal client ID
            client_secret: Service principal secret
        """
        self.subscription_id = subscription_id
        
        # Authenticate
        if tenant_id and client_id and client_secret:
            self.credential = ClientSecretCredential(
                tenant_id=tenant_id,
                client_id=client_id,
                client_secret=client_secret
            )
            logger.info("Azure adapter initialized with service principal")
        else:
            self.credential = DefaultAzureCredential()
            logger.info("Azure adapter initialized with default credentials")
        
        # Initialize clients (lazy loading)
        self._compute_client = None
        self._storage_client = None
        self._resource_client = None
        self._network_client = None
        self._sql_client = None
    
    @property
    def compute_client(self):
        """Lazy load compute client."""
        if not self._compute_client:
            self._compute_client = ComputeManagementClient(self.credential, self.subscription_id)
        return self._compute_client
    
    @property
    def storage_client(self):
        """Lazy load storage client."""
        if not self._storage_client:
            self._storage_client = StorageManagementClient(self.credential, self.subscription_id)
        return self._storage_client
    
    @property
    def resource_client(self):
        """Lazy load resource client."""
        if not self._resource_client:
            self._resource_client = ResourceManagementClient(self.credential, self.subscription_id)
        return self._resource_client
    
    @property
    def network_client(self):
        """Lazy load network client."""
        if not self._network_client:
            self._network_client = NetworkManagementClient(self.credential, self.subscription_id)
        return self._network_client
    
    @property
    def sql_client(self):
        """Lazy load SQL client."""
        if not self._sql_client:
            self._sql_client = SqlManagementClient(self.credential, self.subscription_id)
        return self._sql_client
    
    # ============================================================================
    # RESOURCE GROUPS
    # ============================================================================
    
    def create_resource_group(self, name: str, location: str, tags: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Create a resource group."""
        parameters = {"location": location}
        if tags:
            parameters["tags"] = tags
        
        rg = self.resource_client.resource_groups.create_or_update(name, parameters)
        logger.info(f"Created resource group: {rg.name}")
        return rg.as_dict()
    
    def list_resource_groups(self) -> List[Dict[str, Any]]:
        """List all resource groups."""
        return [rg.as_dict() for rg in self.resource_client.resource_groups.list()]
    
    def delete_resource_group(self, name: str):
        """Delete a resource group."""
        poller = self.resource_client.resource_groups.begin_delete(name)
        poller.wait()
        logger.info(f"Deleted resource group: {name}")
    
    # ============================================================================
    # VIRTUAL MACHINES
    # ============================================================================
    
    def create_vm(
        self,
        resource_group: str,
        vm_name: str,
        location: str,
        vm_size: str = "Standard_B2s",
        admin_username: str = "azureuser",
        admin_password: Optional[str] = None,
        image_reference: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Create a virtual machine."""
        # Default to Ubuntu if no image specified
        if not image_reference:
            image_reference = {
                "publisher": "Canonical",
                "offer": "UbuntuServer",
                "sku": "18.04-LTS",
                "version": "latest"
            }
        
        vm_parameters = {
            "location": location,
            "hardware_profile": {"vm_size": vm_size},
            "storage_profile": {
                "image_reference": image_reference
            },
            "os_profile": {
                "computer_name": vm_name,
                "admin_username": admin_username,
                "admin_password": admin_password
            },
            "network_profile": {
                "network_interfaces": []  # Would need NIC creation first
            }
        }
        
        poller = self.compute_client.virtual_machines.begin_create_or_update(
            resource_group, vm_name, vm_parameters
        )
        vm = poller.result()
        logger.info(f"Created VM: {vm.name}")
        return vm.as_dict()
    
    def list_vms(self, resource_group: Optional[str] = None) -> List[Dict[str, Any]]:
        """List virtual machines."""
        if resource_group:
            vms = self.compute_client.virtual_machines.list(resource_group)
        else:
            vms = self.compute_client.virtual_machines.list_all()
        return [vm.as_dict() for vm in vms]
    
    def start_vm(self, resource_group: str, vm_name: str):
        """Start a VM."""
        poller = self.compute_client.virtual_machines.begin_start(resource_group, vm_name)
        poller.wait()
        logger.info(f"Started VM: {vm_name}")
    
    def stop_vm(self, resource_group: str, vm_name: str):
        """Stop a VM."""
        poller = self.compute_client.virtual_machines.begin_power_off(resource_group, vm_name)
        poller.wait()
        logger.info(f"Stopped VM: {vm_name}")
    
    def delete_vm(self, resource_group: str, vm_name: str):
        """Delete a VM."""
        poller = self.compute_client.virtual_machines.begin_delete(resource_group, vm_name)
        poller.wait()
        logger.info(f"Deleted VM: {vm_name}")
    
    # ============================================================================
    # STORAGE ACCOUNTS
    # ============================================================================
    
    def create_storage_account(
        self,
        resource_group: str,
        account_name: str,
        location: str,
        sku: str = "Standard_LRS",
        kind: str = "StorageV2"
    ) -> Dict[str, Any]:
        """Create a storage account."""
        parameters = {
            "location": location,
            "sku": {"name": sku},
            "kind": kind
        }
        
        poller = self.storage_client.storage_accounts.begin_create(
            resource_group, account_name, parameters
        )
        account = poller.result()
        logger.info(f"Created storage account: {account.name}")
        return account.as_dict()
    
    def list_storage_accounts(self, resource_group: Optional[str] = None) -> List[Dict[str, Any]]:
        """List storage accounts."""
        if resource_group:
            accounts = self.storage_client.storage_accounts.list_by_resource_group(resource_group)
        else:
            accounts = self.storage_client.storage_accounts.list()
        return [acc.as_dict() for acc in accounts]
    
    def delete_storage_account(self, resource_group: str, account_name: str):
        """Delete a storage account."""
        self.storage_client.storage_accounts.delete(resource_group, account_name)
        logger.info(f"Deleted storage account: {account_name}")
    
    # ============================================================================
    # BLOB STORAGE
    # ============================================================================
    
    def upload_blob(
        self,
        storage_account: str,
        container_name: str,
        blob_name: str,
        data: bytes
    ):
        """Upload data to blob storage."""
        # Get connection string (simplified - in production use proper key management)
        blob_service = BlobServiceClient(
            account_url=f"https://{storage_account}.blob.core.windows.net",
            credential=self.credential
        )
        
        blob_client = blob_service.get_blob_client(container_name, blob_name)
        blob_client.upload_blob(data, overwrite=True)
        logger.info(f"Uploaded blob: {blob_name}")
    
    def download_blob(
        self,
        storage_account: str,
        container_name: str,
        blob_name: str
    ) -> bytes:
        """Download data from blob storage."""
        blob_service = BlobServiceClient(
            account_url=f"https://{storage_account}.blob.core.windows.net",
            credential=self.credential
        )
        
        blob_client = blob_service.get_blob_client(container_name, blob_name)
        return blob_client.download_blob().readall()
    
    # ============================================================================
    # SQL DATABASES
    # ============================================================================
    
    def create_sql_server(
        self,
        resource_group: str,
        server_name: str,
        location: str,
        admin_login: str,
        admin_password: str
    ) -> Dict[str, Any]:
        """Create a SQL server."""
        parameters = {
            "location": location,
            "administrator_login": admin_login,
            "administrator_login_password": admin_password
        }
        
        poller = self.sql_client.servers.begin_create_or_update(
            resource_group, server_name, parameters
        )
        server = poller.result()
        logger.info(f"Created SQL server: {server.name}")
        return server.as_dict()
    
    def create_sql_database(
        self,
        resource_group: str,
        server_name: str,
        database_name: str,
        sku: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Create a SQL database."""
        if not sku:
            sku = {"name": "S0", "tier": "Standard"}
        
        parameters = {"sku": sku}
        
        poller = self.sql_client.databases.begin_create_or_update(
            resource_group, server_name, database_name, parameters
        )
        database = poller.result()
        logger.info(f"Created SQL database: {database.name}")
        return database.as_dict()
    
    # ============================================================================
    # UTILITIES
    # ============================================================================
    
    def bootstrap_infrastructure(
        self,
        project_name: str,
        location: str = "eastus"
    ) -> Dict[str, Any]:
        """Bootstrap complete Azure infrastructure for a project."""
        rg_name = f"{project_name}-rg"
        
        # Create resource group
        rg = self.create_resource_group(rg_name, location, tags={"project": project_name})
        
        # Create storage account
        storage_name = f"{project_name.replace('-', '')}storage"[:24]  # Max 24 chars
        storage = self.create_storage_account(rg_name, storage_name, location)
        
        logger.info(f"Bootstrapped Azure infrastructure for '{project_name}'")
        
        return {
            "resource_group": rg,
            "storage_account": storage
        }
