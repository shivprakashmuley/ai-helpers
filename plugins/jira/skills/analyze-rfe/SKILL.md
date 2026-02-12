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

### Required Environment Setup

Before running this skill, the user must have:

1. **Jira Personal Access Token** configured:
   ```bash
   export JIRA_PERSONAL_TOKEN="your_token_here"
   export JIRA_URL="https://issues.redhat.com"  # Optional
   ```

   Get token from: https://issues.redhat.com/secure/ViewProfile.jspa?selectedTab=com.atlassian.pats.pats-plugin:jira-user-personal-access-tokens

2. **Python Dependencies** installed:
   ```bash
   pip install requests aiohttp
   ```

3. **Jira Permissions**:
   - Read access to RFE project
   - Read access to OCPBUGS project (for related work)
   - Read access to component-specific projects

4. **User Input**:
   - RFE key (e.g., RFE-1234) or Jira URL

### Verification

Test the setup with:
```bash
curl -H "Authorization: Bearer $JIRA_PERSONAL_TOKEN" \
     "https://issues.redhat.com/rest/api/2/myself"
```

If this returns your user profile, you're ready to run analyze-rfe.

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

2. **Fetch issue** via Jira REST API:
   ```bash
   GET /rest/api/2/issue/{issue-key}?fields=summary,description,components,labels,status,created,updated,reporter,assignee,issuelinks,customfield_*
   ```

   Use the Jira REST client (see `plugins/jira/skills/analyze-rfe/scripts/fetch_rfe.py`):
   ```python
   import os
   import requests

   jira_url = os.getenv("JIRA_URL", "https://issues.redhat.com")
   token = os.getenv("JIRA_PERSONAL_TOKEN")

   response = requests.get(
       f"{jira_url}/rest/api/2/issue/{issue_key}",
       headers={
           "Authorization": f"Bearer {token}",
           "Accept": "application/json"
       },
       params={
           "fields": "summary,description,components,labels,status,created,updated,reporter,assignee,issuelinks,customfield_12316840,customfield_12319940"
       },
       timeout=30
   )

   rfe_data = response.json()
   ```

3. **Handle errors**:
   - If 401: Display "Authentication failed. Check JIRA_PERSONAL_TOKEN environment variable"
   - If 404: Display "Issue {issue_key} not found. Verify the key and your permissions"
   - If 403: Display "Access denied. You need read permission for the RFE project"
   - If JIRA_PERSONAL_TOKEN not set: Display setup instructions

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

### Step 2.7: Comprehensive Component Context

**Objective**: Gather deep understanding of component architecture, implementation patterns, and historical decisions by analyzing repositories, code, and PR history.

**When to Execute**: Always attempt this step for affected components. If repositories cannot be found or GitHub API is unavailable, gracefully degrade and proceed with available information.

**Actions**:

#### 2.7.1: Discover Repositories

For each affected component:

1. **Check workspace context.md for repository hints**:
   - If context.md exists (from Step 2.5), check for repository URLs
   - Extract downstream and upstream repo references

2. **Search OpenShift GitHub organization** using gh CLI:
   ```bash
   # Check if repo exists (common patterns)
   gh repo view openshift/{component-name} --json name,url,description
   gh repo view openshift/{component-name}-operator --json name,url,description
   gh repo view openshift/cluster-{component-name}-operator --json name,url,description
   ```

3. **Extract upstream reference** from downstream README:
   ```bash
   # Get README to find upstream project
   gh repo view openshift/{component-name} --json readme
   # Look for "upstream:", "based on:", or links to upstream projects
   ```

4. **Search for related components**:
   ```bash
   # Find related repos by keyword
   gh search repos --owner openshift "{component-keyword}" --json name,description,url --limit 10
   ```

5. **Output repository mapping**:
   ```yaml
   Component: {component-name}
   Repositories:
     Downstream: openshift/{repo-name}
     Upstream: {org}/{upstream-repo}
     Related: [list of related repos]
   ```

