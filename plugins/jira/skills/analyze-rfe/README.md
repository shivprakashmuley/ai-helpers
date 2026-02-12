# jira:analyze-rfe - RFE Analysis and Breakdown

Analyze Request for Enhancement (RFE) issues and generate comprehensive breakdowns of Epics, user stories, and outcomes with technical feasibility assessment.

## Quick Start

### Prerequisites (5-minute setup)

1. **Get Jira Personal Access Token**
   - Visit: https://issues.redhat.com/secure/ViewProfile.jspa?selectedTab=com.atlassian.pats.pats-plugin:jira-user-personal-access-tokens
   - Click "Create token" → Copy token

2. **Set Environment Variable**
   ```bash
   export JIRA_PERSONAL_TOKEN="your_token_here"
   ```

3. **Install Dependencies**
   ```bash
   pip install requests aiohttp
   ```

4. **Verify Setup**
   ```bash
   curl -H "Authorization: Bearer $JIRA_PERSONAL_TOKEN" \
        "https://issues.redhat.com/rest/api/2/myself"
   ```

### Usage

```bash
# In Claude Code
/jira:analyze-rfe RFE-1234

# Or with URL
/jira:analyze-rfe https://issues.redhat.com/browse/RFE-1234
```

---

## What It Does

The command performs deep analysis of RFE issues and generates:

### 1. RFE Summary
- Key capability being requested
- Business driver and value
- Affected components and teams

### 2. Related Work Discovery
- Finds related RFEs, epics, and bugs
- Identifies duplicate or overlapping work
- Suggests reuse opportunities

### 3. Component Context (if available)
- Loads component documentation from workspace
- Enriches analysis with component architecture
- Provides historical context from PRs and design decisions

### 4. EPIC(s) Generation
- Breaks down RFE into one or more epics
- Defines scope and acceptance criteria
- Assesses technical complexity and risks
- Maps dependencies and integration points

### 5. User Stories
- Creates user stories in "As a... I want... So that..." format
- Provides acceptance criteria
- Estimates effort (XS/S/M/L/XL based on sprints)
- Maps story dependencies

### 6. Implementation Summary
- Aggregates effort across all epics
- Identifies critical dependencies
- Highlights key risks
- Provides outcomes mapping

---

## Output Example

```markdown
# RFE Analysis: RFE-1234 - Custom SSL Certificates for Control Planes

## RFE Summary
- **Source**: [RFE-1234](https://issues.redhat.com/browse/RFE-1234)
- **Key Capability**: Support custom SSL certificates for managed control planes
- **Business Driver**: Enterprise compliance (SOC2, ISO requirements)
- **Affected Components**: HyperShift, Networking, Security

## Related Work
| Issue | Relationship | Recommendation |
|-------|--------------|----------------|
| [RFE-3456] - TLS Rotation | Related | Leverage rotation logic |
| [EPIC-890] - Cert Management | Overlap | Coordinate with Team B |

## EPIC 1: Custom SSL Certificate Management

**Objective**: Enable cluster admins to upload and manage custom SSL certificates

**Scope**:
- In: Upload during creation, post-creation rotation, validation, alerts
- Out: Certificate generation, CA management

**Technical Complexity**: High
- New cert validation library
- API changes to cluster creation
- Migration for existing clusters

**Key Risks**:
- Breaking change to cluster creation API
- Coordination with consuming teams needed

**Dependencies**: Requires cert-manager operator from Platform team

## User Stories

### Story 1.1: Upload Custom Certificate During Cluster Creation
**As a** cluster admin, **I want to** upload a custom SSL certificate during cluster creation, **so that** I can meet compliance requirements from day one.

**Acceptance Criteria**:
- Upload PEM-encoded certificate and private key
- Validation before cluster provisioning
- Error messages for invalid certificates

**Effort**: L (~4 sprints / 12 weeks)
**Depends On**: None

### Story 1.2: Rotate Certificate Without Downtime
**As a** cluster admin, **I want to** rotate SSL certificates without cluster downtime, **so that** I can renew expiring certificates safely.

**Effort**: M (~3 sprints / 9 weeks)
**Depends On**: Story 1.1

## Implementation Summary

**Total Effort**: ~9 sprints (27 weeks)
**Critical Path**: Story 1.1 blocks all other stories
**Key Risk**: API contract changes require cross-team coordination
```

---

## Documentation

### Setup Guides
- **[PREREQUISITES.md](PREREQUISITES.md)** - Quick checklist and verification
- **[SETUP.md](SETUP.md)** - Comprehensive setup guide with troubleshooting

### Technical Documentation
- **[SKILL.md](SKILL.md)** - Implementation details for AI agents
- **[../../commands/analyze-rfe.md](../../commands/analyze-rfe.md)** - Command reference

---

## Features

### Deep Analysis
- ✅ Parses RFE structure (Nature, Use Case, Business Requirements)
- ✅ Extracts affected components and teams
- ✅ Identifies scope signals (single vs. multiple capabilities)

### Related Work Discovery
- ✅ Searches for related RFEs, epics, and bugs
- ✅ Identifies duplicate or overlapping work
- ✅ Suggests reuse opportunities

