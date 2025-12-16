---
name: Must-Gather Config Discovery
description: Local analysis of must-gather artifacts to generate intelligent obfuscation configuration
---

# Must-Gather Config Discovery

This skill provides local, privacy-preserving analysis of must-gather artifacts to generate intelligent obfuscation configurations for the `must-gather-clean` tool.

## Overview

The discovery process scans must-gather artifacts **entirely locally** (no data sent externally) to detect sensitive patterns and suggest appropriate obfuscation rules. This helps users create custom configurations without manually inspecting the entire must-gather.

## When to Use This Skill

Use this skill when:
- You need to obfuscate a must-gather that contains custom proprietary information
- The default OpenShift config is too generic for your needs
- You want to ensure specific patterns (domain names, keywords, secret formats) are obfuscated
- You're unsure what sensitive data might be present in the must-gather

## How It Works

The discovery script (`discover_config.py`) performs three types of analysis:

### 1. Entropy Analysis

Detects high-entropy strings that are likely secrets, tokens, or API keys.

**Method**: Calculates Shannon entropy for strings and flags those exceeding 4.5 bits/character.

**Examples detected**:
- GitHub tokens: `ghp_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0`
- Base64-encoded secrets
- Random API keys and tokens

**Excluded**: Known non-sensitive high-entropy strings like container image hashes starting with `sha256:`

### 2. Pattern Recognition

Scans for well-known secret formats using regex patterns.

**Detected patterns**:
- AWS Access Keys: `AKIA[0-9A-Z]{16}`
- AWS Secret Keys: `aws_secret_access_key = [A-Za-z0-9/+=]{40}`
- GitHub tokens: `ghp_...`, `github_pat_...`
- Slack tokens: `xoxp-...`, `xoxb-...`, `xoxa-...`
- Google API keys: `AIza...`
- Private key headers: `-----BEGIN PRIVATE KEY-----`
- Azure client IDs: UUID format
- JWT tokens: `eyJ...`
- Generic API keys: `api_key=...` patterns

### 3. Learned Keywords

Analyzes Kubernetes resources to identify proprietary terms.

**Sources**:
- Custom namespace names (excluding `openshift-*`, `kube-*`)
- Resource labels and annotations
- Project names from metadata
- Custom image repository names (excluding well-known registries)
- Organization names from container images

**Example**: If your must-gather contains namespace `acme-production` and images from `quay.io/acme-corp/`, the script identifies `acme-production` and `acme-corp` as keywords to obfuscate.

### 4. Domain Name Discovery

Extracts custom domain names from networking resources.

**Sources**:
- Route resources (`route.openshift.io`)
- Ingress resources (`networking.k8s.io`)
- Certificate resources

**Excluded**: Standard domains like `cluster.local`, `svc`, `*.openshift.io`, `*.k8s.io`, `*.redhat.com`

**Example**: Finds `api.example.com`, `app.prod.example.com` and suggests obfuscating both `example.com` and `prod.example.com`

## Implementation Steps

### Step 1: Locate the Discovery Script

```bash
SCRIPT_PATH=$(find ~ -name "discover_config.py" -path "*/must-gather/skills/must-gather-obfuscate/*" 2>/dev/null | head -1)

if [ -z "$SCRIPT_PATH" ]; then
    echo "ERROR: Discovery script not found."
    exit 1
fi

SCRIPT_DIR=$(dirname "$SCRIPT_PATH")
```

### Step 2: Run the Discovery Analysis

```bash
# Create output directory
mkdir -p .work/must-gather-clean/

# Run the discovery script locally
python3 "$SCRIPT_DIR/discover_config.py" \
    "/path/to/must-gather" \
    ".work/must-gather-clean/discovered-config.yaml"
```

**Parameters**:
- `$1`: Path to must-gather directory (containing `cluster-scoped-resources/`, `namespaces/`)
- `$2`: Output path for generated config file

### Step 3: Review the Generated Config

The script outputs:

1. **Console summary** showing:
   - Number and types of secret patterns found
   - List of discovered domain names
   - List of proprietary keywords identified

