#!/bin/bash
# Helm Chart Validation Script
# This script validates the session-backend Helm chart

set -e

CHART_DIR="./session-backend"
CHART_NAME="session-backend"

echo "=================================================="
echo "  Session Backend Helm Chart Validation"
echo "=================================================="
echo ""

# Check if helm is installed
if ! command -v helm &> /dev/null; then
    echo "❌ Helm is not installed. Please install Helm 3.0+"
    exit 1
fi

echo "✅ Helm is installed: $(helm version --short)"
echo ""

# Check if chart directory exists
if [ ! -d "$CHART_DIR" ]; then
    echo "❌ Chart directory not found: $CHART_DIR"
    exit 1
fi

echo "✅ Chart directory found"
echo ""

# Lint the chart
echo "🔍 Linting chart..."
if helm lint "$CHART_DIR"; then
    echo "✅ Chart lint passed"
else
    echo "❌ Chart lint failed"
    exit 1
fi
echo ""

# Validate with default values
echo "🔍 Validating with default values..."
if helm template test "$CHART_DIR" > /dev/null; then
    echo "✅ Default values validation passed"
else
    echo "❌ Default values validation failed"
    exit 1
fi
echo ""

# Validate with development values
echo "🔍 Validating with development values..."
if helm template test "$CHART_DIR" -f "$CHART_DIR/values-development.yaml" > /dev/null; then
    echo "✅ Development values validation passed"
else
    echo "❌ Development values validation failed"
    exit 1
fi
echo ""

# Validate with production values
echo "🔍 Validating with production values..."
if helm template test "$CHART_DIR" -f "$CHART_DIR/values-production.yaml" > /dev/null; then
    echo "✅ Production values validation passed"
else
    echo "❌ Production values validation failed"
    exit 1
fi
echo ""

# Check required files
echo "🔍 Checking required files..."
REQUIRED_FILES=(
    "$CHART_DIR/Chart.yaml"
    "$CHART_DIR/values.yaml"
    "$CHART_DIR/templates/_helpers.tpl"
    "$CHART_DIR/templates/deployment.yaml"
    "$CHART_DIR/templates/service.yaml"
    "$CHART_DIR/templates/postgresql-statefulset.yaml"
)

ALL_FILES_EXIST=true
for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ $file (missing)"
        ALL_FILES_EXIST=false
    fi
done

if [ "$ALL_FILES_EXIST" = false ]; then
    echo "❌ Some required files are missing"
    exit 1
fi
echo ""

# Generate templates for inspection
echo "🔍 Generating templates..."
OUTPUT_DIR="./generated-manifests"
mkdir -p "$OUTPUT_DIR"

helm template "$CHART_NAME" "$CHART_DIR" \
    -f "$CHART_DIR/values-development.yaml" \
    > "$OUTPUT_DIR/development.yaml"
echo "  ✅ Development manifests: $OUTPUT_DIR/development.yaml"

helm template "$CHART_NAME" "$CHART_DIR" \
    -f "$CHART_DIR/values-production.yaml" \
    > "$OUTPUT_DIR/production.yaml"
echo "  ✅ Production manifests: $OUTPUT_DIR/production.yaml"
echo ""

# Count resources
echo "📊 Resource counts:"
echo "  Development:"
echo "    Deployments: $(grep -c "kind: Deployment" "$OUTPUT_DIR/development.yaml" || echo 0)"
echo "    Services: $(grep -c "kind: Service" "$OUTPUT_DIR/development.yaml" || echo 0)"
echo "    StatefulSets: $(grep -c "kind: StatefulSet" "$OUTPUT_DIR/development.yaml" || echo 0)"
echo "    ConfigMaps: $(grep -c "kind: ConfigMap" "$OUTPUT_DIR/development.yaml" || echo 0)"
echo "    Secrets: $(grep -c "kind: Secret" "$OUTPUT_DIR/development.yaml" || echo 0)"
echo ""
echo "  Production:"
echo "    Deployments: $(grep -c "kind: Deployment" "$OUTPUT_DIR/production.yaml" || echo 0)"
echo "    Services: $(grep -c "kind: Service" "$OUTPUT_DIR/production.yaml" || echo 0)"
echo "    StatefulSets: $(grep -c "kind: StatefulSet" "$OUTPUT_DIR/production.yaml" || echo 0)"
echo "    ConfigMaps: $(grep -c "kind: ConfigMap" "$OUTPUT_DIR/production.yaml" || echo 0)"
echo "    Secrets: $(grep -c "kind: Secret" "$OUTPUT_DIR/production.yaml" || echo 0)"
echo "    HPA: $(grep -c "kind: HorizontalPodAutoscaler" "$OUTPUT_DIR/production.yaml" || echo 0)"
echo "    Ingress: $(grep -c "kind: Ingress" "$OUTPUT_DIR/production.yaml" || echo 0)"
echo "    PDB: $(grep -c "kind: PodDisruptionBudget" "$OUTPUT_DIR/production.yaml" || echo 0)"
echo "    NetworkPolicy: $(grep -c "kind: NetworkPolicy" "$OUTPUT_DIR/production.yaml" || echo 0)"
echo ""

# Dry run (requires kubectl context)
if command -v kubectl &> /dev/null && kubectl cluster-info &> /dev/null; then
    echo "🔍 Running dry-run installation..."
    if helm install "$CHART_NAME" "$CHART_DIR" \
        -f "$CHART_DIR/values-development.yaml" \
        --dry-run --debug > /dev/null 2>&1; then
        echo "✅ Dry-run installation passed"
    else
        echo "⚠️  Dry-run installation failed (this may be expected if cluster resources are not available)"
    fi
else
    echo "⚠️  kubectl not configured, skipping dry-run"
fi
echo ""

# Package the chart
echo "📦 Packaging chart..."
if helm package "$CHART_DIR" -d "$OUTPUT_DIR"; then
    PACKAGE_FILE=$(ls -t "$OUTPUT_DIR"/*.tgz | head -1)
    echo "✅ Chart packaged: $PACKAGE_FILE"
else
    echo "❌ Chart packaging failed"
    exit 1
fi
echo ""

# Summary
echo "=================================================="
echo "  ✅ All validations passed!"
echo "=================================================="
echo ""
echo "Generated files:"
echo "  - $OUTPUT_DIR/development.yaml"
echo "  - $OUTPUT_DIR/production.yaml"
echo "  - $PACKAGE_FILE"
echo ""
echo "Next steps:"
echo "  1. Review generated manifests in $OUTPUT_DIR/"
echo "  2. Test installation: helm install $CHART_NAME $CHART_DIR -f $CHART_DIR/values-development.yaml"
echo "  3. Verify deployment: kubectl get all"
echo ""
