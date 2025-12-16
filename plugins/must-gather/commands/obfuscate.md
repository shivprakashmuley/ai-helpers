---
description: Obfuscate sensitive data in must-gather artifacts using must-gather-clean
argument-hint: "[must-gather-path] [output-path] [--config config-file | --discover]"
---

## Name
must-gather:obfuscate

## Synopsis
```
/must-gather:obfuscate [must-gather-path] [output-path] [--config config-file | --discover]
```

## Description

The `obfuscate` command removes sensitive information from OpenShift must-gather artifacts using the `must-gather-clean` tool. This is essential when sharing must-gather data with external parties, support teams, or public bug reports.

The command:
1. Obtains the must-gather-clean binary (downloads release or builds from source)
2. Optionally generates a custom configuration based on your requirements
3. Runs must-gather-clean on the provided artifacts to obfuscate sensitive data
4. Outputs the cleaned artifacts to the specified location

**Binary Installation Methods:**
- **Download Release** (Recommended): Downloads pre-built binary from GitHub releases - fast, no build tools needed
- **Build from Source**: Clones repository and builds using make - gets latest development version

**Configuration Options:**
- **Default**: Uses built-in default config (obfuscates IPs, MACs, omits Secrets/ConfigMaps)
- **Custom Config**: Pass your own config file with `--config <path>`
- **Discovery Mode**: Use `--discover` to scan the must-gather locally and generate an intelligent config

**Discovery Mode** uses local analysis (no data sent externally) to detect:
- **High-entropy strings** (potential secrets, tokens, API keys)
- **Known secret patterns** (AWS keys, GitHub tokens, Slack tokens, JWTs, etc.)
- **Custom domain names** from Routes, Ingresses, and Certificates
- **Proprietary keywords** from namespace names, labels, and image repositories

**What gets obfuscated:**
- IP addresses
- Hostnames
- Domain names
- MAC addresses
- Usernames
- Passwords and secrets
- Certificate data
- Custom resource sensitive fields

## Prerequisites

**Required Tools:**

1. **curl or wget**: For downloading the release binary (recommended method)
   - Usually pre-installed on most systems
   - Check: `curl --version` or `wget --version`

2. **Python 3**: Required for discovery mode (`--discover` flag only)
   - Check if installed: `python3 --version`
   - Required packages: `pyyaml` (install with `pip3 install pyyaml`)
   - If not installed:
     - **Linux**: `sudo dnf install python3` or `sudo apt install python3 python3-pip`
     - **macOS**: Usually pre-installed, or `brew install python3`
   - Only needed if using `--discover` flag

**Optional (for building from source):**

3. **Go (golang)**: Only needed if building from source instead of downloading release
   - Check if installed: `go version`
   - If not installed, provide installation instructions:
     - **Linux**: `sudo dnf install golang` or `sudo apt install golang-go`
     - **macOS**: `brew install go`
     - **Manual**: https://go.dev/doc/install
   - Minimum version: Go 1.19 or later

4. **Make**: Only needed if building from source
   - Check if installed: `make --version`
   - If not installed:
     - **Linux**: `sudo dnf install make` or `sudo apt install build-essential`
     - **macOS**: Usually pre-installed with Xcode Command Line Tools

5. **Git**: Only needed if building from source
   - Check if installed: `git --version`
   - Usually pre-installed on most systems

**Required Directory Structure:**

Must-gather data typically has this structure:
```
must-gather/
└── registry-ci-openshift-org-origin-...-sha256-<hash>/
    ├── cluster-scoped-resources/
    ├── namespaces/
    └── ...
```

The actual must-gather directory is the subdirectory with the hash name, not the parent directory.

## Implementation

The command performs the following steps:

1. **Parse Arguments**:
   - Check if `--discover` flag is present in the arguments
   - Check if `--config <file>` is present in the arguments
   - Extract must-gather path and output path from remaining arguments

2. **Validate Input Path**:
   - If must-gather path not provided as argument, ask the user
   - Verify the path exists and is readable
   - Check if path contains must-gather data (look for `cluster-scoped-resources/` or `namespaces/` directories)
   - If user provides root directory, automatically find the correct subdirectory

3. **Determine Output Path**:
   - If output path not provided, use default: `<must-gather-path>-obfuscated`
   - Verify output path doesn't already exist (to avoid overwriting)
   - If it exists, ask user if they want to overwrite or provide a different path

