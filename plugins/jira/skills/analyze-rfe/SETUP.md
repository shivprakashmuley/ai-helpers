# Setup Guide for jira:analyze-rfe

This guide walks you through setting up your environment to use the `/jira:analyze-rfe` command.

## Overview

The `analyze-rfe` command uses Jira REST API to fetch and analyze RFE issues. Before using it, you need to configure authentication and install required dependencies.

**Estimated Setup Time:** 5-10 minutes

---

## Step 1: Get Jira Personal Access Token

### Why You Need This
The token authenticates your requests to Jira's API. Without it, the command cannot fetch RFE data.

### How to Get It

1. **Open Jira Token Page**
   - Visit: https://issues.redhat.com/secure/ViewProfile.jspa?selectedTab=com.atlassian.pats.pats-plugin:jira-user-personal-access-tokens
   - Or navigate: Jira → Profile → Personal Access Tokens

2. **Create New Token**
   - Click **"Create token"**
   - Give it a meaningful name: `Claude Code - analyze-rfe`
   - Click **"Create"**

3. **Copy Token Immediately**
   - ⚠️ **IMPORTANT**: Copy the token now - you won't be able to see it again!
   - It looks like: `ABC123def456GHI789jkl012MNO345pqr678STU901vwx234YZA567bcd890`

4. **Store Securely**
   - Save it in your password manager or secure notes
   - Do NOT commit it to git repositories

---

## Step 2: Configure Environment Variables

### Add to Shell Profile

Add these lines to your shell configuration file:

**For Bash** (`~/.bashrc` or `~/.bash_profile`):
```bash
# Jira API Configuration for Claude Code
export JIRA_PERSONAL_TOKEN="paste_your_token_here"
export JIRA_URL="https://issues.redhat.com"  # Optional, defaults to this
```

**For Zsh** (`~/.zshrc`):
```bash
# Jira API Configuration for Claude Code
export JIRA_PERSONAL_TOKEN="paste_your_token_here"
export JIRA_URL="https://issues.redhat.com"  # Optional, defaults to this
```

**For Fish** (`~/.config/fish/config.fish`):
```fish
# Jira API Configuration for Claude Code
set -x JIRA_PERSONAL_TOKEN "paste_your_token_here"
set -x JIRA_URL "https://issues.redhat.com"  # Optional
```

### Load the Configuration

After editing your shell config:

```bash
# For Bash
source ~/.bashrc

# For Zsh
source ~/.zshrc

# For Fish
source ~/.config/fish/config.fish
```

### Verify Environment Variables

Check that the variables are set:

```bash
echo $JIRA_PERSONAL_TOKEN
# Should output your token

echo $JIRA_URL
# Should output: https://issues.redhat.com
```

---

## Step 3: Install Python Dependencies

The analyze-rfe command requires Python libraries for making HTTP requests.

### Check Python Version

```bash
python3 --version
# Should be Python 3.7 or higher
```

### Install Required Libraries

```bash
pip install requests aiohttp
```

**If you don't have pip:**

```bash
# macOS
brew install python3

# Fedora/RHEL
sudo dnf install python3-pip

# Ubuntu/Debian
sudo apt install python3-pip
```

### Verify Installation

```bash
python3 -c "import requests; import aiohttp; print('Dependencies installed successfully')"
# Should output: Dependencies installed successfully
```

---

## Step 4: Verify Setup

### Test Authentication

Run this command to verify your token works:

```bash
curl -H "Authorization: Bearer $JIRA_PERSONAL_TOKEN" \
     "https://issues.redhat.com/rest/api/2/myself"
```

**Expected Output:**
```json
{
  "self": "https://issues.redhat.com/rest/api/2/user?username=your_username",
  "name": "your_username",
  "emailAddress": "your_email@redhat.com",
  "displayName": "Your Name",
  "active": true,
  ...
}
```

**If you see an error:**
- `401 Unauthorized`: Token is invalid or expired - create a new one
- `Connection refused`: Check network connectivity and VPN
- `Command not found: curl`: Install curl (`brew install curl` or `sudo dnf install curl`)

### Test Fetching an RFE

Try fetching a known RFE issue:

```bash
python3 plugins/jira/skills/analyze-rfe/scripts/fetch_rfe.py RFE-1234
```

**Expected Output:**
- JSON data for the RFE issue

**If you see an error:**
- Check the error message and follow the suggestions
- Verify you have read permissions for the RFE project

---

## Step 5: Test the analyze-rfe Command

Now you're ready to test the full command in Claude Code!

```bash
/jira:analyze-rfe RFE-1234
```

**Expected Behavior:**
1. Claude fetches the RFE from Jira
2. Parses the description and requirements
3. Searches for related work
4. Generates EPIC(s) and user stories
5. Outputs a comprehensive analysis report

---

## Troubleshooting

### Error: "JIRA_PERSONAL_TOKEN not configured"

**Solution:**
1. Verify the environment variable is set: `echo $JIRA_PERSONAL_TOKEN`
2. If empty, check you added it to the correct shell config file
3. Source the config file: `source ~/.bashrc` or `source ~/.zshrc`
4. Restart Claude Code to pick up new environment variables

### Error: "Authentication failed (HTTP 401)"

**Possible Causes:**
- Token is invalid or expired
- Token wasn't copied correctly (missing characters)

**Solution:**
1. Create a new token (Step 1)
2. Update `JIRA_PERSONAL_TOKEN` in your shell config
3. Source the config file again

