#!/bin/bash
set -e

# Push the Docker image for test-session-agent to a registry
#
# Usage:
#   ./scripts/push.sh [registry] [tag]
#
# Arguments:
#   registry: Docker registry to push to (default: ECR_REGISTRY from environment)
#   tag: Tag for the image (default: latest)

# Get the registry from command line or environment
REGISTRY=${1:-${ECR_REGISTRY}}
if [[ -z "${REGISTRY}" ]]; then
  echo "Error: No registry specified. Either provide as argument or set ECR_REGISTRY environment variable."
  echo "Usage: ./scripts/push.sh [registry] [tag]"
  exit 1
fi

# Get the tag from command line or use default
TAG=${2:-latest}

# Set the image repository name
REPO="test-session-agent"
LOCAL_IMAGE="${REPO}:${TAG}"
REMOTE_IMAGE="${REGISTRY}/${REPO}:${TAG}"

# Check if the local image exists
if ! docker image inspect ${LOCAL_IMAGE} &> /dev/null; then
  echo "Local image ${LOCAL_IMAGE} not found. Building it first..."
  ./scripts/build.sh ${TAG}
fi

# Tag and push the image
echo "Tagging ${LOCAL_IMAGE} as ${REMOTE_IMAGE}..."
docker tag ${LOCAL_IMAGE} ${REMOTE_IMAGE}

echo "Pushing ${REMOTE_IMAGE} to registry..."
docker push ${REMOTE_IMAGE}

echo "Done! Image pushed: ${REMOTE_IMAGE}"
echo ""
echo "To use this image in your Kubernetes manifests:"
echo "  IMAGE_REPOSITORY=${REGISTRY}/${REPO} IMAGE_TAG=${TAG} kubectl apply -f deployment/k8s/"
echo ""
echo "Or in your Helm values:"
echo "  helm upgrade --install test-session-agent deployment/helm --set image.repository=${REGISTRY}/${REPO} --set image.tag=${TAG}"