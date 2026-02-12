# Upstream Analysis Guide

## Overview

When analyzing OpenShift components, the script can optionally analyze the upstream repository to provide comparative insights and identify adoption opportunities.

## When You'll Be Asked

When running component context analysis, if an upstream repository is discovered, you'll see this prompt:

```
======================================================================
Upstream Repository Found for cert-manager
======================================================================
Upstream: cert-manager/cert-manager

Upstream analysis includes:
  - Codebase structure and architecture
  - Historical PR analysis and design decisions
  - Architecture Decision Records (ADRs)

This is useful for:
  - Understanding original design intent
  - Finding upstream features to adopt
  - Identifying differences between upstream/downstream

Note: This will add ~15-30 seconds to analysis time
======================================================================

Analyze upstream repository 'cert-manager/cert-manager'? [y/N]:
```

## When to Answer "Yes"

### Upstream Adoption RFEs

**Example**: "Adopt upstream cert-manager ACME DNS-01 challenge support"

**Why**: You need to understand how upstream implemented this feature.

**Value**:
- See original design decisions
- Identify integration patterns to reuse
- Understand API contracts
- Find lessons learned from upstream PRs

### Feature Parity Analysis

**Example**: "Enhance OpenShift cert-manager to match upstream capabilities"

**Why**: Need to identify gaps between upstream and downstream.

**Value**:
- List of CRDs/APIs in upstream but not downstream
- Features available upstream to consider adopting
- Understand why divergence exists

### Architectural Alignment

**Example**: "Refactor cert-manager operator to align with upstream architecture"

**Why**: Planning major architectural changes.

**Value**:
- Compare implementation approaches
- Validate proposed changes against upstream patterns
- Identify risks from diverging from upstream

### Design Validation

**Example**: "Implement custom certificate validation for OpenShift"

**Why**: Want to check if upstream has similar capabilities or lessons learned.

**Value**:
- See if upstream solved similar problems
- Avoid reinventing the wheel
- Learn from upstream mistakes

## When to Answer "No"

### OpenShift-Only Features

**Example**: "Add Red Hat SSO integration for certificate management"

**Why**: This is OpenShift-specific, no upstream equivalent.

**Value**: None - upstream won't have relevant insights.

### Time-Constrained Analysis

**Example**: Quick RFE review needed for planning meeting in 30 minutes.

**Why**: Adding 15-30 seconds per component may not be worth it.

**Value**: Minimal when time is critical.

### Known Divergence

**Example**: "Enhance OpenShift-specific certificate rotation logic"

**Why**: You already know OpenShift intentionally differs from upstream here.

**Value**: Limited - you understand the divergence already.

### Simple Bug Fixes

**Example**: "Fix certificate renewal notification timing issue"

**Why**: Bug is in OpenShift-specific code, not upstream-related.

**Value**: None - upstream won't have relevant bug history.

## What You Get with Upstream Analysis

### 1. Architecture Comparison

See how upstream and downstream architectures differ:

```markdown
**Architecture Comparison**:
- Downstream: Kubernetes Operator
- Upstream: Kubernetes Operator
```

Or:

```markdown
**Architecture Comparison**:
- Downstream: Kubernetes Operator (OpenShift-specific)
- Upstream: CLI Tool + Controllers
- *Note: Different architectures indicate OpenShift adaptation for operator model*
```

### 2. Upstream Implementation Patterns

Learn from upstream's approach:

```markdown
**Upstream Implementation Patterns**:
- Upstream PR #1234: ACME DNS-01 challenge implementation
  - Pattern: Provider interface with pluggable DNS backends
  - Why: Enable support for multiple cloud providers (Route53, CloudFlare, etc.)
  - Lesson: Interface-based design allows easy extension
```

### 3. Upstream Architecture Decisions

See documented architectural choices:

```markdown
**Upstream Architecture Decisions**:
- ADR-003-storage: Use Kubernetes secrets for certificate storage
  - Rationale: Native Kubernetes integration, standard RBAC model
  - Trade-offs: Secret size limits vs. custom CRD overhead
```

### 4. Adoption Recommendations

Get specific guidance on what to consider:

```markdown
**Upstream Adoption Considerations**:
- Upstream has 7 CRDs vs downstream 5 - consider adopting:
  - ClusterIssuer: Cluster-scoped issuer (currently namespace-scoped only)
  - Challenge: ACME challenge tracking (currently internal-only)
- Review upstream PR #1234 for ACME implementation patterns
- Consider contributing OpenShift security enhancements back to upstream
```

### 5. Enhanced Recommendations

Recommended approach section includes upstream guidance:

