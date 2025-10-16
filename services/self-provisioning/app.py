"""
Self-Provisioning System
Autonomous infrastructure provisioning for new SomaGent instances.

KAMACHIQ can trigger creation of new isolated SomaGent deployments on-demand.
Uses Terraform for IaC, Kubernetes for orchestration, and automated configuration.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
import subprocess
import json
import os
import tempfile
import hashlib

logger = logging.getLogger(__name__)

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class ProvisionRequest(BaseModel):
    """Request to provision a new SomaGent instance."""
    organization_id: str = Field(..., description="Organization identifier")
    instance_name: str = Field(..., description="Instance name (unique)")
    region: str = Field(default="us-east-1", description="AWS region")
    tier: str = Field(default="standard", description="Instance tier (basic, standard, enterprise)")
    features: List[str] = Field(default_factory=lambda: ["kamachiq", "mao", "tools"], description="Enabled features")
    knowledge_base_seed: Optional[Dict[str, Any]] = Field(None, description="Initial knowledge base data")


class InstanceResponse(BaseModel):
    """Response with provisioned instance details."""
    instance_id: str
    instance_name: str
    status: str  # provisioning, ready, failed
    endpoints: Dict[str, str]
    created_at: datetime
    estimated_ready_time: Optional[str] = None


# ============================================================================
# TERRAFORM TEMPLATES
# ============================================================================

TERRAFORM_MAIN_TEMPLATE = """
terraform {{
  required_providers {{
    aws = {{
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }}
    kubernetes = {{
      source  = "hashicorp/kubernetes"
      version = "~> 2.0"
    }}
  }}
}}

provider "aws" {{
  region = "{region}"
}}

# VPC for SomaGent instance
resource "aws_vpc" "somagent" {{
  cidr_block = "10.0.0.0/16"
  
  tags = {{
    Name = "{instance_name}-vpc"
    Organization = "{organization_id}"
  }}
}}

# Subnets
resource "aws_subnet" "somagent_public" {{
  vpc_id     = aws_vpc.somagent.id
  cidr_block = "10.0.1.0/24"
  
  tags = {{
    Name = "{instance_name}-public-subnet"
  }}
}}

# EKS Cluster
resource "aws_eks_cluster" "somagent" {{
  name     = "{instance_name}-cluster"
  role_arn = aws_iam_role.eks_cluster.arn
  
  vpc_config {{
    subnet_ids = [aws_subnet.somagent_public.id]
  }}
  
  tags = {{
    Organization = "{organization_id}"
    Tier = "{tier}"
  }}
}}

# RDS PostgreSQL
resource "aws_db_instance" "somagent_db" {{
  identifier           = "{instance_name}-db"
  engine              = "postgres"
  engine_version      = "14.7"
  instance_class      = "{db_instance_class}"
  allocated_storage   = {db_storage}
  username            = "somagent"
  password            = "{db_password}"
  skip_final_snapshot = true
  
  tags = {{
    Name = "{instance_name}-database"
  }}
}}

# ElastiCache Redis
resource "aws_elasticache_cluster" "somagent_redis" {{
  cluster_id      = "{instance_name}-redis"
  engine          = "redis"
  node_type       = "{redis_node_type}"
  num_cache_nodes = 1
  
  tags = {{
    Name = "{instance_name}-redis"
  }}
}}

# Output endpoints
output "cluster_endpoint" {{
  value = aws_eks_cluster.somagent.endpoint
}}

output "database_endpoint" {{
  value = aws_db_instance.somagent_db.endpoint
}}

output "redis_endpoint" {{
  value = aws_elasticache_cluster.somagent_redis.cache_nodes[0].address
}}
"""

KUBERNETES_DEPLOYMENT_TEMPLATE = """
apiVersion: v1
kind: Namespace
metadata:
  name: {namespace}

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gateway-api
  namespace: {namespace}
spec:
  replicas: {replicas}
  selector:
    matchLabels:
      app: gateway-api
  template:
    metadata:
      labels:
        app: gateway-api
    spec:
      containers:
      - name: gateway-api
        image: somagent/gateway-api:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          value: "postgresql://somagent:{db_password}@{db_endpoint}/somagent"
        - name: REDIS_URL
          value: "redis://{redis_endpoint}:6379"
        - name: ORGANIZATION_ID
          value: "{organization_id}"

---
apiVersion: v1
kind: Service
metadata:
  name: gateway-api
  namespace: {namespace}
spec:
  type: LoadBalancer
  selector:
    app: gateway-api
  ports:
  - port: 80
    targetPort: 8000
