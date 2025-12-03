"""
⚠️ WE DO NOT MOCK - Real AWS adapter using boto3.

Provides comprehensive AWS integration:
    - EC2 (instances, security groups, key pairs)
    - S3 (buckets, objects, lifecycle)
    - Lambda (functions, layers, triggers)
    - CloudFormation (stacks, templates)
    - IAM (roles, policies, users)
    - RDS (databases, snapshots)
    - DynamoDB (tables, items)
"""

import json
import logging
from typing import Any

import boto3

from services.common.config.base_settings import resolve_env

logger = logging.getLogger(__name__)


class AWSAdapter:
    """
    Real AWS adapter using boto3.

    Requires:
        - AWS_ACCESS_KEY_ID
        - AWS_SECRET_ACCESS_KEY
        - AWS_REGION
    """

    def __init__(self, region_name: str | None = None):
        self.region_name = region_name or resolve_env("AWS_REGION", "us-east-1")
        self.access_key = resolve_env("AWS_ACCESS_KEY_ID")
        self.secret_key = resolve_env("AWS_SECRET_ACCESS_KEY")

        if not self.access_key or not self.secret_key:
            logger.warning("AWS credentials not found. Some operations may fail.")

        self.session = boto3.Session(
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name=self.region_name,
        )

    def _get_client(self, service_name: str) -> Any:
        """Get boto3 client for service."""
        return self.session.client(service_name)

    # ----------------------------------------------------------------------
    # EC2 Operations
    # ----------------------------------------------------------------------

    def run_instances(
        self,
        image_id: str,
        instance_type: str,
        min_count: int = 1,
        max_count: int = 1,
        key_name: str | None = None,
        security_group_ids: list[str] | None = None,
        subnet_id: str | None = None,
        tags: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Launch EC2 instances."""
        ec2 = self._get_client("ec2")

        params = {
            "ImageId": image_id,
            "InstanceType": instance_type,
            "MinCount": min_count,
            "MaxCount": max_count,
        }

        if key_name:
            params["KeyName"] = key_name
        if security_group_ids:
            params["SecurityGroupIds"] = security_group_ids
        if subnet_id:
            params["SubnetId"] = subnet_id

        if tags:
            params["TagSpecifications"] = [
                {
                    "ResourceType": "instance",
                    "Tags": [{"Key": k, "Value": v} for k, v in tags.items()],
                }
            ]

        response = ec2.run_instances(**params)
        return response

    def terminate_instances(self, instance_ids: list[str]) -> dict[str, Any]:
        """Terminate EC2 instances."""
        ec2 = self._get_client("ec2")
        return ec2.terminate_instances(InstanceIds=instance_ids)

    def describe_instances(
        self, instance_ids: list[str] | None = None, filters: list[dict] | None = None
    ) -> dict[str, Any]:
        """Describe EC2 instances."""
        ec2 = self._get_client("ec2")
        params = {}
        if instance_ids:
            params["InstanceIds"] = instance_ids
        if filters:
            params["Filters"] = filters
        return ec2.describe_instances(**params)

    # ----------------------------------------------------------------------
    # S3 Operations
    # ----------------------------------------------------------------------

    def create_bucket(self, bucket_name: str) -> dict[str, Any]:
        """Create S3 bucket."""
        s3 = self._get_client("s3")
        if self.region_name == "us-east-1":
            return s3.create_bucket(Bucket=bucket_name)
        return s3.create_bucket(
            Bucket=bucket_name,
            CreateBucketConfiguration={"LocationConstraint": self.region_name},
        )

    def put_object(
        self, bucket_name: str, key: str, body: str | bytes, content_type: str | None = None
    ) -> dict[str, Any]:
        """Upload object to S3."""
        s3 = self._get_client("s3")
        params = {"Bucket": bucket_name, "Key": key, "Body": body}
        if content_type:
            params["ContentType"] = content_type
        return s3.put_object(**params)

    def get_object(self, bucket_name: str, key: str) -> dict[str, Any]:
        """Download object from S3."""
        s3 = self._get_client("s3")
        response = s3.get_object(Bucket=bucket_name, Key=key)
        # Read body stream
        if "Body" in response:
            response["Body"] = response["Body"].read()
        return response

    def list_objects(self, bucket_name: str, prefix: str = "", max_keys: int = 1000) -> dict[str, Any]:
        """List objects in S3 bucket."""
        s3 = self._get_client("s3")
        return s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix, MaxKeys=max_keys)

    # ----------------------------------------------------------------------
    # Lambda Operations
    # ----------------------------------------------------------------------

    def create_function(
        self,
        function_name: str,
        runtime: str,
        role: str,
        handler: str,
        code_zip: bytes,
        description: str = "",
        timeout: int = 3,
        memory_size: int = 128,
        environment: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Create Lambda function."""
        lambda_client = self._get_client("lambda")

        params = {
            "FunctionName": function_name,
            "Runtime": runtime,
            "Role": role,
            "Handler": handler,
            "Code": {"ZipFile": code_zip},
            "Description": description,
            "Timeout": timeout,
            "MemorySize": memory_size,
            "Publish": True,
        }

        if environment:
            params["Environment"] = {"Variables": environment}

        return lambda_client.create_function(**params)

    def invoke_function(
        self,
        function_name: str,
        payload: dict[str, Any] | None = None,
        invocation_type: str = "RequestResponse",
    ) -> dict[str, Any]:
        """Invoke Lambda function."""
        lambda_client = self._get_client("lambda")

        params = {
            "FunctionName": function_name,
            "InvocationType": invocation_type,
        }

        if payload:
            params["Payload"] = json.dumps(payload)

        response = lambda_client.invoke(**params)

        if "Payload" in response:
            response["Payload"] = response["Payload"].read().decode("utf-8")

        return response

    # ----------------------------------------------------------------------
    # CloudFormation Operations
    # ----------------------------------------------------------------------

    def create_stack(
        self,
        stack_name: str,
        template_body: str,
        parameters: list[dict] | None = None,
        capabilities: list[str] | None = None,
    ) -> dict[str, Any]:
        """Create CloudFormation stack."""
        cf = self._get_client("cloudformation")

        params = {
            "StackName": stack_name,
            "TemplateBody": template_body,
        }

        if parameters:
            params["Parameters"] = parameters
        if capabilities:
            params["Capabilities"] = capabilities

        return cf.create_stack(**params)

    def describe_stacks(self, stack_name: str | None = None) -> dict[str, Any]:
        """Describe CloudFormation stacks."""
        cf = self._get_client("cloudformation")
        params = {}
        if stack_name:
            params["StackName"] = stack_name
        return cf.describe_stacks(**params)

    # ----------------------------------------------------------------------
    # IAM Operations
    # ----------------------------------------------------------------------

    def create_role(self, role_name: str, assume_role_policy_document: str, description: str = "") -> dict[str, Any]:
        """Create IAM role."""
        iam = self._get_client("iam")
        return iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=assume_role_policy_document,
            Description=description,
        )

    def attach_role_policy(self, role_name: str, policy_arn: str) -> dict[str, Any]:
        """Attach managed policy to role."""
        iam = self._get_client("iam")
        return iam.attach_role_policy(RoleName=role_name, PolicyArn=policy_arn)

    # ----------------------------------------------------------------------
    # RDS Operations
    # ----------------------------------------------------------------------

    def create_db_instance(
        self,
        db_instance_identifier: str,
        db_instance_class: str,
        engine: str,
        master_username: str,
        master_user_password: str,
        allocated_storage: int = 20,
        tags: list[dict] | None = None,
    ) -> dict[str, Any]:
        """Create RDS instance."""
        rds = self._get_client("rds")

        params = {
            "DBInstanceIdentifier": db_instance_identifier,
            "DBInstanceClass": db_instance_class,
            "Engine": engine,
            "MasterUsername": master_username,
            "MasterUserPassword": master_user_password,
            "AllocatedStorage": allocated_storage,
        }

        if tags:
            params["Tags"] = tags

        return rds.create_db_instance(**params)

    # ----------------------------------------------------------------------
    # DynamoDB Operations
    # ----------------------------------------------------------------------

    def create_table(
        self,
        table_name: str,
        key_schema: list[dict],
        attribute_definitions: list[dict],
        billing_mode: str = "PAY_PER_REQUEST",
    ) -> dict[str, Any]:
        """Create DynamoDB table."""
        dynamodb = self._get_client("dynamodb")
        return dynamodb.create_table(
            TableName=table_name,
            KeySchema=key_schema,
            AttributeDefinitions=attribute_definitions,
            BillingMode=billing_mode,
        )

    def put_item(self, table_name: str, item: dict[str, Any]) -> dict[str, Any]:
        """Put item into DynamoDB table."""
        dynamodb = self._get_client("dynamodb")
        # Note: item must be in DynamoDB JSON format or use Table resource
        return dynamodb.put_item(TableName=table_name, Item=item)

    def get_item(self, table_name: str, key: dict[str, Any]) -> dict[str, Any]:
        """Get item from DynamoDB table."""
        dynamodb = self._get_client("dynamodb")
        return dynamodb.get_item(TableName=table_name, Key=key)
