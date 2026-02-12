#!/usr/bin/env python3
"""
GitHub Pull Request Analyzer
Analyzes PR history to extract design decisions and lessons learned
"""

import json
import subprocess
import sys
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime, timedelta
import re


class GitHubPRAnalyzer:
    """Analyzes GitHub PRs for historical context"""

    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize the PR analyzer

        Args:
            cache_dir: Directory to cache API results
        """
        self.cache_dir = Path(cache_dir) if cache_dir else Path(".work/jira/analyze-rfe/cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _run_gh_command(self, args: List[str], cache_key: Optional[str] = None) -> Optional[str]:
        """Run gh CLI command with optional caching"""
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
                timeout=60,
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
                return None

        except subprocess.TimeoutExpired:
            print(f"Warning: Command timed out: gh {' '.join(args)}", file=sys.stderr)
            return None
        except Exception as e:
            print(f"Warning: Command failed: {e}", file=sys.stderr)
            return None

    def search_relevant_prs(
        self,
        repo_name: str,
        keywords: List[str],
        max_results: int = 20,
        months_back: int = 12
    ) -> List[Dict]:
        """
        Search for PRs relevant to the RFE keywords

        Args:
            repo_name: Repository name (e.g., "openshift/cert-manager-operator")
            keywords: Search keywords from RFE
            max_results: Maximum PRs to return
            months_back: How far back to search

        Returns:
            List of PR summaries sorted by relevance
        """
        # Build search query
        query_parts = [f'"{kw}"' for kw in keywords[:3]]  # Limit to 3 keywords
        query = " OR ".join(query_parts) if query_parts else ""

        if not query:
            return []

        # Search merged PRs
        pr_data = self._run_gh_command(
            ["search", "prs",
             "--repo", repo_name,
             "--state", "merged",
             "--sort", "updated",
             "--limit", str(max_results),
             "--json", "number,title,url,body,mergedAt,additions,deletions,changedFiles",
             query],
            cache_key=f"pr_search_{repo_name.replace('/', '_')}_{hash(query) % 10000}"
        )

        if not pr_data:
            return []

        try:
            prs = json.loads(pr_data)
            # Rank by relevance
            ranked_prs = self._rank_prs_by_relevance(prs, keywords)
            return ranked_prs[:max_results]
        except json.JSONDecodeError:
            return []

    def _rank_prs_by_relevance(self, prs: List[Dict], keywords: List[str]) -> List[Dict]:
        """
        Rank PRs by keyword relevance

        Scoring:
        - Title match (keyword in title): +10 points
        - Body match (keyword in body): +3 points
        - Recent (merged in last 6 months): +5 points
        - Large PR (changed files > 10): -2 points (complexity penalty)
        """
        scored_prs = []

        for pr in prs:
            score = 0
            title = pr.get("title", "").lower()
            body = pr.get("body", "").lower()

            # Keyword matching
            for keyword in keywords:
                kw_lower = keyword.lower()
                if kw_lower in title:
                    score += 10
                if kw_lower in body:
                    score += 3

            # Recency bonus
            merged_at = pr.get("mergedAt")
            if merged_at:
                try:
                    merged_date = datetime.fromisoformat(merged_at.replace('Z', '+00:00'))
                    six_months_ago = datetime.now(merged_date.tzinfo) - timedelta(days=180)
                    if merged_date > six_months_ago:
                        score += 5
                except (ValueError, TypeError):
                    pass

            # Complexity penalty (very large PRs may be less relevant)
            changed_files = pr.get("changedFiles", 0)
            if changed_files > 20:
                score -= 2

            pr["relevance_score"] = score
            scored_prs.append(pr)

        # Sort by score descending
        scored_prs.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        return scored_prs

    def analyze_pr_details(self, repo_name: str, pr_number: int) -> Dict:
        """
        Get detailed PR information including comments and reviews

        Args:
            repo_name: Repository name
            pr_number: PR number

        Returns:
            Dict with PR details, comments, reviews
        """
        pr_data = self._run_gh_command(
            ["pr", "view", str(pr_number),
             "--repo", repo_name,
             "--json", "number,title,body,url,author,mergedAt,additions,deletions,changedFiles,comments,reviews"],
            cache_key=f"pr_details_{repo_name.replace('/', '_')}_{pr_number}"
        )

        if not pr_data:
            return {}

        try:
            return json.loads(pr_data)
        except json.JSONDecodeError:
            return {}

    def extract_design_insights(self, pr_details: Dict) -> Dict:
        """
        Extract design decisions, rationale, and lessons from PR

        Args:
            pr_details: Full PR details from analyze_pr_details

        Returns:
            Dict with extracted insights
        """
        insights = {
            "design_sections": [],
            "rationale": [],
            "lessons": [],
            "trade_offs": []
        }

        body = pr_details.get("body", "")

        # Extract design sections
        design_patterns = [
            r'##?\s*Design\s*\n(.*?)(?=\n##|\Z)',
            r'##?\s*Architecture\s*\n(.*?)(?=\n##|\Z)',
            r'##?\s*Approach\s*\n(.*?)(?=\n##|\Z)',
            r'##?\s*Implementation\s*\n(.*?)(?=\n##|\Z)',
        ]

        for pattern in design_patterns:
            matches = re.findall(pattern, body, re.IGNORECASE | re.DOTALL)
            for match in matches:
                insights["design_sections"].append(match.strip()[:500])  # Limit length

        # Extract rationale
        rationale_keywords = ["why", "because", "rationale", "reason", "motivation"]
        for comment in pr_details.get("comments", []):
            comment_body = comment.get("body", "").lower()
            for keyword in rationale_keywords:
                if keyword in comment_body:
                    insights["rationale"].append(comment.get("body", "")[:300])
                    break

        # Extract trade-offs
        trade_off_keywords = ["trade-off", "tradeoff", "alternative", "versus", "vs.", "pros and cons"]
        for comment in pr_details.get("comments", []):
            comment_body = comment.get("body", "").lower()
            for keyword in trade_off_keywords:
                if keyword in comment_body:
                    insights["trade_offs"].append(comment.get("body", "")[:300])
                    break

        # Extract lessons
        lesson_keywords = ["learned", "lesson", "mistake", "should have", "next time", "avoid"]
        combined_text = body + " " + " ".join([c.get("body", "") for c in pr_details.get("comments", [])])
        for keyword in lesson_keywords:
            if keyword in combined_text.lower():
                # Extract sentences containing the keyword
                sentences = re.split(r'[.!?]\s+', combined_text)
                for sentence in sentences:
                    if keyword in sentence.lower():
                        insights["lessons"].append(sentence.strip()[:200])

        return insights

    def search_adrs(self, repo_name: str) -> List[Dict]:
        """
        Search for Architecture Decision Records

        Args:
            repo_name: Repository name

        Returns:
            List of ADR files found
        """
        adr_paths = [
            "docs/adr",
            "docs/design",
            "docs/architecture",
            "design",
            "adr"
        ]

        adrs = []
        for path in adr_paths:
            adr_data = self._run_gh_command(
                ["api", f"repos/{repo_name}/contents/{path}",
                 "--jq", ".[] | select(.name | endswith(\".md\")) | {name: .name, path: .path, url: .html_url}"],
                cache_key=f"adr_{repo_name.replace('/', '_')}_{path.replace('/', '_')}"
            )

            if adr_data:
                for line in adr_data.strip().split('\n'):
                    if line:
                        try:
                            adr = json.loads(line)
                            adrs.append(adr)
                        except json.JSONDecodeError:
                            continue

        return adrs

    def search_lessons_learned_issues(self, repo_name: str, limit: int = 5) -> List[Dict]:
        """
        Search for issues/bugs with lessons learned

        Args:
            repo_name: Repository name
            limit: Max issues to return

        Returns:
            List of issues with lessons
        """
        issue_data = self._run_gh_command(
            ["search", "issues",
             "--repo", repo_name,
             "learned OR mistake OR lesson OR regression",
             "--state", "closed",
             "--limit", str(limit),
             "--json", "number,title,body,labels,url"],
            cache_key=f"lessons_{repo_name.replace('/', '_')}"
        )

        if not issue_data:
            return []

        try:
            return json.loads(issue_data)
        except json.JSONDecodeError:
            return []

    def analyze_pr_effort(self, pr_details: Dict) -> Dict:
        """
        Estimate effort from PR metrics

        Args:
            pr_details: PR details

        Returns:
            Effort analysis
        """
        return {
            "changed_files": pr_details.get("changedFiles", 0),
            "additions": pr_details.get("additions", 0),
            "deletions": pr_details.get("deletions", 0),
            "size_category": self._categorize_pr_size(pr_details),
            "merged_at": pr_details.get("mergedAt")
        }

    def _categorize_pr_size(self, pr_details: Dict) -> str:
        """Categorize PR size (XS/S/M/L/XL)"""
        changed_files = pr_details.get("changedFiles", 0)
        additions = pr_details.get("additions", 0)

        if changed_files <= 3 and additions <= 100:
            return "XS"
        elif changed_files <= 10 and additions <= 300:
            return "S"
        elif changed_files <= 25 and additions <= 800:
            return "M"
        elif changed_files <= 50 and additions <= 1500:
            return "L"
        else:
            return "XL"


def main():
    """Test the PR analyzer"""
    if len(sys.argv) < 3:
        print("Usage: github_pr_analyzer.py <repo-name> <keyword1> [keyword2] [keyword3]")
        print("\nExample: github_pr_analyzer.py openshift/cert-manager-operator certificate rotation")
        sys.exit(1)

    repo_name = sys.argv[1]
    keywords = sys.argv[2:]

    analyzer = GitHubPRAnalyzer()

    print(f"Searching PRs in {repo_name} for keywords: {keywords}\n")

    # Search PRs
    prs = analyzer.search_relevant_prs(repo_name, keywords, max_results=10)

    print("=" * 70)
    print(f"FOUND {len(prs)} RELEVANT PRs")
    print("=" * 70)

    for i, pr in enumerate(prs[:5], 1):
        print(f"\n{i}. PR #{pr['number']}: {pr['title']}")
        print(f"   Score: {pr.get('relevance_score', 0)}")
        print(f"   URL: {pr['url']}")
        print(f"   Changed Files: {pr.get('changedFiles', 0)}")

        # Get detailed analysis for top PR
        if i == 1:
            print(f"\n{'=' * 70}")
            print(f"DETAILED ANALYSIS: PR #{pr['number']}")
            print("=" * 70)

            details = analyzer.analyze_pr_details(repo_name, pr['number'])
            if details:
                insights = analyzer.extract_design_insights(details)
                print("\nDesign Sections:")
                for section in insights['design_sections'][:2]:
                    print(f"  - {section[:200]}...")

                print("\nRationale:")
                for rationale in insights['rationale'][:2]:
                    print(f"  - {rationale[:150]}...")

                effort = analyzer.analyze_pr_effort(details)
                print(f"\nEffort: {effort['size_category']} ({effort['changed_files']} files, {effort['additions']} additions)")

    # Search for ADRs
    print(f"\n{'=' * 70}")
    print("ARCHITECTURE DECISION RECORDS")
    print("=" * 70)
    adrs = analyzer.search_adrs(repo_name)
    if adrs:
        for adr in adrs[:5]:
            print(f"  - {adr['name']}: {adr['url']}")
    else:
        print("  No ADRs found")


if __name__ == "__main__":
    main()