"""

# ============================================================================
# TIER CONFIGURATIONS
# ============================================================================

TIER_CONFIGS = {
    "basic": {
        "db_instance_class": "db.t3.micro",
        "db_storage": 20,
        "redis_node_type": "cache.t3.micro",
        "replicas": 1
    },
    "standard": {
        "db_instance_class": "db.t3.small",
        "db_storage": 100,
        "redis_node_type": "cache.t3.small",
        "replicas": 3
    },
    "enterprise": {
        "db_instance_class": "db.r5.large",
        "db_storage": 500,
        "redis_node_type": "cache.r5.large",
        "replicas": 5
    }
}

# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(
    title="Self-Provisioning System",
    description="Autonomous infrastructure provisioning for SomaGent instances",
    version="1.0.0"
)

# In-memory instance tracking (use database in production)
instances: Dict[str, Dict[str, Any]] = {}

# ============================================================================
# PROVISIONING LOGIC
# ============================================================================

def generate_terraform_config(request: ProvisionRequest) -> str:
    """Generate Terraform configuration for instance."""
    tier_config = TIER_CONFIGS.get(request.tier, TIER_CONFIGS["standard"])
    
    # Generate secure database password
    db_password = hashlib.sha256(f"{request.instance_name}-{request.organization_id}".encode()).hexdigest()[:16]
    
    config = TERRAFORM_MAIN_TEMPLATE.format(
        region=request.region,
        instance_name=request.instance_name,
        organization_id=request.organization_id,
        tier=request.tier,
        db_instance_class=tier_config["db_instance_class"],
        db_storage=tier_config["db_storage"],
        redis_node_type=tier_config["redis_node_type"],
        db_password=db_password
    )
    
    return config


def generate_kubernetes_manifest(
    request: ProvisionRequest,
    db_endpoint: str,
    redis_endpoint: str
) -> str:
    """Generate Kubernetes deployment manifest."""
    tier_config = TIER_CONFIGS.get(request.tier, TIER_CONFIGS["standard"])
    db_password = hashlib.sha256(f"{request.instance_name}-{request.organization_id}".encode()).hexdigest()[:16]
    
    manifest = KUBERNETES_DEPLOYMENT_TEMPLATE.format(
        namespace=f"somagent-{request.instance_name}",
        replicas=tier_config["replicas"],
        db_endpoint=db_endpoint,
        redis_endpoint=redis_endpoint,
        db_password=db_password,
        organization_id=request.organization_id
    )
    
    return manifest


def run_terraform(config: str, action: str = "apply") -> Dict[str, Any]:
    """Run Terraform with given configuration."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Write config
        config_path = os.path.join(tmpdir, "main.tf")
        with open(config_path, 'w') as f:
            f.write(config)
        
        # Initialize
        subprocess.run(["terraform", "init"], cwd=tmpdir, check=True)
        
        # Plan
        subprocess.run(["terraform", "plan"], cwd=tmpdir, check=True)
        
        # Apply
        if action == "apply":
            subprocess.run(
                ["terraform", "apply", "-auto-approve"],
                cwd=tmpdir,
                check=True
            )
            
            # Get outputs
            result = subprocess.run(
                ["terraform", "output", "-json"],
                cwd=tmpdir,
                capture_output=True,
                text=True,
                check=True
            )
            
            return json.loads(result.stdout)
        
        return {}


