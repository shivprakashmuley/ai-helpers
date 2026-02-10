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

### Step 3.5: Assess Technical Complexity and Risks

**Objective**: Analyze technical feasibility, complexity, and risks for each epic.

**Actions**:

1. **Analyze technical complexity** for each epic:
   - **Component familiarity**: New technology/framework vs. well-known codebase
   - **Integration scope**: Number of external APIs, databases, services involved
   - **Code impact**: New packages/modules vs. changes to existing code
   - **Team expertise**: Does team have prior experience with this domain?

2. **Identify risks and blockers**:
   - **High risk signals**:
     - New technology stack or unfamiliar frameworks
     - Complex distributed system integrations
     - Performance-sensitive changes (latency, throughput SLOs)
     - Breaking changes requiring migration
     - Security/compliance implications
   - **Medium risk signals**:
     - Cross-team dependencies
     - Significant refactoring of existing code
     - API contract changes requiring coordination
   - **Low risk signals**:
     - Isolated feature additions
     - Well-understood patterns and technologies
     - Single-team ownership

3. **Flag unknowns and research needs**:
   - Architecture decisions requiring spikes
   - Technology evaluation needed
   - External dependency availability/stability
   - Data migration complexity

4. **Assess technical debt impact**:
   - Does this RFE reduce existing tech debt? (refactoring, modernization)
   - Does it introduce new tech debt? (shortcuts, workarounds)
   - Opportunity to clean up related code?

5. **Add to epic output**:
   - **Technical Complexity**: High/Medium/Low with brief justification
   - **Key Risks**: 2-5 bullet points of significant risks
   - **Blockers/Unknowns**: Items requiring resolution before implementation
   - **Tech Debt Impact**: Positive/Neutral/Negative with explanation

### Step 3.6: Map Cross-Component Dependencies

**Objective**: Identify dependencies between epics, stories, and external components.

**Actions**:

1. **Identify epic-level dependencies**:
   - Which epics must be completed before others can start?
   - Which epics can proceed in parallel?
   - Are there external team deliverables required? (APIs, libraries, infrastructure)

2. **Map integration points**:
   - External APIs or services (REST, gRPC, message queues)
   - Shared databases or data stores
   - Authentication/authorization services
   - Configuration management systems
   - CI/CD pipeline changes

3. **Identify cross-team handoffs**:
   - Which teams own dependent components?
   - Are there API contracts to negotiate?
   - Shared library or framework updates needed?

4. **Add to epic output**:
   - **Dependencies**: List of epics, external deliverables, or team dependencies
   - **Integration Points**: External systems this epic interacts with
   - **Critical Path**: Note if epic is on critical path for RFE delivery

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

### Step 4.5: Add Non-Functional Requirement (NFR) Stories

**Objective**: Ensure production-readiness by identifying NFR stories.

**Actions**:

1. **Analyze performance requirements**:
   - Latency targets (API response times, UI render times)
   - Throughput expectations (requests/sec, events/sec)
   - Resource constraints (CPU, memory, storage limits)
   - Add story if needed: "As an SRE, I want performance SLOs defined and monitored..."

2. **Analyze security requirements**:
   - Authentication/authorization changes
   - Data encryption (at rest, in transit)
   - Compliance requirements (GDPR, SOC2, HIPAA)
   - Audit logging needs
   - Add story if needed: "As a security admin, I want audit logs for all configuration changes..."

3. **Analyze scalability requirements**:
   - Expected load growth
   - Horizontal/vertical scaling capabilities
   - Database sharding or partitioning needs
   - Add story if needed: "As a platform engineer, I want auto-scaling based on load metrics..."

4. **Analyze observability requirements**:
   - Metrics to expose (Prometheus, custom metrics)
   - Logging requirements (structured logs, log levels)
   - Alerting rules (SLO violations, error rates)
   - Dashboards (Grafana, custom UI)
   - Add story if needed: "As an SRE, I want Grafana dashboards for key performance metrics..."

5. **NFR story format**:
   - Use same user story format
   - Typical personas: SRE, Security Admin, Platform Engineer, Operator
   - Make acceptance criteria measurable (e.g., "p95 latency < 200ms")

6. **Add NFR stories to epic**: Group NFR stories at the end of each epic's story list

### Step 4.6: Estimate Story Effort

**Objective**: Provide t-shirt sizing to support sprint planning.

**Actions**:

1. **Estimate each story** using these criteria:
   - **Extra Small (XS)**:
     - 1-2 hours of work
     - Single file change, minimal testing
     - Example: Configuration change, simple UI text update
   - **Small (S)**:
     - 2-4 hours of work
     - 1-3 files changed, unit tests
     - Example: Add new API parameter, simple validation logic
   - **Medium (M)**:
     - 1-2 days of work
     - 3-10 files changed, unit + integration tests
     - Example: New API endpoint, UI component with state management
   - **Large (L)**:
     - 3-5 days of work
     - 10+ files, complex testing, possible data migration
     - Example: New service integration, complex business logic
   - **Extra Large (XL)**:
     - > 1 week of work
     - Many files, cross-component changes, extensive testing
     - **Flag for splitting**: XL stories should be broken down further

2. **Consider complexity factors**:
   - Number of components/files touched
   - Integration points (APIs, databases, external services)
   - Testing complexity (mocking, test data, e2e scenarios)
   - Unknown/research required (reduce confidence, increase estimate)
   - Team familiarity with codebase/technology

3. **Map dependencies between stories**:
   - Story A must complete before Story B can start
   - Note in output: "Story 1.2 depends on Story 1.1"

4. **Add to story output**:
   - **Effort**: XS/S/M/L/XL
   - **Depends On**: List of story IDs if applicable
   - **Confidence**: High/Medium/Low (based on unknowns)

5. **Flag oversized stories**:
   - Any story > L should have note: "Consider splitting this story"
   - Suggest potential split points

### Step 4.7: Discover Related Work

**Objective**: Find related RFEs, epics, bugs to prevent duplication and leverage existing work.

**Actions**:

1. **Search Jira for related issues**:
   - Use MCP `jira_search` with keywords from RFE title and affected components
   - Search for:
     - Related RFEs: `project = RFE AND text ~ "<keyword>"`
     - Related epics: `issuetype = Epic AND text ~ "<keyword>"`
     - Related bugs: `issuetype = Bug AND status != Closed AND text ~ "<keyword>"`
     - Same component: `component = "<component-name>" AND created >= -6M`

2. **Analyze related issues** (limit to 5-10 most relevant):
   - Duplicate work? (exact same capability requested)
   - Overlapping scope? (partial overlap, coordination needed)
   - Related implementation? (similar code areas, potential reuse)
   - Historical context? (prior attempts, lessons learned)

3. **Identify reuse opportunities**:
   - Existing libraries or utilities to leverage
   - Similar UI components or patterns
   - Test infrastructure or test data
   - Documentation or runbooks

4. **Add to output**:
   - **Related Work** section with:
     - Issue key, title, relationship (duplicate/overlap/related/historical)
     - Recommendation (block on, coordinate with, reference, leverage)
   - **Reuse Opportunities**: List of code/tests/docs to leverage

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

## Related Work
*[Based on Jira search - omit if no relevant issues found]*
| Issue | Relationship | Recommendation |
|-------|--------------|----------------|
| [KEY-123] - [Title] | Duplicate/Overlap/Related | Block on / Coordinate with / Reference |

**Reuse Opportunities**:
- [Component/Library/Test to leverage]

---

## EPIC(s)

### EPIC 1: [Epic Title]
**Objective**: [What capability is delivered]
**Scope**: In scope / Out of scope
**Acceptance Criteria**:
- [Outcome 1]
- [Outcome 2]
- [Outcome 3]
**Target Users**: [Who benefits]

**Technical Complexity**: High/Medium/Low
- [Justification: new tech, complex integration, etc.]

**Key Risks**:
- [Risk 1: e.g., Breaking API changes require coordination]
- [Risk 2: e.g., Performance impact on existing workloads]

**Blockers/Unknowns**:
- [Item requiring resolution: e.g., Architecture decision on data model]

**Tech Debt Impact**: Positive/Neutral/Negative
- [Explanation: e.g., Reduces tech debt by replacing legacy auth system]

**Dependencies**:
- [Epic/External dependency: e.g., Requires API from Team B (Epic 2.1)]

**Integration Points**:
- [External system: e.g., Auth service (OAuth2), Metrics service (Prometheus)]

**Critical Path**: Yes/No
- [Explanation if yes: e.g., Blocks all downstream features]

---

## User Stories

### Epic 1 → Story 1.1: [Concise Title]
**User Story**: As a [role], I want to [action], so that [value].
**Acceptance Criteria**:
- Test that [criteria 1]
- Verify that [criteria 2]
**Outcome**: [What value this delivers]
**Effort**: S/M/L (estimate)
**Confidence**: High/Medium/Low
**Depends On**: [Story ID if applicable, or "None"]

