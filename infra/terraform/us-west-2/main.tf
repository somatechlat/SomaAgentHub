# SomaAgent US-West-2 Region Deployment
# Primary region for North America

terraform {
  required_version = ">= 1.5"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  backend "s3" {
    bucket         = "somaagent-terraform-state"
    key            = "us-west-2/terraform.tfstate"
    region         = "us-west-2"
    encrypt        = true
    dynamodb_table = "terraform-state-lock"
  }
}

provider "aws" {
  region = "us-west-2"
  
  default_tags {
    tags = {
      Environment = terraform.workspace
      Region      = "us-west-2"
      ManagedBy   = "Terraform"
      Project     = "SomaAgent"
    }
  }
}

# Local variables
locals {
  region = "us-west-2"
  cluster_name = "somaagent-${local.region}"
  vpc_cidr = "10.0.0.0/16"
}

# VPC
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "${local.cluster_name}-vpc"
  cidr = local.vpc_cidr

  azs             = ["us-west-2a", "us-west-2b", "us-west-2c"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]

  enable_nat_gateway   = true
  single_nat_gateway   = false
  enable_dns_hostnames = true
  enable_dns_support   = true

  public_subnet_tags = {
    "kubernetes.io/role/elb" = 1
  }

  private_subnet_tags = {
    "kubernetes.io/role/internal-elb" = 1
  }

  tags = {
    Name = "${local.cluster_name}-vpc"
  }
}

# EKS Cluster
module "eks" {
  source = "../../modules/eks-cluster"

  cluster_name    = local.cluster_name
  cluster_version = "1.28"
  vpc_id          = module.vpc.vpc_id
  subnet_ids      = module.vpc.private_subnets
  region          = local.region

  node_groups = {
    system = {
      desired_size   = 2
      max_size       = 4
      min_size       = 2
      instance_types = ["t3.large"]
      capacity_type  = "ON_DEMAND"
      disk_size      = 50
    }
    application = {
      desired_size   = 4
      max_size       = 12
      min_size       = 3
      instance_types = ["t3.xlarge", "t3a.xlarge"]
      capacity_type  = "SPOT"
      disk_size      = 100
    }
  }
}

# RDS PostgreSQL (for regional data)
resource "aws_db_subnet_group" "main" {
  name       = "${local.cluster_name}-db-subnet"
  subnet_ids = module.vpc.private_subnets

  tags = {
    Name = "${local.cluster_name}-db-subnet"
  }
}

resource "aws_db_instance" "postgres" {
  identifier = "${local.cluster_name}-postgres"

  engine               = "postgres"
  engine_version       = "15.4"
  instance_class       = "db.r6g.xlarge"
  allocated_storage    = 100
  max_allocated_storage = 500

  db_name  = "somaagent"
  username = "postgres"
  password = random_password.db_password.result

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]

  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "mon:04:00-mon:05:00"

  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]

  storage_encrypted = true
  kms_key_id       = aws_kms_key.rds.arn

  skip_final_snapshot       = false
  final_snapshot_identifier = "${local.cluster_name}-postgres-final"

  tags = {
    Name = "${local.cluster_name}-postgres"
  }
}

resource "random_password" "db_password" {
  length  = 32
  special = true
}

resource "aws_security_group" "rds" {
  name_prefix = "${local.cluster_name}-rds-"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [module.eks.cluster_security_group_id]
  }

  tags = {
    Name = "${local.cluster_name}-rds-sg"
  }
}

resource "aws_kms_key" "rds" {
  description             = "RDS encryption key for ${local.cluster_name}"
  deletion_window_in_days = 7
  enable_key_rotation     = true

  tags = {
    Name = "${local.cluster_name}-rds-key"
  }
}

# ClickHouse on EC2 (regional analytics)
resource "aws_instance" "clickhouse" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = "r6i.2xlarge"
  subnet_id     = module.vpc.private_subnets[0]

  vpc_security_group_ids = [aws_security_group.clickhouse.id]

  root_block_device {
    volume_type = "gp3"
    volume_size = 500
    encrypted   = true
  }

  user_data = file("${path.module}/clickhouse-init.sh")

  tags = {
    Name = "${local.cluster_name}-clickhouse"
  }
}

data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }
}

resource "aws_security_group" "clickhouse" {
  name_prefix = "${local.cluster_name}-clickhouse-"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port       = 8123
    to_port         = 8123
    protocol        = "tcp"
    security_groups = [module.eks.cluster_security_group_id]
  }

  ingress {
    from_port       = 9000
    to_port         = 9000
    protocol        = "tcp"
    security_groups = [module.eks.cluster_security_group_id]
  }

  tags = {
    Name = "${local.cluster_name}-clickhouse-sg"
  }
}

# Application Load Balancer
resource "aws_lb" "main" {
  name               = "${local.cluster_name}-lb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = module.vpc.public_subnets

  enable_deletion_protection = true
  enable_http2              = true

  tags = {
    Name = "${local.cluster_name}-alb"
  }
}

resource "aws_security_group" "alb" {
  name_prefix = "${local.cluster_name}-alb-"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${local.cluster_name}-alb-sg"
  }
}

# Outputs
output "cluster_endpoint" {
  description = "EKS cluster endpoint"
  value       = module.eks.cluster_endpoint
}

output "cluster_name" {
  description = "EKS cluster name"
  value       = local.cluster_name
}

output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "vpc_cidr" {
  description = "VPC CIDR"
  value       = local.vpc_cidr
}

output "db_endpoint" {
  description = "RDS endpoint"
  value       = aws_db_instance.postgres.endpoint
  sensitive   = true
}

output "clickhouse_endpoint" {
  description = "ClickHouse endpoint"
  value       = aws_instance.clickhouse.private_ip
}

output "alb_dns_name" {
  description = "ALB DNS name"
  value       = aws_lb.main.dns_name
}