```markdown
**Recommended Approach for RFE Implementation**:
- Review downstream PR #456 for similar implementation patterns
- Review upstream PR #1234 for original design approach
- Consider adopting upstream patterns where applicable to OpenShift
- Align with upstream architecture where possible to ease future updates
- Avoid: Diverging significantly from upstream without strong justification
```

## Command-Line Options

### Always Analyze Upstream (No Prompt)

```bash
./gather_component_context.py cert-manager \
  --keywords "certificate" \
  --analyze-upstream
```

**Use when**: You know upstream analysis is valuable (e.g., upstream adoption RFE).

### Never Analyze Upstream (No Prompt)

```bash
./gather_component_context.py cert-manager \
  --keywords "certificate" \
  --skip-upstream
```

**Use when**: You know upstream analysis isn't needed (e.g., OpenShift-only feature).

### Non-Interactive Mode

```bash
./gather_component_context.py cert-manager \
  --keywords "certificate" \
  --no-interactive
```

**Use when**: Running in automation, CI/CD, or scripts. Defaults to skipping upstream.

### Interactive Mode (Default)

```bash
./gather_component_context.py cert-manager \
  --keywords "certificate"
```

**Use when**: Running interactively and want to decide per-component.

## Performance Considerations

### Time Impact

**Without upstream analysis**:
- Single component: ~15-20 seconds (first run)
- With cache: <5 seconds

**With upstream analysis**:
- Single component: ~30-45 seconds (first run)
- With cache: <10 seconds

**Multiple components** (3 components, with upstream):
- First run: ~2-3 minutes
- Cached: ~15-20 seconds

### API Rate Limits

**Downstream only**:
- ~20-30 GitHub API requests per component

**With upstream**:
- ~40-60 GitHub API requests per component

**GitHub API limit**: 5000 requests/hour (authenticated)

**Practical limit**: Can analyze ~100+ components/hour even with upstream analysis.

## Integration with /jira:analyze-rfe

When `/jira:analyze-rfe` runs and discovers components with upstream repositories, it should:

1. **Check if RFE mentions upstream** (e.g., "adopt upstream", "upstream feature", "parity")
2. **If yes**: Automatically enable upstream analysis (`analyze_upstream=True`)
3. **If no**: Ask user via `AskUserQuestion` tool
4. **Non-interactive mode**: Skip upstream by default

**Example integration**:

```python
# In analyze-rfe skill implementation
rfe_text = rfe_data["fields"]["description"].lower()

# Auto-enable if RFE mentions upstream
analyze_upstream = any(keyword in rfe_text for keyword in [
    "upstream", "parity", "adopt", "alignment"
])

# Or ask user
if not analyze_upstream and has_upstream:
    response = AskUserQuestion(
        questions=[{
            "question": "Upstream repository found. Analyze upstream for design insights?",
            "header": "Upstream",
            "options": [
                {"label": "Yes", "description": "Analyze upstream repo for context"},
                {"label": "No", "description": "Skip upstream analysis"}
            ]
        }]
    )
    analyze_upstream = (response == "Yes")

# Run context gathering
context = gather_component_context(
    component_name,
    rfe_keywords=keywords,
    analyze_upstream=analyze_upstream,
    interactive=False  # Non-interactive when called from skill
)
```

## Examples

### Example 1: Upstream Adoption RFE

**RFE**: "Adopt upstream cert-manager external DNS support"

**Answer**: **Yes** - Need to understand upstream implementation

**Command**:
```bash
./gather_component_context.py cert-manager \
  --keywords "external DNS" "DNS-01" \
  --analyze-upstream
```

### Example 2: OpenShift-Specific Feature

**RFE**: "Add Red Hat SSO integration for certificate issuance"

**Answer**: **No** - OpenShift-specific, no upstream equivalent

**Command**:
```bash
./gather_component_context.py cert-manager \
  --keywords "SSO" "integration" \
  --skip-upstream
```

### Example 3: Uncertain - Let Me Decide Per Component

**RFE**: "Enhance certificate rotation capabilities"

**Answer**: **Interactive** - May want upstream for some components

**Command**:
```bash
./gather_component_context.py cert-manager ingress authentication \
  --keywords "certificate rotation"
# Will prompt for each component that has upstream
```

## Summary

**Default behavior**: Ask the user when upstream is discovered.

**Recommended practice**:
- Answer "Yes" for upstream-related RFEs
- Answer "No" for OpenShift-only features
- Use `--analyze-upstream` flag for known upstream adoption cases
- Use `--skip-upstream` flag for known OpenShift-only features

**Performance**: Adds ~15-30 seconds per component, well within acceptable range for valuable insights.