### Component Context Integration
- ✅ Loads workspace component documentation
- ✅ Enriches with component architecture knowledge
- ✅ Includes historical context from PRs and ADRs

### Technical Assessment
- ✅ Complexity analysis (High/Medium/Low)
- ✅ Risk identification (blockers, unknowns, tech debt)
- ✅ Cross-component dependency mapping
- ✅ Integration point analysis

### Effort Estimation
- ✅ T-shirt sizing (XS/S/M/L/XL)
- ✅ Sprint-based estimates (1 sprint = 3 weeks)
- ✅ Confidence levels (High/Medium/Low)
- ✅ Story dependency mapping

### Outcomes Focus
- ✅ Customer and business outcomes for each story
- ✅ Measurable value delivery
- ✅ Epic-level outcome aggregation

---

## Performance

### Speed (vs. MCP Server)
- **4x faster** overall (1.2s vs 4.8s)
- **5x faster** searches (parallel execution)
- **10x less** data transfer (field optimization)

### API Calls
- 6-13 Jira API calls per RFE analysis
- All searches run in parallel
- Optimized field filtering

---

## Requirements

### Environment Variables
```bash
export JIRA_PERSONAL_TOKEN="your_token"      # Required
export JIRA_URL="https://issues.redhat.com"  # Optional (default)
```

### Python Libraries
```bash
pip install requests aiohttp
```

### Jira Permissions
- Read access to RFE project
- Read access to OCPBUGS project
- Read access to component projects (for related work)

### Network Access
- HTTPS access to issues.redhat.com
- VPN connection (if required by your organization)

---

## Troubleshooting

### "JIRA_PERSONAL_TOKEN not configured"
```bash
# Get token from: https://issues.redhat.com/secure/ViewProfile.jspa
export JIRA_PERSONAL_TOKEN="your_token"
source ~/.bashrc  # Reload environment
```

### "Authentication failed (HTTP 401)"
- Token may be invalid or expired
- Create a new token and update the environment variable

### "Issue not found (HTTP 404)"
- Check issue key is correct (case-sensitive)
- Verify you have read permissions
- Confirm issue exists in Jira

### "Connection timeout"
- Check network connectivity
- Ensure VPN is connected (if required)
- Verify firewall allows HTTPS to Jira

**More help**: See [SETUP.md](SETUP.md) → Troubleshooting section

---

## Examples

### Basic Usage
```bash
/jira:analyze-rfe RFE-1234
```

### With URL
```bash
/jira:analyze-rfe https://issues.redhat.com/browse/RFE-1234
```

### Testing the Setup
```bash
# Verify token works
curl -H "Authorization: Bearer $JIRA_PERSONAL_TOKEN" \
     "https://issues.redhat.com/rest/api/2/myself"

# Test fetch script
python3 plugins/jira/skills/analyze-rfe/scripts/fetch_rfe.py RFE-1234

# Run full analysis
/jira:analyze-rfe RFE-1234
```

---

## Advanced Configuration

### Custom Jira Instance
```bash
export JIRA_URL="https://jira.yourcompany.com"
```

### Proxy Configuration
```bash
export HTTP_PROXY="http://proxy.company.com:8080"
export HTTPS_PROXY="http://proxy.company.com:8080"
```

### Using .netrc (Alternative to Environment Variable)
```bash
cat > ~/.netrc << EOF
machine issues.redhat.com
login your_email@redhat.com
password your_jira_token
EOF

chmod 600 ~/.netrc
```

---

## Next Steps After Analysis

1. **Review the breakdown** with product and engineering teams
2. **Refine estimates** based on team capacity and historical data
3. **Create epics and stories** in Jira:
   ```bash
   /jira:create epic
   /jira:create story
   ```
4. **Schedule spikes** for unknowns identified in the analysis
5. **Plan sprints** using the effort estimates

---

## Technical Details

### API Calls Made
1. Fetch RFE issue (1 call)
2. Search for related RFEs (1 call)
3. Search for related epics (1 call)
4. Search for related bugs (1 call)
5. Search same component issues (1 call)
6. Keyword-based search (1-2 calls)
7. Fetch linked issues (0-5 calls)
8. Get comments (1 call, optional)
9. Get changelog (1 call, optional)

**Total**: 6-13 API calls, most executed in parallel

### Architecture
- Uses Jira REST API v2
- Parallel async requests for performance
- Field optimization to minimize data transfer
- Comprehensive error handling
- Token-based authentication (Bearer)

---

## Support

### Documentation
- **Setup**: [SETUP.md](SETUP.md)
- **Prerequisites**: [PREREQUISITES.md](PREREQUISITES.md)
- **Command Docs**: [../../commands/analyze-rfe.md](../../commands/analyze-rfe.md)

### Getting Help
- **Plugin Issues**: https://github.com/openshift-eng/ai-helpers/issues
- **Jira Access**: Your Jira administrator
- **Network/VPN**: Your IT support

---

## License

Part of the [ai-helpers](https://github.com/openshift-eng/ai-helpers) plugin collection.

---

**Version**: 0.0.1
**Last Updated**: 2025-02-12
**Maintained by**: openshift-eng