4. **Handle Configuration** (Choose one mode):

   **Mode A: Discovery Mode (`--discover`)**:

   This mode uses a local Python script to analyze the must-gather and generate an intelligent configuration.
   **IMPORTANT**: All analysis is done locally - no data is sent to any external service or LLM.

   a. **Locate the Discovery Script**:
      ```bash
      SCRIPT_PATH=$(find ~ -name "discover_config.py" -path "*/must-gather/skills/must-gather-obfuscate/*" 2>/dev/null | head -1)

      if [ -z "$SCRIPT_PATH" ]; then
          echo "ERROR: Discovery script not found."
          echo "Please ensure the must-gather plugin is properly installed."
          exit 1
      fi

      SCRIPT_DIR=$(dirname "$SCRIPT_PATH")
      ```

   b. **Run Discovery Analysis**:
      ```bash
      # Create output directory for config
      mkdir -p .work/must-gather-clean/

      # Run the local discovery script
      python3 "$SCRIPT_DIR/discover_config.py" \
          "$MUST_GATHER_PATH" \
          ".work/must-gather-clean/discovered-config.yaml"
      ```

      The script performs these analyses locally:
      - **Entropy Analysis**: Scans for high-entropy strings (Shannon entropy > 4.5 bits/char) in YAML files and logs
      - **Pattern Recognition**: Detects known secret formats:
        * AWS keys (`AKIA...`), secret keys
        * GitHub tokens (`ghp_...`, `github_pat_...`)
        * Slack tokens (`xoxp-...`, `xoxb-...`)
        * Google API keys (`AIza...`)
        * JWT tokens
        * Private key headers
        * Azure client IDs
        * Generic API key patterns
      - **Domain Discovery**: Extracts custom domains from Routes, Ingresses, Certificates
      - **Keyword Learning**: Identifies proprietary keywords from:
        * Custom namespace names
        * Resource labels and annotations
        * Image repository names
        * Service names

   c. **Review Generated Config**:
      - Display the discovered items summary to user
      - Show the generated config file location: `.work/must-gather-clean/discovered-config.yaml`
      - Ask user if they want to review/edit the config before proceeding
      - If user wants to edit, open the config file for editing
      - Set `CONFIG_FILE=".work/must-gather-clean/discovered-config.yaml"` for use in obfuscation

   **Mode B: Custom Config File (`--config <file>`)**:
   - Verify the config file exists and is readable
   - Validate it's a valid YAML file
   - Set `CONFIG_FILE=<user-provided-path>` for use in obfuscation

   **Mode C: Default Config (no flags)**:
   - Use the default OpenShift config from must-gather-clean examples
   - Copy `examples/openshift_default.yaml` from the cloned repo to `.work/must-gather-clean/default-config.yaml`
   - Set `CONFIG_FILE=".work/must-gather-clean/default-config.yaml"` for use in obfuscation

5. **Setup Working Directory**:
   ```bash
   mkdir -p .work/must-gather-clean/
   ```

6. **Obtain must-gather-clean Binary**:

   **Method A: Download Release (Recommended)**

   a. Check if binary already exists and is executable:
      ```bash
      BINARY_PATH=".work/must-gather-clean/must-gather-clean"

      if [ -f "$BINARY_PATH" ] && [ -x "$BINARY_PATH" ]; then
          echo "Using cached binary at $BINARY_PATH"
      else
          echo "Downloading must-gather-clean binary..."
      fi
      ```

   b. Detect platform and download appropriate release:
      ```bash
      # Detect OS and architecture
      OS=$(uname -s | tr '[:upper:]' '[:lower:]')
      ARCH=$(uname -m)

      # Map architecture names
      case "$ARCH" in
          x86_64)  ARCH="amd64" ;;
          aarch64|arm64) ARCH="arm64" ;;
          *)
              echo "Unsupported architecture: $ARCH"
              exit 1
              ;;
      esac

      # Construct download URL for latest release
      RELEASE_URL="https://github.com/openshift/must-gather-clean/releases/latest/download/must-gather-clean-${OS}-${ARCH}.tar.gz"

      # Download and extract
      cd .work/must-gather-clean/

      if command -v curl &> /dev/null; then
          curl -L -o must-gather-clean.tar.gz "$RELEASE_URL"
      elif command -v wget &> /dev/null; then
          wget -O must-gather-clean.tar.gz "$RELEASE_URL"
      else
          echo "ERROR: Neither curl nor wget found. Cannot download binary."
          echo "Please install curl or wget, or build from source."
          exit 1
      fi

      # Extract binary
      tar -xzf must-gather-clean.tar.gz
      chmod +x must-gather-clean
      rm must-gather-clean.tar.gz

      # Verify download
      if [ ! -f "must-gather-clean" ]; then
          echo "ERROR: Failed to download must-gather-clean binary"
          echo "Try building from source instead."
          exit 1
      fi

      echo "Successfully downloaded must-gather-clean binary"
      ```

   **Method B: Build from Source (Alternative)**

   If download fails or user wants the latest development version:

   a. Check prerequisites:
      ```bash
      # Verify Go is installed
      if ! command -v go &> /dev/null; then
          echo "ERROR: Go is not installed"
          echo "Install from: https://go.dev/doc/install"
          exit 1
      fi

      # Verify Make is installed
      if ! command -v make &> /dev/null; then
          echo "ERROR: Make is not installed"
          exit 1
      fi

      # Verify Git is installed
      if ! command -v git &> /dev/null; then
          echo "ERROR: Git is not installed"
          exit 1
      fi
      ```

   b. Clone repository:
      ```bash
      cd .work/must-gather-clean/

      if [ ! -d "must-gather-clean-src" ]; then
          git clone https://github.com/openshift/must-gather-clean.git must-gather-clean-src
      else
          cd must-gather-clean-src
          git pull
          cd ..
      fi
      ```

   c. Build binary:
      ```bash
      cd must-gather-clean-src
      make build

      # Copy binary to working directory
      cp bin/must-gather-clean ../must-gather-clean
      cd ..

      # Verify build
      if [ ! -f "must-gather-clean" ]; then
          echo "ERROR: Failed to build must-gather-clean binary"
          exit 1
      fi

      echo "Successfully built must-gather-clean from source"
      ```

   **Set binary path for later use:**
   ```bash
   BINARY_PATH="$(pwd)/.work/must-gather-clean/must-gather-clean"
   ```

