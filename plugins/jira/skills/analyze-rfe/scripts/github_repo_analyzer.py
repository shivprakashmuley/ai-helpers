#!/usr/bin/env python3
"""
GitHub Repository Analyzer
Discovers and analyzes OpenShift component repositories using GitHub CLI (gh)
"""

import json
import os
import subprocess
import sys
from typing import Dict, List, Optional, Tuple
from pathlib import Path


class GitHubRepoAnalyzer:
    """Analyzes GitHub repositories remotely via gh CLI"""

    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize the analyzer

        Args:
            cache_dir: Directory to cache API results (default: .work/jira/analyze-rfe/cache)
        """
        self.cache_dir = Path(cache_dir) if cache_dir else Path(".work/jira/analyze-rfe/cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Check if gh CLI is available
        if not self._check_gh_cli():
            print("Error: GitHub CLI (gh) not found", file=sys.stderr)
            print("Install from: https://cli.github.com/", file=sys.stderr)
            sys.exit(1)

    def _check_gh_cli(self) -> bool:
        """Check if gh CLI is installed and authenticated"""
        try:
            result = subprocess.run(
                ["gh", "auth", "status"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def _run_gh_command(self, args: List[str], cache_key: Optional[str] = None) -> Optional[str]:
        """
        Run gh CLI command with optional caching

        Args:
            args: Command arguments
            cache_key: Cache file key (if None, no caching)

        Returns:
            Command output or None on error
        """
        # Check cache first
        if cache_key:
            cache_file = self.cache_dir / f"{cache_key}.json"
            if cache_file.exists():
                return cache_file.read_text()

        try:
            result = subprocess.run(
                ["gh"] + args,
                capture_output=True,
                text=True,
                timeout=30,
                check=False
            )

            if result.returncode == 0:
                output = result.stdout.strip()
                # Cache successful results
                if cache_key and output:
                    cache_file = self.cache_dir / f"{cache_key}.json"
                    cache_file.write_text(output)
                return output
            else:
                # Not an error, just no results (e.g., repo not found)
                return None

        except subprocess.TimeoutExpired:
            print(f"Warning: Command timed out: gh {' '.join(args)}", file=sys.stderr)
            return None
        except Exception as e:
            print(f"Warning: Command failed: gh {' '.join(args)}: {e}", file=sys.stderr)
            return None

    def discover_repositories(self, component_name: str) -> Dict[str, any]:
        """
        Discover downstream, upstream, and related repositories

        Args:
            component_name: Component name (e.g., "cert-manager", "hypershift")

        Returns:
            Dict with downstream, upstream, and related repos
        """
        repos = {
            "component": component_name,
            "downstream": None,
            "upstream": None,
            "related": []
        }

        # Try common OpenShift repo patterns
        patterns = [
            component_name,
            f"{component_name}-operator",
            f"cluster-{component_name}-operator",
            f"{component_name}-controller",
        ]

        for pattern in patterns:
            repo_data = self._run_gh_command(
                ["repo", "view", f"openshift/{pattern}", "--json", "name,url,description,defaultBranchRef"],
                cache_key=f"repo_openshift_{pattern}"
            )

            if repo_data:
                try:
                    repo_info = json.loads(repo_data)
                    repos["downstream"] = {
                        "name": f"openshift/{pattern}",
                        "url": repo_info.get("url"),
                        "description": repo_info.get("description", ""),
                        "default_branch": repo_info.get("defaultBranchRef", {}).get("name", "main")
                    }
                    break  # Found it
                except json.JSONDecodeError:
                    continue

        # If downstream found, try to find upstream from README
        if repos["downstream"]:
            upstream = self._find_upstream_reference(repos["downstream"]["name"])
            if upstream:
                repos["upstream"] = upstream

        # Search for related repos
        related = self._search_related_repos(component_name)
        repos["related"] = related

        return repos

    def _find_upstream_reference(self, repo_name: str) -> Optional[Dict]:
        """Extract upstream repository reference from README"""
        readme_data = self._run_gh_command(
            ["repo", "view", repo_name, "--json", "readme"],
            cache_key=f"readme_{repo_name.replace('/', '_')}"
        )

        if not readme_data:
            return None

        try:
            readme_info = json.loads(readme_data)
            readme_text = readme_info.get("readme", "")

            # Look for common upstream patterns
            # e.g., "upstream: https://github.com/org/repo"
            # e.g., "based on https://github.com/org/repo"
            import re
            patterns = [
                r'upstream[:\s]+(?:https?://)?github\.com/([^/\s]+)/([^/\s\)]+)',
                r'based on[:\s]+(?:https?://)?github\.com/([^/\s]+)/([^/\s\)]+)',
                r'fork of[:\s]+(?:https?://)?github\.com/([^/\s]+)/([^/\s\)]+)',
            ]

            for pattern in patterns:
                match = re.search(pattern, readme_text, re.IGNORECASE)
                if match:
                    org, repo = match.groups()
                    return {
                        "name": f"{org}/{repo}",
                        "url": f"https://github.com/{org}/{repo}"
                    }
        except (json.JSONDecodeError, Exception):
            pass

        return None

    def _search_related_repos(self, component_name: str, limit: int = 5) -> List[Dict]:
        """Search for related repositories in openshift org"""
        search_data = self._run_gh_command(
            ["search", "repos", "--owner", "openshift", component_name,
             "--json", "name,description,url", "--limit", str(limit)],
            cache_key=f"search_repos_{component_name}"
        )

        if not search_data:
            return []

        try:
            results = json.loads(search_data)
            return [
                {
                    "name": f"openshift/{r['name']}",
                    "url": r.get("url"),
                    "description": r.get("description", "")
                }
                for r in results
            ]
        except json.JSONDecodeError:
            return []

    def analyze_codebase_structure(self, repo_name: str) -> Dict[str, any]:
        """
        Analyze repository structure to determine architecture and key components

        Args:
            repo_name: Full repo name (e.g., "openshift/cert-manager-operator")

        Returns:
            Dict with architecture type, key packages, API types
        """
        structure = {
            "architecture": "Unknown",
            "key_packages": [],
            "api_types": [],
            "controllers": []
        }

        # Get root directory structure
        root_contents = self._run_gh_command(
            ["api", f"repos/{repo_name}/contents/", "--jq", ".[].name"],
            cache_key=f"root_{repo_name.replace('/', '_')}"
        )

        if not root_contents:
            return structure

        root_files = root_contents.strip().split('\n')

        # Detect architecture pattern
        has_crd = "config" in root_files or any("crd" in f.lower() for f in root_files)
        has_cmd = "cmd" in root_files
        has_pkg = "pkg" in root_files
        has_dockerfile = any("dockerfile" in f.lower() for f in root_files)

        if has_crd:
            structure["architecture"] = "Kubernetes Operator"
            # Get CRDs
            structure["api_types"] = self._extract_crds(repo_name)
            # Get controllers
            structure["controllers"] = self._find_controllers(repo_name)
        elif has_cmd and has_pkg:
            structure["architecture"] = "CLI Tool / Binary"
        elif has_pkg and not has_cmd:
            structure["architecture"] = "Library"
        elif has_dockerfile:
            structure["architecture"] = "Containerized Service"

        # Get key packages
        if has_pkg:
            structure["key_packages"] = self._get_key_packages(repo_name)

        return structure

    def _extract_crds(self, repo_name: str) -> List[Dict]:
        """Extract CRD definitions"""
        crd_paths = [
            "config/crd/bases",
            "config/crds",
            "deploy/crds",
        ]

        crds = []
        for path in crd_paths:
            crd_data = self._run_gh_command(
                ["api", f"repos/{repo_name}/contents/{path}", "--jq", ".[] | select(.name | endswith(\".yaml\")) | .name"],
                cache_key=f"crds_{repo_name.replace('/', '_')}_{path.replace('/', '_')}"
            )

            if crd_data:
                crd_files = crd_data.strip().split('\n')
                for crd_file in crd_files:
                    if crd_file:
                        crds.append({
                            "file": crd_file,
                            "path": f"{path}/{crd_file}"
                        })
                break  # Found CRDs, no need to check other paths

        return crds

    def _find_controllers(self, repo_name: str) -> List[str]:
        """Find controller files"""
        pkg_controllers = self._run_gh_command(
            ["api", f"repos/{repo_name}/contents/pkg/controllers", "--jq", ".[].name"],
            cache_key=f"controllers_{repo_name.replace('/', '_')}"
        )

        if pkg_controllers:
            return [c for c in pkg_controllers.strip().split('\n') if c]

        return []

    def _get_key_packages(self, repo_name: str) -> List[Dict]:
        """Get key packages from pkg/ directory"""
        pkg_data = self._run_gh_command(
            ["api", f"repos/{repo_name}/contents/pkg", "--jq", ".[] | select(.type == \"dir\") | {{name: .name, path: .path}}"],
            cache_key=f"pkg_{repo_name.replace('/', '_')}"
        )

        if not pkg_data:
            return []

        packages = []
        for line in pkg_data.strip().split('\n'):
            if line:
                try:
                    pkg = json.loads(line)
                    packages.append(pkg)
                except json.JSONDecodeError:
                    continue

        return packages[:10]  # Limit to top 10

    def get_repository_metadata(self, repo_name: str) -> Dict:
        """Get basic repository metadata"""
        data = self._run_gh_command(
            ["repo", "view", repo_name, "--json",
             "name,description,url,defaultBranchRef,languages,stargazerCount,createdAt,updatedAt"],
            cache_key=f"metadata_{repo_name.replace('/', '_')}"
        )

        if data:
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                pass

        return {}


def main():
    """Test the analyzer"""
    if len(sys.argv) < 2:
        print("Usage: github_repo_analyzer.py <component-name>")
        print("\nExample: github_repo_analyzer.py cert-manager")
        sys.exit(1)

    component_name = sys.argv[1]

    analyzer = GitHubRepoAnalyzer()

    print(f"Analyzing component: {component_name}\n")

    # Discover repositories
    repos = analyzer.discover_repositories(component_name)
    print("=" * 70)
    print("REPOSITORIES")
    print("=" * 70)
    print(json.dumps(repos, indent=2))

    # Analyze structure if downstream repo found
    if repos["downstream"]:
        downstream_name = repos["downstream"]["name"]
        print(f"\n{'=' * 70}")
        print(f"CODEBASE STRUCTURE: {downstream_name}")
        print("=" * 70)
        structure = analyzer.analyze_codebase_structure(downstream_name)
        print(json.dumps(structure, indent=2))


if __name__ == "__main__":
    main()