2. **Config file** at specified output path containing:
   - Regex obfuscators for detected secret patterns
   - Keyword replacements for proprietary terms
   - Domain obfuscation rules
   - Standard IP/MAC obfuscation
   - Default Kubernetes resource omissions

Example output:

```
================================================================================
DISCOVERY RESULTS
================================================================================

Potential secret patterns found:
  - github_token: 3 occurrence(s)
  - aws_access_key: 1 occurrence(s)

Custom domain names (2 found):
  - api.example.com
  - app.prod.example.com

Proprietary keywords (5 found):
  - acme-production
  - acme-staging
  - acme-corp
  - internal-app
  - custom-service

================================================================================

[✓] Configuration generated: .work/must-gather-clean/discovered-config.yaml
```

### Step 4: Use the Generated Config

```bash
# Run must-gather-clean with the discovered config
./must-gather-clean \
    -c .work/must-gather-clean/discovered-config.yaml \
    -i /path/to/must-gather \
    -o /path/to/output
```

## Configuration Structure

The generated config follows the must-gather-clean schema:

```yaml
config:
  obfuscate:
    # Regex patterns for detected secrets
    - type: Regex
      regex: "AKIA[0-9A-Z]{16}"
      target: FileContents

    # Proprietary keywords
    - type: Keywords
      target: All
      replacement:
        acme-production: keyword-0001
        acme-corp: keyword-0002

    # Discovered domains
    - type: Domain
      replacementType: Consistent
      target: All
      domainNames:
        - example.com
        - api.example.com

    # Standard obfuscation
    - type: IP
      replacementType: Consistent
      target: All
    - type: MAC
      replacementType: Consistent
      target: All

  omit:
    - type: Kubernetes
      kubernetesResource:
        kind: Secret
    - type: Kubernetes
      kubernetesResource:
        kind: ConfigMap
```

## Performance Considerations

To ensure reasonable performance on large must-gathers:

- **Sampling**: Scans maximum of 500 files for secret patterns
- **File size limit**: Skips files larger than 10MB
- **Read limit**: Reads maximum 1MB per file
- **Smart targeting**: Focuses on YAML files and logs where secrets are most likely

## Privacy Guarantees

**CRITICAL**: This script operates entirely locally.

- No network requests are made
- No data is sent to external services
- No LLM or AI service is used
- All analysis uses local pattern matching and heuristics
- Safe to use with highly sensitive must-gather data

## Error Handling

Common issues and solutions:

**Missing pyyaml package**:
```bash
pip3 install pyyaml
```

**Python 3 not found**:
```bash
# Linux
sudo dnf install python3
# or
sudo apt install python3

# macOS
brew install python3
```

**Script not executable**:
```bash
chmod +x plugins/must-gather/skills/must-gather-obfuscate/discover_config.py
```

## Customizing the Output

After generation, you can edit the config file to:
- Remove obfuscation rules you don't need
- Add additional patterns or keywords
- Adjust replacement types (Consistent vs Static)
- Add file omission patterns

## Limitations

- **Heuristic-based**: May not catch all secrets in non-standard formats
- **False positives**: High-entropy analysis may flag some non-sensitive strings
- **Performance**: Very large must-gathers (>10GB) may take several minutes to analyze
- **Custom secrets**: Application-specific secret formats may require manual addition to the config

## Best Practices

1. **Always review** the generated config before using it
2. **Edit as needed** to add custom patterns specific to your environment
3. **Test first** on a small subset if working with very large must-gathers
4. **Spot-check** the obfuscated output to ensure sensitive data was properly handled
5. **Save configs** for reuse when cleaning similar must-gathers from the same environment

## Related Documentation

- [must-gather-clean Configuration Schema](https://github.com/openshift/must-gather-clean#configuration)
- [Shannon Entropy](https://en.wikipedia.org/wiki/Entropy_(information_theory))
- [Common Secret Patterns](https://github.com/openshift/must-gather-clean#obfuscation)
