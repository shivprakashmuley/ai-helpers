# Operator-Operand Analysis Guide

## Overview

In OpenShift, many components follow the **Operator pattern**, where:
- **Operator**: A Kubernetes controller that manages the lifecycle of workloads
- **Operand(s)**: The actual workload(s) being managed by the operator

For comprehensive RFE analysis, we need to analyze **both the operator AND its operands**, as they have different responsibilities and an RFE may require changes in either or both.

## Examples of Operator-Operand Relationships

### cluster-monitoring-operator
- **Operator**: `openshift/cluster-monitoring-operator`
- **Operands**:
  - `prometheus` - Metrics collection and alerting
  - `alertmanager` - Alert routing and notifications
  - `prometheus-operator` - Manages Prometheus instances
  - `node-exporter` - Node-level metrics collection
  - `kube-state-metrics` - Kubernetes object metrics

### cluster-logging-operator
- **Operator**: `openshift/cluster-logging-operator`
- **Operands**:
  - `fluentd` - Log collection and forwarding
  - `elasticsearch` - Log storage and search
  - `kibana` - Log visualization

### cert-manager-operator
- **Operator**: `openshift/cert-manager-operator`
- **Operands**:
  - `cert-manager` - Certificate management controller
  - `cert-manager-webhook` - Admission webhook
  - `cainjector` - CA bundle injection

## Why Analyze Both?

### Operator Responsibilities
- **Lifecycle management**: Installation, upgrades, configuration
- **Resource management**: Creating/updating operand deployments
- **Configuration**: Translating CRs into operand configuration
- **Monitoring**: Health checks, metrics collection
- **Status reporting**: Aggregating operand status

### Operand Responsibilities
- **Core functionality**: Business logic and workload processing
- **API implementation**: Actual feature implementation
- **Data processing**: Handling workload-specific operations
- **Integration**: External system communication

### Where to Implement RFEs

**Operator changes** needed for:
- New configuration options (add field to CR, pass to operand)
- Deployment topology changes (replicas, anti-affinity, etc.)
- Upgrade/migration logic
- Resource constraints (memory, CPU limits)
- Monitoring/alerting rules

**Operand changes** needed for:
- New feature functionality
- API/protocol changes
- Performance improvements
- Bug fixes in core logic
- New integrations with external systems

**Both** needed for:
- New CRDs or API types
- Feature flags requiring both config and implementation
- Major architectural changes

## How Operand Discovery Works

### Automatic Discovery

The script automatically discovers operands using multiple strategies:

#### 1. README Analysis
Searches README for patterns like:
- "manages X, Y, and Z"
- "deploys X"
- "operands: X, Y"
- Markdown list items with component names

**Example**:
```markdown
The Cluster Monitoring Operator manages:
* [Prometheus](https://github.com/prometheus/prometheus)
* [Alertmanager](https://github.com/prometheus/alertmanager)
```
→ Discovers: `prometheus`, `alertmanager`

#### 2. Deployment Manifests
Parses manifest files (YAML) for image references:

**Example** (from `manifests/deployment.yaml`):
```yaml
spec:
  containers:
  - name: prometheus
    image: quay.io/openshift/prometheus:v2.40.0
```
→ Discovers: `prometheus`

#### 3. OLM ClusterServiceVersion (CSV)
Extracts operands from OLM metadata:

**Example** (from `bundle/manifests/cluster-monitoring-operator.csv.yaml`):
```yaml
spec:
  install:
    spec:
      deployments:
      - name: prometheus-operator
      - name: alertmanager
```
→ Discovers: `prometheus-operator`, `alertmanager`

### Repository Enrichment

After discovering operand names, the script:
1. Searches for corresponding repositories in `openshift/` org
2. Tries common patterns:
   - `openshift/{operand-name}`
   - `openshift/{operand-name}-controller`
   - `openshift/{operand-name}-server`
3. Attaches repository metadata (URL, description)

## User Interaction

When operands are discovered, you'll be asked:

```
======================================================================
Operands Found for cluster-monitoring
======================================================================
This is an Operator managing 2 operand(s):
  1. prometheus (openshift/prometheus)
  2. alertmanager (openshift/alertmanager)

Operand analysis includes:
  - Codebase structure for each operand
  - Historical PR analysis
  - Implementation patterns

This is useful for:
  - Understanding operator vs operand responsibilities
  - Determining where to implement RFE (operator or operand)
  - Comprehensive view of the full component stack

Note: This will add ~10-20 seconds per operand
======================================================================

Analyze operand repositories? [y/N]:
```

## When to Analyze Operands

### Answer "Yes" For:

**Configuration-focused RFEs**:
- Example: "Add support for custom Prometheus retention policies"
- Why: Need to understand both how operator configures AND how Prometheus implements retention
- Value: See full configuration flow from CR to operand

**Feature parity RFEs**:
- Example: "Support Alertmanager clustering"
- Why: Understand if operand already supports it, operator just needs to enable
- Value: Identify configuration vs functionality gaps

**Performance RFEs**:
- Example: "Improve metrics collection performance"
- Why: Could be operator deployment topology OR operand implementation
- Value: Determine bottleneck location

**Multi-component RFEs**:
- Example: "Add support for remote write to external Prometheus"
- Why: Touches both Prometheus (operand) and configuration (operator)
- Value: Full stack understanding

### Answer "No" For:

**Pure operator concerns**:
- Example: "Support running operator on ARM architecture"
- Why: Only affects operator, not operands
- Value: None - operands not relevant

