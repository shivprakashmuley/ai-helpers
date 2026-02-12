#!/bin/bash
# Example: Upstream analysis for cert-manager component
#
# This demonstrates analyzing both downstream (OpenShift) and upstream repositories
# to gain comprehensive understanding for RFE analysis.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "======================================================================="
echo "Example: Upstream Analysis for cert-manager"
echo "======================================================================="
echo ""
echo "This example analyzes cert-manager with upstream analysis enabled."
echo "It will analyze:"
echo "  - Downstream: openshift/cert-manager-operator"
echo "  - Upstream: cert-manager/cert-manager"
echo ""
echo "Use case: Understanding how OpenShift cert-manager differs from upstream"
echo "          and identifying upstream features to potentially adopt."
echo ""
echo "Press Enter to continue..."
read

echo ""
echo "Running analysis with upstream enabled..."
echo ""

python3 gather_component_context.py cert-manager \
  --keywords "certificate" "rotation" "ACME" \
  --analyze-upstream \
  --max-prs 5 \
  --deep-dive 2 \
  -v

echo ""
echo "======================================================================="
echo "Analysis Complete!"
echo "======================================================================="
echo ""
echo "The output above includes:"
echo "  ✓ Downstream repository analysis"
echo "  ✓ Upstream repository analysis"
echo "  ✓ Architecture comparison"
echo "  ✓ Upstream implementation patterns"
echo "  ✓ Adoption recommendations"
echo ""
echo "To save output to file, run:"
echo "  ./gather_component_context.py cert-manager \\"
echo "    --keywords 'certificate' 'rotation' \\"
echo "    --analyze-upstream \\"
echo "    -o cert-manager-analysis.md"
echo ""
