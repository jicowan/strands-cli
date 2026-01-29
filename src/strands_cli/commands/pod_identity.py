"""Implementation of the create-pod-identity command."""

import json
import subprocess
from typing import Optional, Tuple

import boto3
from rich.console import Console

console = Console()


def create_pod_identity_association(
    service_account_name: str,
    policy_arn: str,
    cluster_name: Optional[str] = None,
    namespace: str = "default",
    role_name: Optional[str] = None,
) -> Tuple[bool, str]:
    """Create an IAM role with pod identity trust policy and attach the specified policy.

    Args:
        service_account_name: The name of the service account.
        policy_arn: The ARN of the policy to attach to the role.
        cluster_name: The name of the EKS cluster. If not provided, the current context will be used.
        namespace: The Kubernetes namespace where the service account exists.
        role_name: Optional name for the IAM role. If not provided, a name will be generated.

    Returns:
        Tuple[bool, str]: Success status and message or error.
    """
    # Check if AWS credentials are configured
    try:
        session = boto3.Session()
        sts_client = session.client('sts')
        account_id = sts_client.get_caller_identity()["Account"]
    except Exception as e:
        return False, f"AWS credentials are not configured correctly: {str(e)}"

    # Generate role name if not provided
    if not role_name:
        role_name = f"eks-pod-identity-{service_account_name}"

    # Get current EKS cluster name if not provided
    if not cluster_name:
        try:
            result = subprocess.run(
                ["kubectl", "config", "current-context"],
                capture_output=True,
                check=True,
                text=True
            )
            context = result.stdout.strip()
            if "eks.amazonaws.com" in context:
                # Extract cluster name from EKS context format
                cluster_name = context.split("/")[1]
            else:
                return False, "Current kubectl context is not an EKS cluster. Please specify --cluster-name."
        except (subprocess.SubprocessError, IndexError):
            return False, "Failed to get current kubectl context. Please specify --cluster-name."

    # Create the trust policy document
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "AllowEksAuthToAssumeRoleForPodIdentity",
                "Effect": "Allow",
                "Principal": {
                    "Service": "pods.eks.amazonaws.com"
                },
                "Action": [
                    "sts:AssumeRole",
                    "sts:TagSession"
                ]
            }
        ]
    }

    try:
        # Create the IAM role
        iam_client = session.client('iam')
        console.print(f"Creating IAM role: {role_name}")
        response = iam_client.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description=f"Role for EKS Pod Identity used by {service_account_name} service account in {namespace} namespace"
        )
        role_arn = response['Role']['Arn']

        # Attach the policy to the role
        console.print(f"Attaching policy {policy_arn} to role {role_name}")
        iam_client.attach_role_policy(
            RoleName=role_name,
            PolicyArn=policy_arn
        )

        # Create the EKS pod identity association
        eks_client = session.client('eks')
        console.print(f"Creating pod identity association for {service_account_name} in {namespace} namespace")
        eks_client.create_pod_identity_association(
            clusterName=cluster_name,
            namespace=namespace,
            serviceAccount=service_account_name,
            roleArn=role_arn
        )

        return True, f"Successfully created pod identity association for {service_account_name} in {namespace} namespace with role {role_arn}"

    except Exception as e:
        return False, f"Failed to create pod identity association: {str(e)}"