"""Tests for the pod identity command."""

import json
import subprocess
from unittest.mock import patch, MagicMock

import pytest
import boto3

from strands_cli.commands.pod_identity import create_pod_identity_association


class TestPodIdentityCommands:
    """Tests for pod identity command."""

    @patch("boto3.Session")
    @patch("subprocess.run")
    def test_create_pod_identity_association_success(self, mock_subprocess_run, mock_boto3_session):
        """Test creating a pod identity association (success case)."""
        # Mock subprocess call for kubectl context
        mock_process = MagicMock()
        mock_process.stdout = "test-context:eks.amazonaws.com/test-cluster"
        mock_subprocess_run.return_value = mock_process

        # Mock AWS clients and their return values
        mock_iam = MagicMock()
        mock_iam.create_role.return_value = {
            'Role': {'Arn': 'arn:aws:iam::123456789012:role/test-role'}
        }

        mock_eks = MagicMock()

        mock_sts = MagicMock()
        mock_sts.get_caller_identity.return_value = {"Account": "123456789012"}

        # Create a session that returns our mocked clients
        mock_session = MagicMock()

        # Configure side_effect to return different clients based on the service name
        def get_client(service_name):
            if service_name == 'sts':
                return mock_sts
            elif service_name == 'iam':
                return mock_iam
            elif service_name == 'eks':
                return mock_eks
            return MagicMock()

        mock_session.client.side_effect = get_client
        mock_boto3_session.return_value = mock_session

        # Test inputs
        service_account_name = "test-sa"
        policy_arn = "arn:aws:iam::aws:policy/AmazonBedrockFullAccess"

        # Call the function
        success, message = create_pod_identity_association(
            service_account_name=service_account_name,
            policy_arn=policy_arn
        )

        # Verify result
        assert success is True
        assert "Successfully created pod identity association" in message

        # Verify IAM role was created with correct trust policy
        mock_iam.create_role.assert_called_once()
        args, kwargs = mock_iam.create_role.call_args
        assert kwargs['RoleName'] == f"eks-pod-identity-{service_account_name}"

        trust_policy = json.loads(kwargs['AssumeRolePolicyDocument'])
        assert trust_policy["Statement"][0]["Principal"]["Service"] == "pods.eks.amazonaws.com"
        assert "sts:AssumeRole" in trust_policy["Statement"][0]["Action"]
        assert "sts:TagSession" in trust_policy["Statement"][0]["Action"]

        # Verify policy was attached
        mock_iam.attach_role_policy.assert_called_once_with(
            RoleName=f"eks-pod-identity-{service_account_name}",
            PolicyArn=policy_arn
        )

        # Verify EKS pod identity association was created
        mock_eks = mock_session.client('eks')
        mock_eks.create_pod_identity_association.assert_called_once()

    @patch("boto3.Session")
    def test_create_pod_identity_association_no_aws_credentials(self, mock_boto3_session):
        """Test creating a pod identity association with no AWS credentials."""
        # Mock boto3.Session to raise an exception
        mock_boto3_session.side_effect = Exception("No AWS credentials found")

        # Test inputs
        service_account_name = "test-sa"
        policy_arn = "arn:aws:iam::aws:policy/AmazonBedrockFullAccess"

        # Call the function
        success, message = create_pod_identity_association(
            service_account_name=service_account_name,
            policy_arn=policy_arn
        )

        # Verify result
        assert success is False
        assert "AWS credentials are not configured correctly" in message

    @patch("boto3.Session")
    @patch("subprocess.run")
    def test_create_pod_identity_association_custom_parameters(self, mock_subprocess_run, mock_boto3_session):
        """Test creating a pod identity association with custom parameters."""
        # Mock AWS clients and their return values
        mock_iam = MagicMock()
        mock_iam.create_role.return_value = {
            'Role': {'Arn': 'arn:aws:iam::123456789012:role/my-custom-role'}
        }

        mock_eks = MagicMock()

        mock_sts = MagicMock()
        mock_sts.get_caller_identity.return_value = {"Account": "123456789012"}

        # Create a session that returns our mocked clients
        mock_session = MagicMock()

        # Configure side_effect to return different clients based on the service name
        def get_client(service_name):
            if service_name == 'sts':
                return mock_sts
            elif service_name == 'iam':
                return mock_iam
            elif service_name == 'eks':
                return mock_eks
            return MagicMock()

        mock_session.client.side_effect = get_client
        mock_boto3_session.return_value = mock_session

        # Test inputs with custom parameters
        service_account_name = "test-sa"
        policy_arn = "arn:aws:iam::aws:policy/AmazonBedrockFullAccess"
        cluster_name = "my-custom-cluster"
        namespace = "custom-namespace"
        role_name = "my-custom-role"

        # Call the function with custom parameters
        success, message = create_pod_identity_association(
            service_account_name=service_account_name,
            policy_arn=policy_arn,
            cluster_name=cluster_name,
            namespace=namespace,
            role_name=role_name
        )

        # Verify result
        assert success is True

        # Verify IAM role was created with custom name
        mock_iam = mock_session.client('iam')
        mock_iam.create_role.assert_called_once()
        args, kwargs = mock_iam.create_role.call_args
        assert kwargs['RoleName'] == role_name

        # Verify EKS pod identity association was created with custom parameters
        mock_eks = mock_session.client('eks')
        mock_eks.create_pod_identity_association.assert_called_once_with(
            clusterName=cluster_name,
            namespace=namespace,
            serviceAccount=service_account_name,
            roleArn=mock_iam.create_role.return_value['Role']['Arn']
        )

    @patch("boto3.Session")
    @patch("subprocess.run")
    def test_create_pod_identity_association_subprocess_error(self, mock_subprocess_run, mock_boto3_session):
        """Test creating a pod identity association with subprocess error."""
        # Mock subprocess call to raise an exception
        mock_subprocess_run.side_effect = subprocess.SubprocessError("Command failed")

        # Mock boto3 session
        mock_session = MagicMock()
        mock_boto3_session.return_value = mock_session

        mock_sts = MagicMock()
        mock_sts.get_caller_identity.return_value = {"Account": "123456789012"}
        mock_session.client.return_value = mock_sts

        # Test inputs
        service_account_name = "test-sa"
        policy_arn = "arn:aws:iam::aws:policy/AmazonBedrockFullAccess"

        # Call the function without specifying cluster name
        success, message = create_pod_identity_association(
            service_account_name=service_account_name,
            policy_arn=policy_arn
        )

        # Verify result
        assert success is False
        assert "Failed to get current kubectl context" in message