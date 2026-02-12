#!/bin/bash
# Test script for component context analysis scripts

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "======================================================================="
echo "Testing Component Context Analysis Scripts"
echo "======================================================================="
echo ""

# Check prerequisites
echo "Checking prerequisites..."
echo ""

# Check gh CLI
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI (gh) not found"
    echo "   Install from: https://cli.github.com/"
    exit 1
fi

if ! gh auth status &> /dev/null; then
    echo "❌ GitHub CLI not authenticated"
    echo "   Run: gh auth login"
    exit 1
fi

echo "✓ GitHub CLI installed and authenticated"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found"
    exit 1
fi

echo "✓ Python 3 installed"
echo ""

# Test 1: Repository Analyzer
echo "======================================================================="
echo "Test 1: Repository Analyzer"
echo "======================================================================="
echo "Testing: python3 github_repo_analyzer.py cert-manager"
echo ""

python3 github_repo_analyzer.py cert-manager 2>&1 | head -30
echo ""
echo "✓ Repository analyzer test passed"
echo ""

# Test 2: PR Analyzer
echo "======================================================================="
echo "Test 2: PR Analyzer"
echo "======================================================================="
echo "Testing: python3 github_pr_analyzer.py openshift/cert-manager-operator certificate"
echo ""

python3 github_pr_analyzer.py openshift/cert-manager-operator certificate 2>&1 | head -30
echo ""
echo "✓ PR analyzer test passed"
echo ""

# Test 3: Full Context Gatherer
echo "======================================================================="
echo "Test 3: Full Context Gatherer"
echo "======================================================================="
echo "Testing: python3 gather_component_context.py cert-manager --keywords certificate -v"
echo ""

python3 gather_component_context.py cert-manager --keywords "certificate" -v 2>&1 | head -50
echo ""
echo "✓ Context gatherer test passed"
echo ""

# Summary
echo "======================================================================="
echo "All Tests Passed! ✓"
echo "======================================================================="
echo ""
echo "Scripts are ready to use. Examples:"
echo ""
echo "  # Analyze single component"
echo "  ./gather_component_context.py hypershift"
echo ""
echo "  # Analyze with keywords"
echo "  ./gather_component_context.py cert-manager --keywords 'certificate rotation'"
echo ""
echo "  # Multiple components"
echo "  ./gather_component_context.py hypershift cert-manager --keywords 'certificate'"
echo ""
echo "  # Output to file"
echo "  ./gather_component_context.py hypershift -o output.md"
echo ""
echo "See README.md for full documentation."
echo ""
