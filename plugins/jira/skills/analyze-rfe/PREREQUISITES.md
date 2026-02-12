# Prerequisites Checklist for jira:analyze-rfe

Quick reference for what you need before running `/jira:analyze-rfe`.

## ✅ Pre-flight Checklist

Before running the command, verify each item:

### 1. Jira Personal Access Token

- [ ] Token created at: https://issues.redhat.com/secure/ViewProfile.jspa
- [ ] Token copied and stored securely
- [ ] Environment variable set: `JIRA_PERSONAL_TOKEN`
- [ ] Token works (test with curl command below)

**Test Command:**
```bash
curl -H "Authorization: Bearer $JIRA_PERSONAL_TOKEN" \
     "https://issues.redhat.com/rest/api/2/myself"
```

---

### 2. Environment Variables

- [ ] `JIRA_PERSONAL_TOKEN` is set
- [ ] `JIRA_URL` is set (optional, defaults to https://issues.redhat.com)
- [ ] Variables added to shell config (~/.bashrc or ~/.zshrc)
- [ ] Shell config reloaded (run `source ~/.bashrc`)

**Verify:**
```bash
echo $JIRA_PERSONAL_TOKEN  # Should show your token
echo $JIRA_URL             # Should show: https://issues.redhat.com
```

---

### 3. Python Dependencies

- [ ] Python 3.7+ installed
- [ ] `requests` library installed
- [ ] `aiohttp` library installed

**Install:**
```bash
pip install requests aiohttp
```

**Verify:**
```bash
python3 -c "import requests; import aiohttp; print('✓ Dependencies OK')"
```

---

### 4. Jira Permissions

- [ ] Read access to **RFE project**
- [ ] Read access to **OCPBUGS project** (for related work)
- [ ] Read access to relevant component projects (OCPSTRAT, HOSTEDCP, etc.)

**Test Access:**
```bash
# Can you view an RFE issue?
curl -H "Authorization: Bearer $JIRA_PERSONAL_TOKEN" \
     "https://issues.redhat.com/rest/api/2/issue/RFE-1234"
```

---

### 5. Network Access

- [ ] Internet connectivity available
- [ ] Access to https://issues.redhat.com
- [ ] VPN connected (if required by your organization)
- [ ] No firewall blocking HTTPS to Jira
- [ ] Proxy configured (if needed)

**Test Connectivity:**
```bash
curl -I https://issues.redhat.com
# Should return: HTTP/2 200
```

---

## 🚀 Quick Setup (5 minutes)

If starting from scratch:

```bash
# 1. Get token (manual step via browser)
# Visit: https://issues.redhat.com/secure/ViewProfile.jspa
# Click: "Create token" → Copy token

# 2. Set environment variable (replace YOUR_TOKEN)
echo 'export JIRA_PERSONAL_TOKEN="YOUR_TOKEN"' >> ~/.bashrc
source ~/.bashrc

# 3. Install dependencies
pip install requests aiohttp

# 4. Test it works
curl -H "Authorization: Bearer $JIRA_PERSONAL_TOKEN" \
     "https://issues.redhat.com/rest/api/2/myself"

# 5. Try analyze-rfe
# In Claude Code: /jira:analyze-rfe RFE-1234
```

---

## 🔧 Troubleshooting Quick Fixes

### "JIRA_PERSONAL_TOKEN not configured"
```bash
# Check if set
echo $JIRA_PERSONAL_TOKEN

# If empty, add to shell config
echo 'export JIRA_PERSONAL_TOKEN="your_token"' >> ~/.bashrc
source ~/.bashrc
```

### "Authentication failed (HTTP 401)"
```bash
# Token may be invalid - create a new one
# Visit: https://issues.redhat.com/secure/ViewProfile.jspa
# Create new token → Update environment variable
```

### "Issue not found (HTTP 404)"
```bash
# Check issue exists
open https://issues.redhat.com/browse/RFE-1234

# Check you have read permissions
curl -H "Authorization: Bearer $JIRA_PERSONAL_TOKEN" \
     "https://issues.redhat.com/rest/api/2/issue/RFE-1234"
```

### "requests library not installed"
```bash
pip install requests aiohttp
```

### "Connection timeout"
```bash
# Check network
ping issues.redhat.com

# Check VPN (if required)
# Connect to VPN and retry
```

---

## 📋 Required Environment Variables

| Variable | Required? | Default | Purpose |
|----------|-----------|---------|---------|
| `JIRA_PERSONAL_TOKEN` | ✅ Yes | None | Authenticates API requests |
| `JIRA_URL` | ⚠️ Optional | `https://issues.redhat.com` | Jira instance URL |

---

## 📦 Required Python Libraries

| Library | Version | Purpose |
|---------|---------|---------|
| `requests` | >= 2.25.0 | HTTP client for Jira API |
| `aiohttp` | >= 3.7.0 | Async HTTP for parallel requests |

---

## 🔐 Required Jira Permissions

| Project/Access | Why Needed |
|----------------|------------|
| **RFE** (read) | Fetch the RFE issue being analyzed |
| **OCPBUGS** (read) | Find related bugs for context |
| **Component projects** (read) | Discover related epics and work |

Request access from your Jira administrator if missing.

---

## 🌐 Network Requirements

| Requirement | Details |
|-------------|---------|
| **Protocol** | HTTPS (port 443) |
| **Host** | `issues.redhat.com` |
| **VPN** | May be required (depends on org) |
| **Proxy** | Configure if needed |
| **Firewall** | Must allow outbound HTTPS |

---

## ✅ Verification Script

Run this to check all prerequisites:

```bash
#!/bin/bash
echo "Checking jira:analyze-rfe prerequisites..."
echo ""

# Check environment variables
echo "1. Environment Variables:"
if [ -n "$JIRA_PERSONAL_TOKEN" ]; then
    echo "   ✓ JIRA_PERSONAL_TOKEN is set"
else
    echo "   ✗ JIRA_PERSONAL_TOKEN is NOT set"
    echo "     Fix: export JIRA_PERSONAL_TOKEN=\"your_token\""
fi

if [ -n "$JIRA_URL" ]; then
    echo "   ✓ JIRA_URL is set to: $JIRA_URL"
else
    echo "   ⚠ JIRA_URL not set (will use default: https://issues.redhat.com)"
fi

echo ""

# Check Python dependencies
echo "2. Python Dependencies:"
if python3 -c "import requests" 2>/dev/null; then
    echo "   ✓ requests library installed"
else
    echo "   ✗ requests library NOT installed"
    echo "     Fix: pip install requests"
fi

if python3 -c "import aiohttp" 2>/dev/null; then
    echo "   ✓ aiohttp library installed"
else
    echo "   ✗ aiohttp library NOT installed"
    echo "     Fix: pip install aiohttp"
fi

echo ""

# Check network connectivity
echo "3. Network Connectivity:"
if curl -s -I https://issues.redhat.com | grep -q "HTTP/2 200"; then
    echo "   ✓ Can reach issues.redhat.com"
else
    echo "   ✗ Cannot reach issues.redhat.com"
    echo "     Check: VPN connection, firewall, network"
fi

echo ""

# Check Jira authentication
echo "4. Jira Authentication:"
if [ -n "$JIRA_PERSONAL_TOKEN" ]; then
    RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" \
               -H "Authorization: Bearer $JIRA_PERSONAL_TOKEN" \
               "https://issues.redhat.com/rest/api/2/myself")

    if [ "$RESPONSE" = "200" ]; then
        echo "   ✓ Token is valid and working"
    else
        echo "   ✗ Token authentication failed (HTTP $RESPONSE)"
        echo "     Fix: Create new token at https://issues.redhat.com/secure/ViewProfile.jspa"
    fi
else
    echo "   ⚠ Skipped (no token set)"
fi

echo ""
echo "Prerequisite check complete!"
echo ""
echo "If all checks passed (✓), you're ready to run:"
echo "  /jira:analyze-rfe RFE-1234"
echo ""
echo "If any checks failed (✗), follow the fix instructions above."
```

**Save this as `check_prerequisites.sh` and run:**
```bash
chmod +x check_prerequisites.sh
./check_prerequisites.sh
```

---

## 📚 Additional Resources

- **Full Setup Guide**: [SETUP.md](SETUP.md)
- **Command Documentation**: [../../commands/analyze-rfe.md](../../commands/analyze-rfe.md)
- **Implementation Details**: [SKILL.md](SKILL.md)
- **Jira API Documentation**: https://developer.atlassian.com/cloud/jira/platform/rest/v2/

---

## 🆘 Getting Help

### Common Issues
- Most issues are covered in [SETUP.md](SETUP.md) → Troubleshooting section
- Run the verification script above to diagnose problems

### Support Channels
- **Plugin Issues**: https://github.com/openshift-eng/ai-helpers/issues
- **Jira Access**: Your Jira administrator
- **Network/VPN**: Your IT support team

---

**Last Updated:** 2025-02-12
