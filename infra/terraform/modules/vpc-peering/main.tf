# VPC Peering Module for Multi-Region Connectivity
# Creates VPC peering connections between regions

variable "requester_vpc_id" {
  description = "VPC ID of the requester"
  type        = string
}

variable "requester_region" {
  description = "AWS region of the requester VPC"
  type        = string
}

variable "requester_cidr" {
  description = "CIDR block of the requester VPC"
  type        = string
}

variable "accepter_vpc_id" {
  description = "VPC ID of the accepter"
  type        = string
}

variable "accepter_region" {
  description = "AWS region of the accepter VPC"
  type        = string
}

variable "accepter_cidr" {
  description = "CIDR block of the accepter VPC"
  type        = string
}

variable "peering_name" {
  description = "Name tag for the peering connection"
  type        = string
}

# VPC Peering Connection
resource "aws_vpc_peering_connection" "main" {
  vpc_id        = var.requester_vpc_id
  peer_vpc_id   = var.accepter_vpc_id
  peer_region   = var.accepter_region
  auto_accept   = false

  tags = {
    Name = var.peering_name
    Side = "Requester"
  }
}

# Accept the peering connection (in accepter region)
resource "aws_vpc_peering_connection_accepter" "main" {
  provider                  = aws.accepter
  vpc_peering_connection_id = aws_vpc_peering_connection.main.id
  auto_accept               = true

  tags = {
    Name = var.peering_name
    Side = "Accepter"
  }
}

# Route table entries for requester VPC
resource "aws_route" "requester_to_accepter" {
  count = length(data.aws_route_tables.requester.ids)

  route_table_id            = data.aws_route_tables.requester.ids[count.index]
  destination_cidr_block    = var.accepter_cidr
  vpc_peering_connection_id = aws_vpc_peering_connection.main.id
}

# Route table entries for accepter VPC
resource "aws_route" "accepter_to_requester" {
  provider = aws.accepter
  count    = length(data.aws_route_tables.accepter.ids)

  route_table_id            = data.aws_route_tables.accepter.ids[count.index]
  destination_cidr_block    = var.requester_cidr
  vpc_peering_connection_id = aws_vpc_peering_connection.main.id
}

# Data sources for route tables
data "aws_route_tables" "requester" {
  vpc_id = var.requester_vpc_id
}

data "aws_route_tables" "accepter" {
  provider = aws.accepter
  vpc_id   = var.accepter_vpc_id
}

# Security group rules to allow traffic between VPCs
resource "aws_security_group_rule" "requester_ingress" {
  type              = "ingress"
  from_port         = 0
  to_port           = 65535
  protocol          = "-1"
  cidr_blocks       = [var.accepter_cidr]
  security_group_id = data.aws_security_group.requester_default.id
}

resource "aws_security_group_rule" "accepter_ingress" {
  provider          = aws.accepter
  type              = "ingress"
  from_port         = 0
  to_port           = 65535
  protocol          = "-1"
  cidr_blocks       = [var.requester_cidr]
  security_group_id = data.aws_security_group.accepter_default.id
}

data "aws_security_group" "requester_default" {
  vpc_id = var.requester_vpc_id
  name   = "default"
}

data "aws_security_group" "accepter_default" {
  provider = aws.accepter
  vpc_id   = var.accepter_vpc_id
  name     = "default"
}

# Outputs
output "peering_connection_id" {
  description = "ID of the VPC peering connection"
  value       = aws_vpc_peering_connection.main.id
}

output "peering_status" {
  description = "Status of the VPC peering connection"
  value       = aws_vpc_peering_connection.main.accept_status
}
