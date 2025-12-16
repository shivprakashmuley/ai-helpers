#!/usr/bin/env python3
"""
Discovery script for must-gather-clean configuration.
Analyzes must-gather artifacts locally to suggest obfuscation config.

This script NEVER sends data externally - all analysis is done locally.
"""

import os
import re
import sys
import yaml
import json
import math
from collections import defaultdict, Counter
from pathlib import Path
from typing import Dict, List, Set, Tuple


def calculate_entropy(data: str) -> float:
    """Calculate Shannon entropy of a string."""
    if not data:
        return 0.0

    entropy = 0.0
    length = len(data)

    # Count character frequencies
    frequencies = Counter(data)

    # Calculate entropy
    for count in frequencies.values():
        probability = count / length
        if probability > 0:
            entropy -= probability * math.log2(probability)

    return entropy


def is_high_entropy(value: str, threshold: float = 4.5, min_length: int = 20) -> bool:
    """Check if a string has high entropy (likely a secret/token)."""
    if len(value) < min_length:
        return False

    # Skip known non-sensitive high-entropy strings
    if value.startswith(('sha256:', 'registry-ci-', 'quay.io/openshift-release-dev')):
        return False

    entropy = calculate_entropy(value)
    return entropy > threshold


# Known secret patterns
SECRET_PATTERNS = {
    'aws_access_key': r'AKIA[0-9A-Z]{16}',
    'aws_secret_key': r'aws_secret_access_key\s*[:=]\s*[A-Za-z0-9/+=]{40}',
    'github_token': r'(ghp_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{82})',
    'slack_token': r'xox[pbar]-[0-9]{12}-[0-9]{12}-[0-9]{12}-[a-z0-9]{32}',
    'google_api_key': r'AIza[0-9A-Za-z-_]{35}',
    'private_key_header': r'-----BEGIN (RSA |DSA |EC |OPENSSH )?PRIVATE KEY-----',
    'azure_client_id': r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
    'jwt_token': r'eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+',
    'generic_api_key': r'api[_-]?key[_-]?[=:]\s*[\'"]?[A-Za-z0-9_\-]{20,}[\'"]?',
}


def scan_for_secret_patterns(must_gather_path: str) -> Dict[str, int]:
    """Scan for known secret patterns in must-gather files."""
    findings = defaultdict(int)

    # Sample files to scan (don't scan everything - too slow)
    sample_patterns = [
        '**/cluster-scoped-resources/**/*.yaml',
        '**/namespaces/**/*.yaml',
        '**/pods/**/logs/*.log',
    ]

    scanned_files = 0
    max_files = 500  # Limit scanning for performance

    for pattern in sample_patterns:
        for file_path in Path(must_gather_path).glob(pattern):
            if scanned_files >= max_files:
                break

            if file_path.is_file() and file_path.stat().st_size < 10 * 1024 * 1024:  # Skip files > 10MB
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read(1024 * 1024)  # Read max 1MB per file

                        for secret_type, pattern in SECRET_PATTERNS.items():
                            matches = re.findall(pattern, content)
                            if matches:
                                findings[secret_type] += len(matches)

                        scanned_files += 1
                except Exception:
                    pass  # Skip files we can't read

    return findings


def discover_domain_names(must_gather_path: str) -> Set[str]:
    """Discover custom domain names from Ingress/Route/Certificate resources."""
    domains = set()

    # Standard OpenShift domains to exclude
    exclude_domains = {
        'cluster.local', 'svc', 'pod', 'node',
        'openshift.io', 'k8s.io', 'kubernetes.io',
        'redhat.com', 'coreos.com',
    }

    # Look for domain names in Routes and Ingresses
    route_patterns = [
        '**/cluster-scoped-resources/config.openshift.io/ingresses/*.yaml',
        '**/namespaces/**/route.openshift.io/routes/*.yaml',
        '**/namespaces/**/networking.k8s.io/ingresses/*.yaml',
    ]

    domain_pattern = r'(?:host|domain|dnsName):\s*([a-z0-9.-]+\.[a-z]{2,})'

    for pattern in route_patterns:
        for file_path in Path(must_gather_path).glob(pattern):
            if file_path.is_file():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        matches = re.findall(domain_pattern, content, re.IGNORECASE)
                        for match in matches:
                            domain = match.lower().strip()
                            # Skip excluded domains
                            if not any(domain.endswith(excluded) for excluded in exclude_domains):
                                domains.add(domain)
                except Exception:
                    pass

    return domains