#### 2.7.2: Analyze Codebase Structure

**For downstream repository** (prioritize this over upstream):

1. **Detect architecture pattern**:
   - Check for `config/crd/` → Kubernetes Operator
   - Check for `cmd/` + `main.go` → CLI tool / Binary
   - Check for `pkg/` only → Library
   - Check `Dockerfile` → Containerized service
   - Check `go.mod` for `operator-sdk` → Operator SDK based

2. **Map key packages** (for Go projects):
   ```bash
   # Use gh API to browse repository structure
   gh api repos/openshift/{repo}/contents/pkg --jq '.[] | {name, path, type}'

   # Identify key directories
   gh api repos/openshift/{repo}/contents/pkg/controllers --jq '.[] | .name'
   gh api repos/openshift/{repo}/contents/api --jq '.[] | .name'
   ```

3. **Extract API types** (for Kubernetes operators):
   ```bash
   # List CRDs
   gh api repos/openshift/{repo}/contents/config/crd/bases --jq '.[] | .name'

   # Download a sample CRD to understand API
   gh api repos/openshift/{repo}/contents/config/crd/bases/{crd-file}.yaml --raw
   ```
   - Parse CRD to extract: kind, group, version, key spec fields

4. **Identify controllers**:
   - Search for files matching `*controller.go` or `*reconciler.go`
   - Note controller names and responsibilities

5. **Output structure analysis**:
   ```markdown
   **Architecture**: Kubernetes Operator (controller-runtime)
   **Key Packages**:
   - pkg/controllers/{name}: {inferred purpose}
   - pkg/api/v1: API type definitions
   **API Types**:
   - {Kind}: {brief description from CRD}
   ```

#### 2.7.3: Understand Implementation Logic

**Analyze reconciliation patterns** (for operators):

1. **Search for Reconcile function**:
   ```bash
   # Use Grep to find reconciliation logic
   gh search code --repo openshift/{repo} "func.*Reconcile.*Context"
   ```

2. **Identify integration patterns**:
   - Search for client initialization: `kubernetes.NewForConfig`, `dynamic.NewForConfig`
   - Check `go.mod` for key dependencies (client-go, AWS SDK, Prometheus client, etc.)
   - Note external systems the component integrates with

3. **Identify error handling patterns**:
   - Search for error handling patterns in reconciliation code
   - Note retry logic, exponential backoff, circuit breakers

4. **Output implementation summary**:
   ```markdown
   **Implementation Pattern**: Controller reconciliation loop
   **Integration Points**:
   - Kubernetes API (via client-go)
   - {External service}: {purpose}
   **Key Patterns**:
   - {Pattern identified}: {description}
   ```

#### 2.7.4: Gather Historical Context

**Search for relevant PRs to understand design decisions**:

1. **Extract keywords from RFE**:
   - Use RFE title, nature, desired behavior to create search keywords
   - Example: "certificate rotation", "custom configuration", "ACME"

2. **Search merged PRs**:
   ```bash
   # Search by keywords
   gh search prs \
     --repo openshift/{repo} \
     --state merged \
     --sort updated \
     --limit 10 \
     "{keyword1} {keyword2}" \
     --json number,title,url,body,mergedAt
   ```

3. **Rank PRs by relevance**:
   - Score PRs based on keyword matches in title (high weight) and body (medium weight)
   - Prioritize recent PRs (merged in last 6-12 months)
   - Select top 5 most relevant PRs for deep analysis

4. **Analyze PR discussions** (for top 3-5 PRs):
   ```bash
   # Get PR details with comments and reviews
   gh pr view {pr-number} \
     --repo openshift/{repo} \
     --json number,title,body,comments,reviews
   ```

   Extract from PR body and comments:
   - Design sections: "## Design", "## Architecture", "## Approach", "## Rationale"
   - Trade-off discussions: Comments mentioning "why", "alternative", "trade-off"
   - Lessons learned: References to previous issues or bugs

