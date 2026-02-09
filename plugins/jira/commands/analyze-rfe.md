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

The `jira:analyze-rfe` command analyzes a Request for Enhancement (RFE) from Jira and generates a structured breakdown of Epics, user stories, and their outcomes. This helps product and engineering teams transform customer-driven RFEs into actionable implementation plans.

This command is particularly useful for:
- Breaking down complex RFEs into implementable work items
- Planning sprints and releases from customer requests
- Creating epics and stories that align with RFE scope
- Understanding the full scope and outcomes of an RFE before implementation
- Preparing for refinement or planning sessions

The command performs deep analysis of:
- The RFE's nature and description
- Current limitations and desired behavior
- Business requirements and use cases
- Affected packages and components
- **Workspace context** (optional): When the workspace contains `context.md` files (e.g., `docs/component-context/context.md`), the command loads component Purpose, Scope, and Key Areas to enrich the breakdown.

## Implementation

This command invokes the `analyze-rfe` skill to:

1. **Fetch RFE** - Retrieve the RFE from Jira via MCP
2. **Parse Structure** - Extract nature, description, business requirements, affected components
3. **Gather Workspace Context** - Search for `context.md` files in the workspace (e.g., `docs/component-context/context.md`). When components match the RFE, load Purpose, Scope, Key Areas, and use them to enrich epics and stories.
4. **Generate EPIC(s)** - Break down the RFE into one or more epics with scope and acceptance criteria
5. **Generate User Stories** - Create user stories for each epic in proper "As a... I want... So that..." format
6. **Define Outcomes** - Specify the measurable outcomes and value each story delivers

For detailed implementation, see:
- `plugins/jira/skills/analyze-rfe/SKILL.md`

## Arguments

- **$1 – rfe-key** *(required)*
  Jira issue key for the RFE (e.g., `RFE-1234`).
  Can also accept a full Jira URL; the key will be extracted automatically.

## Return Value

- **Structured Markdown Report** including:
  - RFE Summary
  - EPIC(s) with objective, scope, acceptance criteria
  - User stories with acceptance criteria
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

## EPIC(s)

### EPIC 1: [Epic Title]
**Objective**: ...
**Scope**: ...
**Acceptance Criteria**:
- ...

## User Stories

### Epic 1 → Story 1
**As a** [role], **I want** [action], **so that** [value].
**Acceptance Criteria**: ...
**Outcome**: ...

### Epic 1 → Story 2
...
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
