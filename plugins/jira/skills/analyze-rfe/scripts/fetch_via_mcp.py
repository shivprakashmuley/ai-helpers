#!/usr/bin/env python3
"""
Fetch Jira issue via MCP server
"""

import json
import sys
import requests

def fetch_issue_via_mcp(issue_key):
    """Fetch issue using MCP server"""

    # MCP server endpoint
    mcp_url = "http://localhost:8080"

    # First, establish a session
    session_response = requests.get(f"{mcp_url}/sse", stream=True, timeout=5)

    # Parse the endpoint from SSE
    for line in session_response.iter_lines():
        if line:
            line = line.decode('utf-8')
            if line.startswith('data: '):
                endpoint = line[6:].strip()
                break

    # Now make the tool call
    messages_url = f"{mcp_url}{endpoint}"

    # Prepare the MCP request
    mcp_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "jira_get_issue",
            "arguments": {
                "issue_key": issue_key,
                "fields": "*all"
            }
        }
    }

    # Make the request
    response = requests.post(
        messages_url,
        json=mcp_request,
        headers={"Content-Type": "application/json"},
        timeout=30
    )

    if response.status_code == 200:
        result = response.json()
        return result
    else:
        print(f"Error: HTTP {response.status_code}")
        print(response.text)
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: fetch_via_mcp.py <issue-key>")
        sys.exit(1)

    issue_key = sys.argv[1]
    result = fetch_issue_via_mcp(issue_key)

    print(json.dumps(result, indent=2))