5. **Search for Architecture Decision Records (ADRs)**:
   ```bash
   # Check common ADR locations
   gh api repos/openshift/{repo}/contents/docs/adr --jq '.[] | {name, path}'
   gh api repos/openshift/{repo}/contents/docs/design --jq '.[] | {name, path}'
   ```
   - If ADRs exist, download and parse key decisions

6. **Search for related issues/bugs with lessons**:
   ```bash
   # Search for closed bugs with learning opportunities
   gh search issues \
     --repo openshift/{repo} \
     "learned OR mistake OR lesson OR regression" \
     --state closed \
     --limit 5 \
     --json number,title,body,labels
   ```

7. **Output historical context**:
   ```markdown
   **Relevant PRs**:
   - #{pr-number}: {title}
     - **Design**: {key design decision}
     - **Why**: {rationale from discussion}
     - **Lesson**: {what was learned}

   **Architecture Decisions**:
   - {ADR title}: {decision summary}

   **Lessons Learned**:
   - Issue #{number}: {lesson extracted}
   ```

#### 2.7.5: Synthesize Insights

**Combine all gathered context into actionable guidance**:

1. **Generate component summary**:
   - **What it does**: Based on README, CRDs, package structure
   - **Why it exists**: Based on project description and use cases
   - **How it works**: Based on architecture pattern and reconciliation flow

2. **Extract key implementation patterns**:
   - Controller patterns from code analysis
   - Design patterns from PR discussions
   - Error handling and retry patterns

3. **Distill design principles**:
   - From ADRs: architectural constraints and decisions
   - From PR discussions: team conventions and guidelines
   - From lessons learned: anti-patterns to avoid

4. **Identify risk factors**:
   - Complexity risks: Number of CRDs, integration points
   - Historical risks: Past bugs, regressions, incidents
   - Integration risks: External dependencies, API contracts

5. **Recommend approach for RFE**:
   - Suggest which patterns to follow
   - Identify which existing code/logic to reuse (reference specific PRs)
   - Highlight pitfalls to avoid (based on lessons learned)
   - Note dependencies on other teams/components

6. **Add comprehensive context section to output**:
   ```markdown
   ## Comprehensive Component Context

   ### Component: {component-name}

   **Repositories**:
   - Downstream: openshift/{repo}
   - Upstream: {org}/{upstream-repo}
   - Related: {related repos}

   **What it does**: {1-2 sentence summary}

   **Why it exists**: {purpose and value}

   **How it works**:
   - Architecture: {pattern}
   - Reconciliation: {flow summary for operators}
   - Integration: {external systems}

   **Key Implementation Patterns**:
   1. {Pattern}: {description}
   2. {Pattern}: {description}

   **Historical Context**:
   - PR #{number}: {key insight}
   - ADR: {decision reference}
   - Lesson: {anti-pattern to avoid}

   **Risk Factors**:
   - {Risk}: {mitigation}

   **Recommended Approach for RFE**:
   - {Guidance based on analysis}
   - Reuse: {specific code/PRs to leverage}
   - Avoid: {pitfalls from lessons learned}
   ```

#### 2.7.6: Integration with Epic/Story Generation

**Use comprehensive context when generating epics and stories**:

1. **In Epic scope definition** (Step 3):
   - Reference architecture patterns identified
   - Note integration points that must be addressed
   - Include risks from historical analysis

2. **In Technical Complexity assessment** (Step 3.5):
   - Use codebase structure to estimate complexity
   - Reference similar PRs for effort calibration
   - Note unknowns based on missing patterns

3. **In Story implementation guidance**:
   - Reference specific files/packages to modify
   - Suggest patterns to follow from historical PRs
   - Include lessons learned as acceptance criteria or notes

