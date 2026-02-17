#!/usr/bin/env python3
"""
Test script to verify Phase 1 fixes
Tests PR search, operand discovery, and error handling
"""

import sys
from pathlib import Path

# Add scripts directory to path
scripts_dir = Path(__file__).parent
sys.path.insert(0, str(scripts_dir))

from github_pr_analyzer import GitHubPRAnalyzer
from operand_discovery import OperandDiscovery


def test_pr_search_fix():
    """Test that PR search now works without quotes"""
    print("=" * 70)
    print("TEST 1: PR Search Fix")
    print("=" * 70)
    print("\nTesting cert-manager-operator with keywords: certificate, rotation, ACME")
    print("Expected: Find >0 PRs (previously found 0 due to quoted keywords)\n")

    analyzer = GitHubPRAnalyzer()
    prs = analyzer.search_relevant_prs(
        'openshift/cert-manager-operator',
        ['certificate', 'rotation', 'ACME'],
        max_results=5
    )

    print(f"Result: Found {len(prs)} PRs")
    if prs:
        print("\nTop 3 PRs:")
        for i, pr in enumerate(prs[:3], 1):
            print(f"  {i}. PR #{pr['number']}: {pr['title']}")
            print(f"     Score: {pr.get('relevance_score', 0)}")

    status = "✓ PASS" if len(prs) > 0 else "✗ FAIL"
    print(f"\n{status}: PR search {'working correctly' if len(prs) > 0 else 'still broken'}")
    return len(prs) > 0


def test_operand_discovery_fix():
    """Test that operand discovery has fewer false positives"""
    print("\n" + "=" * 70)
    print("TEST 2: Operand Discovery Fix")
    print("=" * 70)
    print("\nTesting external-secrets-operator")
    print("Expected: Find 1-3 operands (not 13 false positives like 'Manager', 'this')\n")

    discovery = OperandDiscovery()
    operands = discovery.discover_operands('openshift/external-secrets-operator')

    print(f"Result: Found {len(operands)} operands")
    if operands:
        print("\nDiscovered operands:")
        for i, operand in enumerate(operands, 1):
            print(f"  {i}. {operand.get('name')} (Source: {operand.get('source')})")

    # Check for known false positives
    false_positives = ['manager', 'this', 'when', 'support']
    found_false_positives = [op for op in operands if op.get('name', '').lower() in false_positives]

    if found_false_positives:
        print(f"\n✗ WARNING: Found false positives: {[op.get('name') for op in found_false_positives]}")

    status = "✓ PASS" if len(operands) <= 5 and not found_false_positives else "✗ FAIL"
    print(f"\n{status}: Operand discovery {'improved' if status == '✓ PASS' else 'needs more work'}")
    return status == "✓ PASS"


def test_error_handling():
    """Test error handling with invalid inputs"""
    print("\n" + "=" * 70)
    print("TEST 3: Error Handling")
    print("=" * 70)
    print("\nTesting with nonexistent repository")
    print("Expected: No crash, graceful degradation\n")

    try:
        from gather_component_context import ComponentContextGatherer

        gatherer = ComponentContextGatherer(verbose=False)
        context = gatherer.gather_context(
            "nonexistent-component-12345",
            rfe_keywords=["test"],
            analyze_upstream=False,
            analyze_operands=False,
            interactive=False
        )

        print(f"Result: Successfully handled nonexistent component")
        print(f"  Downstream repo: {context['repositories'].get('downstream', 'None')}")
        status = "✓ PASS"
    except Exception as e:
        print(f"Result: CRASHED with error: {e}")
        status = "✗ FAIL"

    print(f"\n{status}: Error handling {'working correctly' if status == '✓ PASS' else 'needs fixing'}")
    return status == "✓ PASS"


def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("PHASE 1 FIXES VERIFICATION")
    print("=" * 70)
    print("\nRunning tests to verify critical bug fixes...\n")

    results = []

    # Test 1: PR Search
    try:
        results.append(("PR Search Fix", test_pr_search_fix()))
    except Exception as e:
        print(f"\n✗ FAIL: PR search test crashed: {e}")
        results.append(("PR Search Fix", False))

    # Test 2: Operand Discovery
    try:
        results.append(("Operand Discovery Fix", test_operand_discovery_fix()))
    except Exception as e:
        print(f"\n✗ FAIL: Operand discovery test crashed: {e}")
        results.append(("Operand Discovery Fix", False))

    # Test 3: Error Handling
    try:
        results.append(("Error Handling", test_error_handling()))
    except Exception as e:
        print(f"\n✗ FAIL: Error handling test crashed: {e}")
        results.append(("Error Handling", False))

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")

    total_passed = sum(1 for _, passed in results if passed)
    total_tests = len(results)

    print(f"\nTotal: {total_passed}/{total_tests} tests passed")

    if total_passed == total_tests:
        print("\n🎉 All Phase 1 fixes verified successfully!")
        return 0
    else:
        print("\n⚠️  Some tests failed - review output above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