def discover_proprietary_keywords(must_gather_path: str) -> Set[str]:
    """Discover proprietary keywords from Kubernetes resources."""
    keywords = set()

    # Standard OpenShift/Kubernetes prefixes to exclude
    exclude_prefixes = {
        'openshift-', 'kube-', 'default', 'istio-', 'knative-',
        'prometheus', 'grafana', 'etcd', 'apiserver', 'controller',
    }

    # Look for custom namespace names
    namespace_pattern = '**/cluster-scoped-resources/core/namespaces/*.yaml'

    for file_path in Path(must_gather_path).glob(namespace_pattern):
        if file_path.is_file():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    if data and 'metadata' in data and 'name' in data['metadata']:
                        ns_name = data['metadata']['name']
                        # Skip standard namespaces
                        if not any(ns_name.startswith(prefix) for prefix in exclude_prefixes):
                            keywords.add(ns_name)

                        # Check labels and annotations for custom values
                        if 'labels' in data['metadata']:
                            for key, value in data['metadata']['labels'].items():
                                if '/' not in value and len(value) > 3:  # Simple heuristic
                                    if not any(value.startswith(prefix) for prefix in exclude_prefixes):
                                        keywords.add(value)
            except Exception:
                pass

    # Look for custom image repositories
    pod_pattern = '**/namespaces/**/core/pods/*.yaml'
    image_pattern = r'image:\s*([a-z0-9.-]+)/([a-z0-9._-]+)/'

    scanned = 0
    for file_path in Path(must_gather_path).glob(pod_pattern):
        if scanned >= 100:  # Limit for performance
            break
        if file_path.is_file():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    matches = re.findall(image_pattern, content)
                    for registry, org in matches:
                        # Skip well-known registries
                        if registry not in ['quay.io', 'registry.redhat.io', 'gcr.io', 'docker.io']:
                            keywords.add(registry)
                        # Add org if not standard
                        if org not in ['openshift-release-dev', 'openshift', 'redhat']:
                            keywords.add(org)
                scanned += 1
            except Exception:
                pass

    return keywords


def generate_config(must_gather_path: str, output_file: str) -> Dict:
    """Generate must-gather-clean config based on discovery analysis."""

    print("[*] Starting discovery analysis (all processing is local)...")
    print(f"[*] Analyzing must-gather at: {must_gather_path}\n")

    # Perform discovery
    print("[1/3] Scanning for secret patterns...")
    secret_patterns = scan_for_secret_patterns(must_gather_path)

    print("[2/3] Discovering domain names...")
    domain_names = discover_domain_names(must_gather_path)

    print("[3/3] Identifying proprietary keywords...")
    keywords = discover_proprietary_keywords(must_gather_path)

    # Display findings
    print("\n" + "="*70)
    print("DISCOVERY RESULTS")
    print("="*70)

    if secret_patterns:
        print("\nPotential secret patterns found:")
        for secret_type, count in secret_patterns.items():
            print(f"  - {secret_type}: {count} occurrence(s)")
    else:
        print("\nNo known secret patterns detected")

    if domain_names:
        print(f"\nCustom domain names ({len(domain_names)} found):")
        for domain in sorted(domain_names)[:20]:  # Show first 20
            print(f"  - {domain}")
        if len(domain_names) > 20:
            print(f"  ... and {len(domain_names) - 20} more")
    else:
        print("\nNo custom domain names found")

    if keywords:
        print(f"\nProprietary keywords ({len(keywords)} found):")
        for keyword in sorted(keywords)[:20]:  # Show first 20
            print(f"  - {keyword}")
        if len(keywords) > 20:
            print(f"  ... and {len(keywords) - 20} more")
    else:
        print("\nNo proprietary keywords detected")

    print("\n" + "="*70)

    # Build configuration
    config = {
        'config': {
            'obfuscate': [],
            'omit': []
        }
    }

    # Add regex patterns for discovered secrets
    for secret_type in secret_patterns.keys():
        if secret_type in SECRET_PATTERNS:
            config['config']['obfuscate'].append({
                'type': 'Regex',
                'regex': SECRET_PATTERNS[secret_type],
                'target': 'FileContents'
            })

    # Add proprietary keywords
    if keywords:
        keyword_replacements = {}
        for i, keyword in enumerate(sorted(keywords), 1):
            keyword_replacements[keyword] = f'keyword-{i:04d}'

        config['config']['obfuscate'].append({
            'type': 'Keywords',
            'target': 'All',
            'replacement': keyword_replacements
        })

    # Add domain obfuscation
    if domain_names:
        config['config']['obfuscate'].append({
            'type': 'Domain',
            'replacementType': 'Consistent',
            'target': 'All',
            'domainNames': sorted(domain_names)
        })

    # Add standard obfuscation
    config['config']['obfuscate'].extend([
        {
            'type': 'IP',
            'replacementType': 'Consistent',
            'target': 'All'
        },
        {
            'type': 'MAC',
            'replacementType': 'Consistent',
            'target': 'All'
        }
    ])

    # Add standard omissions
    config['config']['omit'].extend([
        {
            'type': 'Kubernetes',
            'kubernetesResource': {'kind': 'Secret'}
        },
        {
            'type': 'Kubernetes',
            'kubernetesResource': {'kind': 'ConfigMap'}
        },
        {
            'type': 'Kubernetes',
            'kubernetesResource': {
                'kind': 'CertificateSigningRequest',
                'apiVersion': 'certificates.k8s.io/v1'
            }
        }
    ])

    # Write config file
    with open(output_file, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    print(f"\n[✓] Configuration generated: {output_file}")
    print("\nReview the generated config and edit if needed before using it.")

    return config


def main():
    if len(sys.argv) < 3:
        print("Usage: discover_config.py <must-gather-path> <output-config-file>")
        sys.exit(1)

    must_gather_path = sys.argv[1]
    output_file = sys.argv[2]

    if not os.path.exists(must_gather_path):
        print(f"Error: Must-gather path does not exist: {must_gather_path}")
        sys.exit(1)

    try:
        generate_config(must_gather_path, output_file)
    except Exception as e:
        print(f"Error during discovery: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