### Error: "Issue not found (HTTP 404)"

**Possible Causes:**
- Issue key is incorrect (typo, wrong case)
- Issue doesn't exist
- You don't have read permissions

**Solution:**
1. Check the issue exists: https://issues.redhat.com/browse/RFE-1234
2. Verify you have read permissions for the RFE project
3. Try the curl test command from Step 4

### Error: "Connection timeout"

**Possible Causes:**
- Network connectivity issues
- VPN not connected
- Firewall blocking Jira API

**Solution:**
1. Check internet connection
2. Connect to VPN if required
3. Try accessing Jira web UI: https://issues.redhat.com
4. Check firewall/proxy settings

### Error: "requests library not installed"

**Solution:**
```bash
pip install requests aiohttp
```

If `pip` is not found:
```bash
python3 -m ensurepip
pip install requests aiohttp
```

### Error: "Invalid JQL query"

**Possible Causes:**
- Component name has special characters
- Custom field not accessible

**Solution:**
- This is typically handled by the command
- Report the issue with the specific JQL query shown

---

## Required Permissions

To use analyze-rfe effectively, you need read access to:

### Critical Projects
- ✅ **RFE** - To fetch the RFE issue itself
- ✅ **OCPBUGS** - To find related bugs (for related work discovery)

### Component-Specific Projects (Based on RFE Components)
- ⚠️ **OCPSTRAT** - For strategic epics
- ⚠️ **HOSTEDCP** - For hosted control plane work
- ⚠️ **Other component projects** - As needed

**How to Check Your Permissions:**
1. Try browsing the project in Jira: https://issues.redhat.com/browse/RFE
2. If you can see issues, you have read access
3. If you see "You do not have permission", request access from your Jira admin

**How to Request Access:**
1. Contact your Jira administrator or project lead
2. Specify which projects you need read access to
3. Mention it's for RFE analysis and planning

---

## Network Requirements

### Required Connectivity
- ✅ HTTPS access to `issues.redhat.com`
- ✅ Outbound HTTPS (port 443) allowed

### VPN Requirements (if applicable)
- Some organizations require VPN to access Jira
- Connect to VPN before running analyze-rfe

### Proxy Configuration (if needed)

If your organization uses a proxy:

```bash
# Add to shell config
export HTTP_PROXY="http://proxy.company.com:8080"
export HTTPS_PROXY="http://proxy.company.com:8080"
export NO_PROXY="localhost,127.0.0.1"
```

---

## Security Best Practices

### Protect Your Token

1. **Never commit tokens to git**
   - Add `.env` to `.gitignore`
   - Use environment variables, not config files

2. **Use project-local token files (optional)**
   ```bash
   # Create a local .env file (NOT committed)
   echo 'export JIRA_PERSONAL_TOKEN="your_token"' > ~/.jira_token
   chmod 600 ~/.jira_token

   # Source it in your shell config
   echo 'source ~/.jira_token' >> ~/.bashrc
   ```

3. **Rotate tokens regularly**
   - Create new tokens every 90 days
   - Delete old tokens from Jira

4. **Use pre-commit hooks**
   - Install [rh-pre-commit](https://source.redhat.com/departments/it/it_information_security/leaktk/leaktk_components/rh_pre_commit)
   - Scans for accidentally committed secrets

### Token Scope

Jira Personal Access Tokens have the same permissions as your user account:
- They can do anything you can do in Jira
- Store them as securely as your password
- Don't share them with others

---

## Alternative: Using .netrc (Advanced)

Instead of environment variables, you can use `~/.netrc`:

```bash
# Create ~/.netrc
cat > ~/.netrc << EOF
machine issues.redhat.com
login your_email@redhat.com
password your_jira_token
EOF

# Secure the file
chmod 600 ~/.netrc
```

The REST client will automatically use credentials from `.netrc` if `JIRA_PERSONAL_TOKEN` is not set.

---

## Quick Reference

### Environment Variables
```bash
export JIRA_PERSONAL_TOKEN="your_token"      # Required
export JIRA_URL="https://issues.redhat.com"  # Optional (default)
```

### Python Dependencies
```bash
pip install requests aiohttp
```

### Verification Commands
```bash
# Test token
curl -H "Authorization: Bearer $JIRA_PERSONAL_TOKEN" \
     "https://issues.redhat.com/rest/api/2/myself"

# Test Python dependencies
python3 -c "import requests; import aiohttp; print('OK')"

# Test fetch script
python3 plugins/jira/skills/analyze-rfe/scripts/fetch_rfe.py RFE-1234
```

### Usage
```bash
# In Claude Code
/jira:analyze-rfe RFE-1234
/jira:analyze-rfe https://issues.redhat.com/browse/RFE-1234
```

---

## Getting Help

### If you encounter issues:

1. **Check this setup guide** - Most issues are covered in Troubleshooting
2. **Verify each step** - Run the verification commands
3. **Check error messages** - They usually tell you what's wrong
4. **Review logs** - Look for detailed error output

### Support Resources

- **Plugin Issues**: https://github.com/openshift-eng/ai-helpers/issues
- **Jira Access**: Contact your Jira administrator
- **Network/VPN**: Contact your IT support

---

## Next Steps

Once setup is complete:

1. ✅ Run your first analysis: `/jira:analyze-rfe RFE-1234`
2. ✅ Review the generated breakdown
3. ✅ Use `/jira:create epic` and `/jira:create story` to create issues in Jira
4. ✅ Share feedback or report issues

Happy analyzing! 🚀
