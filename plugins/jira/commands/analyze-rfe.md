---
description: Analyze an RFE and output meaningful EPIC, user stories, and their outcomes
argument-hint: <rfe-key>
---

## Name
jira:analyze-rfe

## Synopsis
```
/jira:analyze-rfe <rfe-key>
```

## Description

The `jira:analyze-rfe` command analyzes a Request for Enhancement (RFE) from Jira and generates a comprehensive breakdown of Epics, user stories, and their outcomes with technical feasibility assessment. This helps product and engineering teams transform customer-driven RFEs into actionable, well-estimated implementation plans.

This command is particularly useful for:
- Breaking down complex RFEs into implementable work items
- Planning sprints and releases from customer requests with effort estimates
- Identifying technical risks, dependencies, and blockers early
- Creating epics and stories that align with RFE scope
- Understanding the full scope and outcomes of an RFE before implementation
- Preparing for refinement or planning sessions with comprehensive analysis
- Discovering related work to prevent duplication and enable reuse

The command performs deep analysis of:
- The RFE's nature and description
- Current limitations and desired behavior
- Business requirements and use cases
- Affected packages and components
- **Technical complexity and risks**: Assesses implementation difficulty, identifies blockers
- **Cross-component dependencies**: Maps integration points and team handoffs
- **Non-functional requirements**: Generates NFR stories for performance, security, scalability, observability
- **Effort estimation**: Provides t-shirt sizing (XS/S/M/L/XL) for sprint planning
- **Related work discovery**: Searches Jira for related RFEs, epics, bugs to prevent duplication
- **Workspace context** (optional): When the workspace contains `context.md` files (e.g., `docs/component-context/context.md`), the command loads component Purpose, Scope, and Key Areas to enrich the breakdown
- **Comprehensive component context**: Deep repository analysis including:
  - Repository discovery (downstream/upstream/related repos)
  - Codebase structure analysis (architecture patterns, key packages, API types)
  - Implementation logic understanding (reconciliation flows, integration patterns)
  - Historical context (relevant PRs, design discussions, ADRs, lessons learned)
  - Synthesized insights (design principles, risk factors, recommended approach)

## Implementation

This command invokes the `analyze-rfe` skill to:

1. **Fetch RFE** - Retrieve the RFE from Jira via MCP
2. **Parse Structure** - Extract nature, description, business requirements, affected components
3. **Discover Related Work** - Search Jira for related RFEs, epics, bugs; identify reuse opportunities
4. **Gather Workspace Context** - Search for `context.md` files in the workspace (e.g., `docs/component-context/context.md`). When components match the RFE, load Purpose, Scope, Key Areas, and use them to enrich epics and stories
5. **Comprehensive Component Context** - For affected components:
   - Discover repositories (downstream, upstream, related)
   - Analyze codebase structure (architecture, packages, API types)
   - Understand implementation logic (patterns, integration points)
   - Gather historical context (PRs, design discussions, ADRs, lessons learned)
   - Synthesize insights (design principles, recommended approach, risks)
6. **Generate EPIC(s)** - Break down the RFE into one or more epics with scope and acceptance criteria
7. **Assess Technical Complexity** - Analyze complexity, identify risks, blockers, and tech debt impact
8. **Map Dependencies** - Identify epic dependencies, integration points, and cross-team handoffs
9. **Generate User Stories** - Create user stories for each epic in proper "As a... I want... So that..." format
10. **Add NFR Stories** - Generate non-functional requirement stories for performance, security, scalability, observability
11. **Estimate Effort** - Provide t-shirt sizing (XS/S/M/L/XL) and map story dependencies (calibrated using historical PR analysis when available)
12. **Define Outcomes** - Specify the measurable outcomes and value each story delivers
13. **Generate Implementation Summary** - Aggregate effort, dependencies, and risks across all epics

For detailed implementation, see:
- `plugins/jira/skills/analyze-rfe/SKILL.md`

## Arguments

- **$1 – rfe-key** *(required)*
  Jira issue key for the RFE (e.g., `RFE-1234`).
  Can also accept a full Jira URL; the key will be extracted automatically.

## Return Value

- **Comprehensive Markdown Report** including:
  - RFE Summary
  - Related Work (Jira search results)
  - Component Context (from workspace, if available)
  - EPIC(s) with objective, scope, acceptance criteria, complexity, risks, dependencies
  - User stories (functional + NFR) with acceptance criteria, effort estimates, dependencies
  - Implementation summary with effort overview and risk aggregation
  - Outcomes mapping (what each story delivers)
