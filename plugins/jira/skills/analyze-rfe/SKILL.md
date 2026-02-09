---
name: Analyze RFE
description: Implementation guide for analyzing RFEs and generating EPIC, user stories, and outcomes breakdown
---

# Analyze RFE

This skill provides implementation guidance for the `/jira:analyze-rfe` command, which analyzes Request for Enhancement (RFE) issues and generates a structured breakdown of Epics, user stories, and their outcomes.

**IMPORTANT FOR AI**: When invoked, execute the implementation steps below. Load the `create-epic`, `create-story`, and `create-feature-request` skills for reference on EPIC/story structure and RFE conventions.

## When to Use This Skill

This skill is automatically invoked by the `/jira:analyze-rfe` command and should not be called directly by users.

## Prerequisites

- **MCP Jira server configured** (required - see `plugins/jira/README.md`)
- Read access to the RFE project
- User provides an RFE key (e.g., RFE-1234) or Jira URL

## RFE Structure Reference

RFEs typically contain these sections (Jira Wiki markup):

- **Nature and Description** - What is being requested
- **Current Limitation** - What doesn't work today
- **Desired Behavior** - What should happen
- **Use Case** - How customers will use this
- **Business Requirements** - Customer impact, regulatory drivers, justification
- **Affected Packages and Components** - Teams, operators, technical components

## Implementation Steps

### Step 1: Fetch the RFE

**Objective**: Retrieve the RFE from Jira.

**Actions**:

1. **Parse input**: Extract issue key from user input
   - If URL provided (e.g., `https://issues.redhat.com/browse/RFE-1234`), extract `RFE-1234`
   - If key provided directly (e.g., `RFE-1234`), use as-is
   - Validate format: `RFE-\d+` or `[A-Z]+-\d+` (accept non-RFE project for flexibility)

2. **Fetch issue** via MCP:
   ```
   mcp__atlassian__jira_get_issue(issue_key=<rfe-key>, fields="*all")
   ```

3. **Handle errors**:
   - If 404/403: Display error, suggest verifying key and permissions
   - If MCP unavailable: Point to Jira plugin README for setup

4. **Display progress**: Show RFE title and link

### Step 2: Parse and Extract RFE Content

**Objective**: Extract structured information from the RFE description.

**Actions**:

1. **Parse description** - Strip Jira Wiki markup, extract:
   - **Nature/Description**: Main capability being requested
   - **Current Limitation**: Gaps or problems today
   - **Desired Behavior**: Bullet points or paragraphs of desired functionality
   - **Use Case**: How customers will use this
   - **Business Requirements**: Customer impact, regulatory drivers, justification
   - **Affected Components**: Teams, operators, technical areas

2. **Handle sparse RFEs**: If sections are missing or minimal:
   - Note the gaps in the output
   - Proceed with available information
   - Suggest what additional detail would improve the breakdown

3. **Detect scope signals**:
   - Single capability vs. multiple distinct capabilities → influences number of epics
   - Cross-team components → may warrant multiple epics
   - Phased delivery (MVP vs. advanced) → may warrant epic ordering

### Step 2.5: Gather Workspace Context (Optional)

**Objective**: Enrich analysis with component context from the workspace.

**Actions**:

1. **Search for context.md files** in the workspace:
   - Search for `**/context.md` or `**/component-context/**/context.md`
   - Use available file search (glob, grep, or list_dir) to locate `context.md` files

2. **Match components**: For each component mentioned in the RFE (from Jira Component field or "Affected Packages and Components"):
   - Normalize name (e.g., cert-manager-operator, cert-manager, hypershift)
   - Check if any context.md mentions this component in Component Identity, Aliases, or RFE Mapping Hints

3. **Load matching context.md**:
   - Read the full content of each matching file
   - Extract: Purpose, Scope, Out of Scope, Key Technical Areas, RFE Mapping Hints, Related Components

4. **Use context when generating**:
   - **Epic scope**: Respect Out of Scope from context; use Related Components for handoffs
   - **Story placement**: Map stories to Key Technical Areas where applicable
   - **Component assignment**: Use Jira Component from context for suggested assignment
   - **Outcomes**: Align with Purpose and target users from context

5. **Add to output**: If context was loaded, add a "Component Context (from workspace)" section:
   ```markdown
   ## Component Context (from workspace)
   [Component name]: [1-2 line summary from Purpose]
   - Scope: [key scope items]
   - Key areas: [paths/packages]
   ```

6. **Fallback**: If no context.md found or no matches, proceed without workspace context. This is optional enrichment.

### Step 3: Generate EPIC(s)

**Objective**: Break down the RFE into one or more epics.

**Epic Criteria** (from create-epic skill):
- **Scope**: Broader than a story, narrower than a feature
- **Timebox**: Fits in a quarter/release (2-8 sprints)
- **Acceptance Criteria**: High-level outcomes, not implementation details

**Actions**:

1. **Determine epic count**:
   - Single cohesive capability → 1 epic
   - Multiple distinct capabilities (e.g., API + UI + CLI) → 2-3 epics
   - Phased delivery (MVP + enhancements) → 2 epics with dependency

2. **For each epic, generate**:
   - **Summary/Title**: Clear, action-oriented (e.g., "Enable custom configuration for ProductA API endpoints")
   - **Objective**: What capability will be delivered, who benefits
   - **Scope (In/Out)**: What's included and excluded
   - **Epic Acceptance Criteria**: 3-6 high-level outcomes (measurable, user-observable)
   - **Target Users**: Who benefits