7. **Get Default Config (if needed)**:

   If using default config mode (no `--config` or `--discover`), we need the example config:
   ```bash
   # Only needed if not using custom config or discovery mode
   if [ ! -f ".work/must-gather-clean/openshift_default.yaml" ]; then
       # Download example config from repository
       curl -L -o .work/must-gather-clean/openshift_default.yaml \
           https://raw.githubusercontent.com/openshift/must-gather-clean/main/examples/openshift_default.yaml

       CONFIG_FILE=".work/must-gather-clean/openshift_default.yaml"
   fi
   ```

8. **Run must-gather-clean with Configuration**:
   ```bash
   # Get absolute paths
   MUST_GATHER_PATH=$(realpath <user-provided-must-gather-path>)
   OUTPUT_PATH=$(realpath <user-provided-output-path>)
   CONFIG_FILE_ABS=$(realpath "$CONFIG_FILE")

   # Run the obfuscation tool with the selected config
   "$BINARY_PATH" \
       -c "$CONFIG_FILE_ABS" \
       -i "$MUST_GATHER_PATH" \
       -o "$OUTPUT_PATH"
   ```

9. **Verify Output**:
   - Check that output directory was created
   - Confirm it contains obfuscated files
   - Display summary of what was processed
   - Review the generated `report.yaml` in the current directory (contains replacement statistics)

10. **Provide Results**:
   - Show the location of obfuscated artifacts
   - Show the location of the config file used
   - Remind user to verify sensitive data was removed before sharing
   - Suggest spot-checking a few files to ensure obfuscation worked as expected
   - **IMPORTANT**: Remind user NOT to share the `report.yaml` file (it contains original values)

## Error Handling

**Binary Download Failures:**
- If download fails (404, network error, etc.), offer to build from source instead
- Common issues:
  - Network connectivity problems
  - Unsupported platform (not Linux/macOS or not amd64/arm64)
  - Release not available for platform
  - curl/wget not installed
- Suggest building from source as fallback

**Missing Prerequisites (for building from source):**
- If Go is not installed, provide clear installation instructions for the user's platform
- If Make is not installed, provide installation instructions
- If Git is not installed, provide installation instructions
- Only check these if building from source

**Build Failures:**
- If `make build` fails, display the full error output
- Common issues:
  - Go version too old (need 1.19+)
  - Missing dependencies (usually auto-downloaded by Go)
  - Network issues downloading dependencies
  - Make not found
- Suggest solutions based on error type

**Python/Discovery Failures:**
- If Python 3 not found when using `--discover`, provide installation instructions
- If pyyaml not installed, suggest: `pip3 install pyyaml`
- If discovery script fails, display error and fall back to default config

**Runtime Failures:**
- If must-gather-clean fails during execution, display the error
- Common issues:
  - Invalid must-gather structure
  - Insufficient disk space
  - Permission issues
  - Invalid config file format
- Help user diagnose the specific problem

**Output Path Conflicts:**
- If output path already exists, ask user to confirm overwrite or provide new path
- Never silently overwrite existing data