### Epic 1 → Story 1.2: [Concise Title]
...

### Epic 1 → Story 1.N: [NFR Title - Performance]
**User Story**: As an SRE, I want [capability], so that [operational value].
**Acceptance Criteria**:
- [Measurable criteria: e.g., p95 latency < 200ms]
**Outcome**: [What value this delivers]
**Effort**: M (estimate)
**Confidence**: Medium
**Depends On**: Story 1.1, Story 1.2

---

## Implementation Summary

### Effort Overview
| Epic | Stories | Total Effort (story points estimated) |
|------|---------|---------------------------------------|
| Epic 1 | 5 stories (3 feature + 2 NFR) | ~15-20 days (3-4 sprints) |

### Critical Dependencies
- [List of blocking items across epics]

### Key Risks Across All Epics
1. [Highest priority risk]
2. [Second priority risk]

---

## Outcomes Summary
| Story | Outcome | Effort |
|-------|---------|--------|
| 1.1 | [Outcome] | S |
| 1.2 | [Outcome] | M |
| 1.N (NFR) | [Operational outcome] | M |

---
*Generated by `/jira:analyze-rfe` on [timestamp]*

## Next Steps
1. Review with product/engineering teams
2. Refine estimates and dependencies
3. Use `/jira:create epic` and `/jira:create story` to create issues in Jira
4. Schedule technical spike for: [List unknowns requiring research]
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
6. **Be realistic about complexity**: Don't downplay risks or unknowns; flag them explicitly
7. **Include NFRs proactively**: Don't wait for SRE/security teams to ask; generate NFR stories upfront
8. **Estimate conservatively**: When in doubt, size larger; teams can adjust down
9. **Map dependencies explicitly**: Clear dependency graphs prevent planning surprises
10. **Search thoroughly for related work**: Spend time on Jira search to prevent duplicate effort
11. **Flag XL stories immediately**: Stories > 1 week should be broken down before planning
12. **Make risks measurable**: Quantify impact when possible (e.g., "affects 50K clusters", "3 external API integrations")

## Example Workflow

```
User runs: /jira:analyze-rfe RFE-5678

1. Fetch RFE-5678 via MCP
2. Parse: "Support custom SSL certificates for ProductA managed control planes"
   - Desired: Upload, validate, rotate certs
   - Use case: Enterprise compliance (SOC2, ISO)
   - Components: HyperShift, OCM, Networking

3. Search for related work:
   - Find RFE-3456 (TLS cert rotation) - Related, can reuse rotation logic
   - Find EPIC-890 (Certificate management) - Overlapping, coordinate with Team B

4. Generate EPIC:
   - "Custom SSL certificate management for ProductA control planes"
   - AC: Upload during creation, rotate post-creation, validation, alerts
   - Complexity: High (new cert validation library, API changes)
   - Risks: Breaking change to cluster creation API, migration for existing clusters
   - Dependencies: Requires cert-manager operator from Platform team
   - Integration: Vault (cert storage), Kubernetes secrets, control plane API

5. Generate Stories:
   - Story 1: As cluster admin, I want to upload custom cert during creation...
     - Effort: L (API changes, validation, tests)
     - Depends on: None
   - Story 2: As cluster admin, I want to rotate cert without downtime...
     - Effort: M (reuse logic from RFE-3456)
     - Depends on: Story 1
   - Story 3: As cluster admin, I want validation before cluster goes active...
     - Effort: S (validation library integration)
     - Depends on: Story 1
   - Story 4 (NFR): As an SRE, I want alerts when cert expiry < 30 days...
     - Effort: S (Prometheus alerts)
     - Depends on: Story 2

6. Outcomes:
   - Story 1 → Enables compliance-driven deployments
   - Story 2 → Reduces operational risk
   - Story 3 → Prevents misconfiguration
   - Story 4 → Prevents cert expiration incidents

7. Implementation Summary:
   - Total effort: ~12-15 days (2-3 sprints)
   - Critical path: Story 1 blocks Stories 2, 3, 4
   - Key risk: API contract negotiation with consuming teams

8. Output markdown report with all analysis
```

## See Also

- `create-feature-request` skill - RFE structure and conventions
- `create-epic` skill - Epic format and acceptance criteria
- `create-story` skill - User story format and acceptance criteria
- `/jira:create` - Create the generated epics and stories in Jira