**Deployment-only changes**:
- Example: "Add anti-affinity rules for operator pods"
- Why: Purely deployment configuration
- Value: None - operand logic unchanged

**Quick analysis**:
- Example: Need fast turnaround for planning meeting
- Why: Operand analysis adds 10-20 seconds per operand
- Value: Limited when time-constrained

## Output Format

When operands are analyzed, additional sections are added:

```markdown
### Component: cluster-monitoring

**What it does**: Operator for OpenShift cluster monitoring stack (Operator managing workload operands)

**Repositories**:
- Downstream: openshift/cluster-monitoring-operator
- Related: ...

**Operand Repositories**:

*This operator manages the following operands:*

1. **prometheus** (`openshift/prometheus`)
   - The Prometheus monitoring system and time series database
   - Architecture: CLI Tool / Binary
   - Key packages: promql, storage
   - Analyzed 2 relevant PR(s)

2. **alertmanager** (`openshift/alertmanager`)
   - Prometheus Alertmanager for alert routing
   - Architecture: CLI Tool / Binary
   - Key packages: api, dispatch
   - Analyzed 1 relevant PR(s)

**Operator vs Operand Responsibilities**:
- **Operator**: Lifecycle management, configuration, upgrades, monitoring
- **Operands**: Core workload functionality, business logic

**Implementation Guidance**:
- **Configuration/lifecycle changes**: Implement in operator
- **Core functionality changes**: Implement in operand
- **API/CRD changes**: May require both operator and operand changes
```

## Command-Line Control

### Interactive Mode (Default)
```bash
./gather_component_context.py cluster-monitoring --keywords "prometheus retention"
# Will prompt when operands discovered
```

### Always Analyze Operands
```bash
./gather_component_context.py cluster-monitoring \
  --analyze-operands \
  --keywords "prometheus retention"
```

### Never Analyze Operands
```bash
./gather_component_context.py cluster-monitoring \
  --skip-operands \
  --keywords "prometheus retention"
```

### Non-Interactive Mode
```bash
./gather_component_context.py cluster-monitoring \
  --no-interactive \
  --keywords "prometheus retention"
# Skips operands (and upstream) by default
```

## Performance Impact

**Per operand**:
- Repository discovery: ~2-3 seconds
- Structure analysis: ~3-5 seconds
- PR search (if keywords): ~5-10 seconds
- Total: ~10-20 seconds per operand

**Example** (cluster-monitoring with 3 operands):
- Without operands: ~20 seconds
- With operands: ~50-80 seconds
- Still within acceptable range for comprehensive analysis

## Integration with /jira:analyze-rfe

When `/jira:analyze-rfe` runs:

1. **Detect operator components** from RFE "Affected Components"
2. **Discover operands** automatically
3. **Ask user** if operands should be analyzed
4. **Analyze each operand** (if approved)
5. **Synthesize holistic view** in RFE breakdown:
   - Operator responsibilities
   - Operand responsibilities
   - Where to implement this RFE

**Example flow**:

```python
# In analyze-rfe skill
component_name = "cluster-monitoring"

context = gather_component_context(
    component_name,
    rfe_keywords=["prometheus", "retention", "custom"],
    analyze_operands=None,  # Will ask user
    interactive=True
)

if context.get("is_operator") and context.get("operands"):
    # Generate epic/story guidance
    for operand in context["operands"]:
        operand_name = operand["name"]
        # Note: Story X.Y may need changes in {operand_name} operand
```

## Best Practices

1. **Always analyze operands** for:
   - Feature parity RFEs
   - Configuration-heavy RFEs
   - Multi-component RFEs
   - Performance RFEs

2. **Skip operands** for:
   - Pure operator concerns
   - Deployment-only changes
   - Time-constrained analysis

3. **Use implementation guidance** to determine:
   - Which repos need changes
   - Story placement (operator vs operand)
   - Dependencies between operator and operand stories

4. **Leverage operand insights** for:
   - Effort estimation (compare to operand PRs)
   - Risk identification (operand complexity)
   - Design patterns (how operand is configured)

## Examples

### Example 1: Prometheus Retention RFE

**RFE**: "Support custom Prometheus retention policies in OpenShift monitoring"

**Components**: cluster-monitoring-operator

**Answer**: **Yes** to operand analysis

**Why**: Need to understand both:
- How operator passes retention config to Prometheus
- How Prometheus implements retention logic

**Result**:
- Operator context: Configuration management patterns
- Prometheus operand context: Retention implementation, storage backend
- Implementation guidance: Add CR field (operator), validate config (operator), apply retention (Prometheus handles automatically)

### Example 2: Operator ARM Support

**RFE**: "Support cluster-monitoring-operator on ARM architecture"

**Components**: cluster-monitoring-operator

**Answer**: **No** to operand analysis

**Why**: Pure operator deployment concern, operands already support ARM

**Result**:
- Operator context: Sufficient
- Skip operand analysis: Not relevant

## Summary

**Operator-operand analysis provides**:
- ✓ Complete view of component stack
- ✓ Clear implementation guidance (operator vs operand)
- ✓ Better effort estimation
- ✓ Reduced risk of missing dependencies

**When to use**:
- Configuration-focused RFEs
- Feature parity analysis
- Multi-component changes
- Performance improvements

**Performance**: Adds ~10-20 seconds per operand, worthwhile for comprehensive understanding.