## Return Value

The command outputs:

1. **Progress Messages**:
   - Status of each step (downloading/building binary, discovery analysis, obfuscating)
   - Download progress or build progress
   - Percentage progress if available from must-gather-clean

2. **Success Summary**:
   ```
   ✓ Must-gather artifacts successfully obfuscated

   Input:  /path/to/must-gather/registry-ci-openshift-org-origin-4-20-...-sha256-abc123/
   Output: /path/to/must-gather-obfuscated/

   IMPORTANT: Please verify sensitive data was removed before sharing:
   - Spot-check a few YAML files for IP addresses, hostnames, secrets
   - Review logs for sensitive information
   - Check certificate files are properly redacted

   The obfuscated must-gather is ready to share at:
   /path/to/must-gather-obfuscated/
   ```

3. **Failure Messages**:
   - Clear error description
   - Suggested remediation steps
   - Command to manually retry if needed

## Examples

1. **Basic obfuscation with default config**:
   ```
   /must-gather:obfuscate ./must-gather/registry-ci-openshift-org-origin-4-20-...-sha256-abc123/
   ```
   Uses the default OpenShift config to obfuscate IPs, MACs, and omit Secrets/ConfigMaps.
   Creates output at `./must-gather/registry-ci-openshift-org-origin-4-20-...-sha256-abc123-obfuscated/`

2. **Discovery mode - intelligent config generation**:
   ```
   /must-gather:obfuscate ./my-must-gather/ ./cleaned-must-gather/ --discover
   ```
   Scans the must-gather locally to detect:
   - Secret patterns (AWS keys, GitHub tokens, etc.)
   - Custom domain names
   - Proprietary keywords
   Generates an intelligent config and uses it for obfuscation.

3. **Use custom config file**:
   ```
   /must-gather:obfuscate ./my-must-gather/ ./cleaned-must-gather/ --config ./my-config.yaml
   ```
   Uses your own custom configuration file for obfuscation.

4. **Specify custom output path**:
   ```
   /must-gather:obfuscate ./my-must-gather/ ./cleaned-must-gather/
   ```
   Obfuscates `./my-must-gather/` and outputs to `./cleaned-must-gather/` using default config.

5. **Interactive mode (no arguments)**:
   ```
   /must-gather:obfuscate
   ```
   Prompts user for must-gather path and output location, uses default config.

## Notes

- **Privacy**: Discovery mode analysis is done ENTIRELY LOCALLY - no data is sent to external services or LLMs
- **Binary Installation**:
  - **Recommended**: Downloads pre-built binary from GitHub releases (fast, no build tools needed)
  - **Alternative**: Builds from source for latest development version
  - Binary is cached at `.work/must-gather-clean/must-gather-clean` and reused for subsequent runs
- **Platform Support**: Supports Linux and macOS on amd64 and arm64 architectures
- **Working Directory**: All temporary files are stored in `.work/must-gather-clean/` which is gitignored
- **Discovery Script**: Located at `plugins/must-gather/skills/must-gather-obfuscate/discover_config.py`
- **Config Files**: Generated configs are saved in `.work/must-gather-clean/` for review and reuse
- **Verification**: Always manually verify sensitive data was removed before sharing obfuscated must-gathers
- **Original Preserved**: The original must-gather is never modified - obfuscated version is created separately
- **Size**: Obfuscated output will be similar size to original (slightly smaller due to compression of some fields)
- **Reversibility**: Obfuscation is one-way - original data cannot be recovered from obfuscated artifacts
- **Report File**: `report.yaml` is generated in the current directory by must-gather-clean - DO NOT SHARE IT (contains original sensitive values mapping)

## Security Considerations

**Before Sharing:**
1. Spot-check obfuscated files for any remaining sensitive data
2. Look for IP addresses, hostnames, domain names, passwords
3. Review certificate data is properly redacted
4. Check custom resources for application-specific secrets

**Limitations:**
- Tool uses heuristics and may miss some edge cases
- Custom application secrets in non-standard formats may not be caught
- Always review before sharing externally

## Arguments

- **$1** (must-gather-path): Optional. Path to the must-gather directory to obfuscate. If not provided, user will be prompted.
- **$2** (output-path): Optional. Path where obfuscated must-gather should be written. If not provided, defaults to `<must-gather-path>-obfuscated`.
- **--discover**: Optional flag. Enable discovery mode to scan the must-gather locally and generate an intelligent configuration based on detected patterns.
- **--config <file>**: Optional. Path to a custom configuration file to use for obfuscation. Cannot be used with `--discover`.