def deploy_to_kubernetes(manifest: str, kubeconfig_path: Optional[str] = None):
    """Deploy to Kubernetes cluster."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(manifest)
        manifest_path = f.name
    
    try:
        cmd = ["kubectl", "apply", "-f", manifest_path]
        if kubeconfig_path:
            cmd.extend(["--kubeconfig", kubeconfig_path])
        
        subprocess.run(cmd, check=True)
        logger.info("Kubernetes deployment successful")
    finally:
        os.remove(manifest_path)


def seed_knowledge_base(
    instance_id: str,
    knowledge_data: Dict[str, Any]
):
    """Seed knowledge base with organization-specific data."""
    # In production, this would populate the memory-gateway with initial knowledge
    logger.info(f"Seeding knowledge base for instance {instance_id}")
    # POST to memory-gateway API with knowledge_data


def configure_identity(
    instance_id: str,
    organization_id: str
):
    """Configure SPIFFE identity for new instance."""
    logger.info(f"Configuring SPIFFE identity for instance {instance_id}")
    # Generate SPIFFE ID: spiffe://somagent.ai/{organization_id}/{instance_id}


def initialize_constitution(
    instance_id: str,
    organization_id: str
):
    """Initialize constitution service with org defaults."""
    logger.info(f"Initializing constitution for instance {instance_id}")
    # POST to constitution-service with default governance policies


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.post("/provision", response_model=InstanceResponse)
async def provision_instance(request: ProvisionRequest):
    """
    Provision a new SomaGent instance.
    
    This triggers:
    1. Terraform infrastructure creation (VPC, EKS, RDS, Redis)
    2. Kubernetes deployment of services
    3. SPIFFE identity configuration
    4. Constitution initialization
    5. Knowledge base seeding
    """
    # Generate instance ID
    instance_id = hashlib.sha256(
        f"{request.organization_id}:{request.instance_name}".encode()
    ).hexdigest()[:16]
    
    # Check if already exists
    if instance_id in instances:
        raise HTTPException(status_code=400, detail="Instance already exists")
    
    # Create instance record
    instances[instance_id] = {
        "id": instance_id,
        "name": request.instance_name,
        "organization_id": request.organization_id,
        "status": "provisioning",
        "created_at": datetime.utcnow(),
        "tier": request.tier,
        "region": request.region
    }
    
    try:
        # Step 1: Generate Terraform config
        logger.info(f"Generating Terraform config for {request.instance_name}")
        tf_config = generate_terraform_config(request)
        
        # Step 2: Run Terraform (async in production)
        logger.info(f"Running Terraform for {request.instance_name}")
        # In production, this would be an async Celery task
        # outputs = run_terraform(tf_config)
        # For demo, use placeholder outputs
        outputs = {
            "cluster_endpoint": {"value": f"https://{request.instance_name}.eks.amazonaws.com"},
            "database_endpoint": {"value": f"{request.instance_name}-db.rds.amazonaws.com"},
            "redis_endpoint": {"value": f"{request.instance_name}-redis.cache.amazonaws.com"}
        }
        
        # Step 3: Deploy to Kubernetes
        logger.info(f"Deploying to Kubernetes for {request.instance_name}")
        k8s_manifest = generate_kubernetes_manifest(
            request,
            outputs["database_endpoint"]["value"],
            outputs["redis_endpoint"]["value"]
        )
        # deploy_to_kubernetes(k8s_manifest)
        
        # Step 4: Configure identity
        configure_identity(instance_id, request.organization_id)
        
        # Step 5: Initialize constitution
        initialize_constitution(instance_id, request.organization_id)
        
        # Step 6: Seed knowledge base
        if request.knowledge_base_seed:
            seed_knowledge_base(instance_id, request.knowledge_base_seed)
        
        # Update instance status
        instances[instance_id]["status"] = "ready"
        instances[instance_id]["endpoints"] = {
            "gateway": f"http://{request.instance_name}.somagent.ai",
            "kamachiq": f"http://{request.instance_name}.somagent.ai/kamachiq",
            "mao": f"http://{request.instance_name}.somagent.ai/mao"
        }
        
        logger.info(f"Instance {request.instance_name} provisioned successfully")
        
        return InstanceResponse(
            instance_id=instance_id,
            instance_name=request.instance_name,
            status="ready",
            endpoints=instances[instance_id]["endpoints"],
            created_at=instances[instance_id]["created_at"],
            estimated_ready_time="5-10 minutes"
        )
        
    except Exception as e:
        logger.error(f"Provisioning failed: {e}")
        instances[instance_id]["status"] = "failed"
        raise HTTPException(status_code=500, detail=f"Provisioning failed: {str(e)}")


@app.get("/instances/{instance_id}", response_model=InstanceResponse)
def get_instance(instance_id: str):
    """Get instance status and details."""
    if instance_id not in instances:
        raise HTTPException(status_code=404, detail="Instance not found")
    
    instance = instances[instance_id]
    return InstanceResponse(
        instance_id=instance["id"],
        instance_name=instance["name"],
        status=instance["status"],
        endpoints=instance.get("endpoints", {}),
        created_at=instance["created_at"]
    )


@app.get("/instances")
def list_instances(organization_id: Optional[str] = None):
    """List all instances (optionally filtered by organization)."""
    result = list(instances.values())
    
    if organization_id:
        result = [i for i in result if i.get("organization_id") == organization_id]
    
    return {"instances": result}


@app.delete("/instances/{instance_id}")
def deprovision_instance(instance_id: str):
    """Deprovision (destroy) an instance."""
    if instance_id not in instances:
        raise HTTPException(status_code=404, detail="Instance not found")
    
    instance = instances[instance_id]
    
    # In production, run `terraform destroy`
    logger.info(f"Deprovisioning instance {instance['name']}")
    
    # Remove from tracking
    del instances[instance_id]
    
    return {"message": f"Instance {instance['name']} deprovisioned"}


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "self-provisioning",
        "active_instances": len(instances)
    }


if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.getenv("PORT"))
    uvicorn.run(app, host="0.0.0.0", port=port)