3. **Align with RFE**: Ensure each epic maps to RFE's desired behavior and use case

### Step 4: Generate User Stories

**Objective**: Create user stories for each epic.

**Story Format** (from create-story skill):
```
As a <role>, I want to <action>, so that <value>.
```

**Actions**:

1. **For each epic, identify story candidates**:
   - One story per distinct user-facing capability
   - Stories should be completable in one sprint
   - Map to RFE's "Desired Behavior" bullets where possible

2. **For each story, generate**:
   - **User story** (full "As a... I want... So that..." in description)
   - **Summary** (concise 5-10 word title for Jira)
   - **Acceptance Criteria**: 2-6 testable criteria (test-based, verification-based, or BDD format)
   - **Outcome**: What value this story delivers (business/customer benefit)

3. **Story quality checks**:
   - User-focused (not technical implementation)
   - Specific and actionable
   - Right-sized (one sprint)

### Step 5: Define Outcomes

**Objective**: Explicitly state the outcome/value of each story.

**Outcome Format**:
- **Customer outcome**: What the customer can now do
- **Business outcome**: Impact on adoption, compliance, deals, etc.
- **Measurable**: Where possible (e.g., "reduce manual steps from 5 to 1")

**Actions**:

1. **For each story**, write 1-2 sentence outcome
2. **Link to RFE**: Reference the business requirement or use case this addresses
3. **Aggregate**: Provide epic-level outcomes summarizing story outcomes

### Step 6: Output the Report

**Objective**: Present the structured breakdown.

**Actions**:

1. **Format as Markdown** using the structure in the command file

2. **Optional**: Save to `.work/jira/analyze-rfe/<rfe-key>/breakdown.md`
   - Create directory with `mkdir -p`
   - Add footer: `*Generated by /jira:analyze-rfe on <timestamp>*`

3. **Display to user**:
   - Full markdown report in response
   - Summary statistics (epics count, stories count)
   - Note: "Use `/jira:create epic` and `/jira:create story` to create these in Jira"

## Output Structure Template

```markdown
# RFE Analysis: [KEY] - [Title]

## RFE Summary
| Field | Value |
|-------|-------|
| **Source** | [Jira link] |
| **Key Capability** | One-line summary |
| **Business Driver** | Why this matters |
| **Affected Components** | Teams, operators |

## Component Context (from workspace)
*[If context.md files found - otherwise omit]*
| Component | Purpose | Key Areas |
|-----------|---------|-----------|
| [name] | [from context.md] | [paths] |

## EPIC(s)

### EPIC 1: [Epic Title]
**Objective**: [What capability is delivered]
**Scope**: In scope / Out of scope
**Acceptance Criteria**:
- [Outcome 1]
- [Outcome 2]
- [Outcome 3]
**Target Users**: [Who benefits]

---

## User Stories

### Epic 1 → Story 1.1: [Concise Title]
**User Story**: As a [role], I want to [action], so that [value].
**Acceptance Criteria**:
- Test that [criteria 1]
- Verify that [criteria 2]
**Outcome**: [What value this delivers]

### Epic 1 → Story 1.2: [Concise Title]
...

---

## Outcomes Summary
| Story | Outcome |
|-------|---------|
| 1.1 | [Outcome] |
| 1.2 | [Outcome] |

---
*Generated by `/jira:analyze-rfe` on [timestamp]*
```

## Error Handling

**Issue Not Found** (404, 403):
- Display error with verification steps
- Suggest: Check issue key, Jira permissions, MCP configuration

**Not RFE Project**:
- Warn: "Issue is not from RFE project. Proceeding with analysis."
- Continue (user may have linked a related issue)

**Sparse RFE** (minimal description):
- Note: "RFE has limited detail. Consider enriching with: [suggested sections]"
- Generate best-effort breakdown from available content

**MCP Unavailable**:
- Display setup instructions from `plugins/jira/README.md`

## Best Practices for AI Implementation

1. **Synthesize, don't copy**: Transform RFE content into proper agile artifacts
2. **Right-size**: Epics = quarter scope, Stories = sprint scope
3. **Outcome-focused**: Every story should have a clear customer/business outcome
4. **Reference conventions**: Use create-epic and create-story skill formats
5. **Link to source**: When generating stories, reference which RFE bullet they address

## Example Workflow

```
User runs: /jira:analyze-rfe RFE-5678

1. Fetch RFE-5678 via MCP
2. Parse: "Support custom SSL certificates for ProductA managed control planes"
   - Desired: Upload, validate, rotate certs
   - Use case: Enterprise compliance (SOC2, ISO)
   - Components: HyperShift, OCM, Networking

3. Generate EPIC:
   - "Custom SSL certificate management for ProductA control planes"
   - AC: Upload during creation, rotate post-creation, validation, alerts

4. Generate Stories:
   - Story 1: As cluster admin, I want to upload custom cert during creation...
   - Story 2: As cluster admin, I want to rotate cert without downtime...
   - Story 3: As cluster admin, I want validation before cluster goes active...

5. Outcomes:
   - Story 1 → Enables compliance-driven deployments
   - Story 2 → Reduces operational risk
   - Story 3 → Prevents misconfiguration

6. Output markdown report
```

## See Also

- `create-feature-request` skill - RFE structure and conventions
- `create-epic` skill - Epic format and acceptance criteria
- `create-story` skill - User story format and acceptance criteria
- `/jira:create` - Create the generated epics and stories in Jira