4. **In Effort estimation** (Step 4.6):
   - Calibrate estimates using similar past PRs
   - Example: "Similar to PR #456 which took 4 days"

**Performance Considerations**:

- **Caching**: Cache repository metadata and PR search results to `.work/jira/analyze-rfe/cache/`
- **Rate limiting**: Respect GitHub API rate limits (5000 req/hour for authenticated users)
- **Selective depth**: Limit deep PR analysis to top 5 PRs
- **Parallel execution**: Process multiple components concurrently if applicable

**Error Handling**:

- **Repository not found**: Note component doesn't have public repo, proceed without comprehensive context
- **API rate limit**: Cache what was gathered, note "analysis incomplete due to rate limit"
- **Private repositories**: Note access issue, suggest running with proper GitHub token

**Configuration**:

Users can control analysis depth via environment variables (optional):
- `ANALYZE_RFE_MAX_PRS=10`: Max PRs to search (default: 10)
- `ANALYZE_RFE_DEEP_DIVE_PRS=5`: Number of PRs to analyze in detail (default: 5)
- `GITHUB_TOKEN`: GitHub token for API access (required for private repos and higher rate limits)

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

### Step 4.5: Estimate Story Effort

**Objective**: Provide t-shirt sizing to support sprint planning.

**Sprint Duration**: 3 weeks per sprint/cycle

**Actions**:

1. **Estimate each story** using these criteria:
   - **Extra Small (XS)**:
     - ~1 Sprint (3 weeks) to complete
     - Single component change, standard testing
     - Example: Add new API parameter, simple validation logic, configuration change
     - Note: Consider if this should be a smaller task-sized issue
   - **Small (S)**:
     - ~2 Sprints (6 weeks) to complete
     - 1-2 components affected, unit + integration tests
     - Example: New API endpoint, UI component with state management
   - **Medium (M)**:
     - ~3 Sprints (9 weeks) to complete
     - Multiple components, cross-team coordination, complex testing
     - Example: New service integration, complex business logic with dependencies
   - **Large (L)**:
     - ~4 Sprints (12 weeks) to complete
     - Significant cross-component changes, extensive testing, possible data migration
     - Example: Major feature addition requiring API changes and UI overhaul
   - **Extra Large (XL)**:
     - ~5 Sprints (15 weeks) to complete
     - Many components, cross-team dependencies, architectural changes
     - **Flag for splitting**: XL stories should be broken down or elevated to Feature/Initiative level

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

### Step 4.6: Discover Related Work

**Objective**: Find related RFEs, epics, bugs to prevent duplication and leverage existing work.

**Actions**:

1. **Search Jira for related issues** using REST API:
   ```bash
   POST /rest/api/2/search
   Content-Type: application/json

   {
     "jql": "project = RFE AND text ~ \"<keyword>\" AND created >= -12M",
     "fields": ["key", "summary", "status", "created", "components"],
     "maxResults": 20
   }
   ```

   Run multiple searches (can be parallelized for performance):
   - **Related RFEs**: `project = RFE AND text ~ "<keyword>" AND created >= -12M AND key != {current-rfe}`
   - **Related Epics**: `issuetype = Epic AND component = "<component-name>" AND status IN ("In Progress", "To Do", "New")`
   - **Related Bugs**: `project = OCPBUGS AND component = "<component-name>" AND created >= -6M AND text ~ "<keyword>"`
   - **Same Component**: `component = "<component-name>" AND created >= -6M AND issuetype IN (Epic, Story, Feature)`
   - **Keyword Search**: `text ~ "<keyword1>" OR text ~ "<keyword2>" OR text ~ "<keyword3>"`

   Example Python code:
   ```python
   def search_jira(jql, fields=None, max_results=20):
       response = requests.post(
           f"{jira_url}/rest/api/2/search",
           headers={
               "Authorization": f"Bearer {token}",
               "Content-Type": "application/json"
           },
           json={
               "jql": jql,
               "fields": fields or ["key", "summary", "status"],
               "maxResults": max_results
           },
           timeout=30
       )
       return response.json()
   ```

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