- **Optional**: Output can be saved to `.work/jira/analyze-rfe/<rfe-key>/breakdown.md`

## Output Format

```markdown
# RFE Analysis: [RFE-KEY] - [Title]

## RFE Summary
- **Source**: [link]
- **Key Capability**: ...
- **Business Driver**: ...
- **Affected Components**: ...

## Related Work
| Issue | Relationship | Recommendation |
|-------|--------------|----------------|
| [KEY-123] - [Title] | Duplicate/Overlap | Coordinate with |

**Reuse Opportunities**: [Libraries/components to leverage]

## Component Context (from workspace)
*[If context.md found - basic component purpose and scope]*

## Comprehensive Component Context
*[If repository analysis performed - deep technical understanding]*

### Component: [component-name]

**Repositories**:
- Downstream: openshift/{repo}
- Upstream: {org}/{upstream-repo}
- Related: {related repos}

**What it does**: {concise description}
**Why it exists**: {purpose and value}
**How it works**:
- Architecture: {pattern (e.g., Kubernetes Operator)}
- Key packages: {important code areas}
- Integration: {external systems}

**Key Implementation Patterns**:
1. {Pattern}: {description}

**Historical Context**:
- PR #{number} ({date}): {key design decision or lesson}
- ADR: {architecture decision reference}
- Lesson from Issue #{number}: {anti-pattern to avoid}

**Risk Factors**:
- {Risk type}: {description and mitigation}

**Recommended Approach for RFE**:
- {Guidance based on component analysis}
- Reuse: {reference to specific PR or code to leverage}
- Follow: {design principles to respect}
- Avoid: {pitfalls from historical analysis}

## EPIC(s)

### EPIC 1: [Epic Title]
**Objective**: ...
**Scope**: ...
**Acceptance Criteria**: ...
**Technical Complexity**: High/Medium/Low - [justification]
**Key Risks**:
- [Risk 1]
- [Risk 2]
**Blockers/Unknowns**: [Items requiring resolution]
**Tech Debt Impact**: Positive/Neutral/Negative - [explanation]
**Dependencies**: [Epic/external dependencies]
**Integration Points**: [External systems]
**Critical Path**: Yes/No

## User Stories

### Epic 1 → Story 1.1: [Title]
**As a** [role], **I want** [action], **so that** [value].
**Acceptance Criteria**: ...
**Outcome**: ...
**Effort**: M
**Confidence**: High
**Depends On**: None

### Epic 1 → Story 1.N: [NFR Title - Performance]
**As an** SRE, **I want** [capability], **so that** [operational value].
**Acceptance Criteria**: [Measurable criteria]
**Outcome**: ...
**Effort**: S
**Depends On**: Story 1.1, 1.2

## Implementation Summary

### Effort Overview
| Epic | Stories | Total Effort |
|------|---------|--------------|
| Epic 1 | 5 (3 feature + 2 NFR) | ~15-20 days |

### Critical Dependencies
- [Blocking items]

### Key Risks
1. [Highest priority risk]
2. [Second priority risk]

## Outcomes Summary
| Story | Outcome | Effort |
|-------|---------|--------|
| 1.1 | [Outcome] | M |

---
*Generated by `/jira:analyze-rfe` on [timestamp]*

## Next Steps
1. Review with product/engineering teams
2. Use `/jira:create epic` and `/jira:create story` to create in Jira
3. Schedule spikes for unknowns
```

## Examples

### Basic Usage

Analyze an RFE and generate the breakdown:
```
/jira:analyze-rfe RFE-1234
```

### With URL

The command accepts Jira URLs:
```
/jira:analyze-rfe https://issues.redhat.com/browse/RFE-1234
```

## Error Handling

- **Issue Not Found**: Verify RFE key and Jira permissions
- **Not an RFE**: If the issue is not from the RFE project or not a Feature Request type, warn the user but proceed with analysis
- **Sparse RFE**: If the RFE lacks sufficient detail, indicate gaps and suggest what information would improve the breakdown

## Prerequisites

- MCP Jira server configured and accessible
- Network access to Jira (e.g., https://issues.redhat.com)
- Read permissions for the RFE project

## See Also

- `jira:create` - Create epics and stories from the generated breakdown
- `jira:create feature-request RFE` - Create new RFEs
- `jira:generate-feature-doc` - Generate documentation for implemented features