## Comprehensive Component Context

### Component: [component-name]
*[If repositories found and analyzed - otherwise note "No public repository found for analysis"]*

**Repositories**:
- Downstream: openshift/{repo-name}
- Upstream: {org}/{upstream-repo} (if identified)
- Related: {comma-separated list of related repos}

**What it does**: {1-2 sentence description based on README and structure analysis}

**Why it exists**: {purpose and business value}

**How it works**:
- **Architecture**: {Kubernetes Operator | Library | CLI Tool | Microservice}
- **Key Packages**: {top 3-5 packages and their roles}
  - pkg/controllers/{name}: {purpose}
  - pkg/api/v1: {API definitions}
- **API Types** (for operators): {CRD kinds with brief description}
- **Integration Points**: {external systems - Kubernetes API, databases, cloud services}

**Key Implementation Patterns**:
1. **{Pattern name}**: {description from code or PR analysis}
2. **{Pattern name}**: {description}

**Critical Code Paths**:
- `{file path}`: {what it does and complexity estimate}

**Historical Context**:

**Relevant PRs**:
- PR #{number} (merged {date}): {title}
  - **Design**: {key design decision from PR}
  - **Why**: {rationale from discussion}
  - **Lesson**: {what was learned or why this approach}
  - **Scope**: {number of files changed, complexity}

**Architecture Decisions** (if ADRs found):
- **{ADR title}**: {decision summary}
  - **Rationale**: {why this decision}
  - **Trade-offs**: {pros and cons}

**Design Principles** (from PR discussions and ADRs):
1. {Principle}: {description}
2. {Principle}: {description}

**Lessons Learned** (from closed issues/bugs):
- Issue #{number}: {title}
  - **Lesson**: {what to avoid or ensure}
  - **Impact**: {how it affects this RFE}

**Risk Factors**:
- **{Risk type}** (Complexity/Historical/Integration): {description}
  - **Mitigation**: {how to address}

**Recommended Approach for RFE Implementation**:
- Follow {architecture pattern} established in {reference}
- Reuse {specific code/logic} from PR #{number}
- Apply design principle: {principle from analysis}
- Avoid {anti-pattern} (learned from Issue #{number})
- Consider {specific technical approach} based on {evidence}
- Estimate calibration: Similar to PR #{number} which modified {X} files and took {Y} time

---

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
**Effort**: S (~2 sprints / 6 weeks)
**Confidence**: High/Medium/Low
**Depends On**: [Story ID if applicable, or "None"]

### Epic 1 → Story 1.2: [Concise Title]
...

---

## Implementation Summary

### Effort Overview
| Epic | Stories | Total Effort |
|------|---------|--------------|
| Epic 1 | 5 stories | ~10-12 sprints (30-36 weeks) |

### Critical Dependencies
- [List of blocking items across epics]

### Key Risks Across All Epics
1. [Highest priority risk]
2. [Second priority risk]

---

## Outcomes Summary
| Story | Outcome | Effort |
|-------|---------|--------|
| 1.1 | [Outcome] | S (~2 sprints) |
| 1.2 | [Outcome] | M (~3 sprints) |

---
*Generated by `/jira:analyze-rfe` on [timestamp]*

## Next Steps
1. Review with product/engineering teams
2. Refine estimates and dependencies
3. Use `/jira:create epic` and `/jira:create story` to create issues in Jira
4. Schedule technical spike for: [List unknowns requiring research]
```

## Error Handling

**Authentication Failed** (401):
```
Error: Authentication failed (HTTP 401)

Required Setup:
1. Get Jira Personal Access Token:
   https://issues.redhat.com/secure/ViewProfile.jspa?selectedTab=com.atlassian.pats.pats-plugin:jira-user-personal-access-tokens

2. Set environment variable:
   export JIRA_PERSONAL_TOKEN="your_token_here"

3. Verify it works:
   curl -H "Authorization: Bearer $JIRA_PERSONAL_TOKEN" \
        "https://issues.redhat.com/rest/api/2/myself"
```

**Issue Not Found** (404):
```
Error: Issue {issue-key} not found (HTTP 404)

Verification Steps:
1. Check the issue key is correct (e.g., RFE-1234, not rfe-1234)
2. Verify you have read permissions for the RFE project
3. Confirm the issue exists: https://issues.redhat.com/browse/{issue-key}
```

**Access Denied** (403):
```
Error: Access denied (HTTP 403)

You need read permissions for:
- RFE project
- The specific issue's component
- Related projects (OCPBUGS, OCPSTRAT for related work discovery)

Contact your Jira administrator to request access.
```

**Token Not Configured**:
```
Error: JIRA_PERSONAL_TOKEN environment variable not set

Setup Instructions:
1. Get token: https://issues.redhat.com/secure/ViewProfile.jspa
2. Export: export JIRA_PERSONAL_TOKEN="your_token"
3. Restart Claude Code to pick up the new environment variable
```

**Network/Timeout Errors**:
```
Error: Connection timeout or network error

Check:
1. Network connectivity to Jira
2. VPN connection (if required)
3. Firewall rules allowing HTTPS to issues.redhat.com
```

**Not RFE Project**:
- Warn: "Issue is not from RFE project. Proceeding with analysis."
- Continue (user may have linked a related issue)

**Sparse RFE** (minimal description):
- Note: "RFE has limited detail. Consider enriching with: [suggested sections]"
- Generate best-effort breakdown from available content

**Missing Dependencies**:
```
Error: Required Python library not found

Install dependencies:
pip install requests aiohttp
```

## Best Practices for AI Implementation

1. **Synthesize, don't copy**: Transform RFE content into proper agile artifacts
2. **Right-size**: Epics = quarter scope, Stories = sprint scope
3. **Outcome-focused**: Every story should have a clear customer/business outcome
4. **Reference conventions**: Use create-epic and create-story skill formats
5. **Link to source**: When generating stories, reference which RFE bullet they address
6. **Be realistic about complexity**: Don't downplay risks or unknowns; flag them explicitly
7. **Estimate conservatively**: When in doubt, size larger; teams can adjust down
8. **Map dependencies explicitly**: Clear dependency graphs prevent planning surprises
9. **Search thoroughly for related work**: Spend time on Jira search to prevent duplicate effort
10. **Flag XL stories immediately**: Stories > 1 week should be broken down before planning
11. **Make risks measurable**: Quantify impact when possible (e.g., "affects 50K clusters", "3 external API integrations")

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
     - Effort: L (~4 sprints / 12 weeks - API changes, validation, tests)
     - Depends on: None
   - Story 2: As cluster admin, I want to rotate cert without downtime...
     - Effort: M (~3 sprints / 9 weeks - reuse logic from RFE-3456)
     - Depends on: Story 1
   - Story 3: As cluster admin, I want validation before cluster goes active...
     - Effort: S (~2 sprints / 6 weeks - validation library integration)
     - Depends on: Story 1

6. Outcomes:
   - Story 1 → Enables compliance-driven deployments
   - Story 2 → Reduces operational risk
   - Story 3 → Prevents misconfiguration

7. Implementation Summary:
   - Total effort: ~9 sprints (27 weeks)
   - Critical path: Story 1 blocks Stories 2, 3
   - Key risk: API contract negotiation with consuming teams

8. Output markdown report with all analysis
```

## See Also

- `create-feature-request` skill - RFE structure and conventions
- `create-epic` skill - Epic format and acceptance criteria
- `create-story` skill - User story format and acceptance criteria
- `/jira:create` - Create the generated epics and stories in Jira
