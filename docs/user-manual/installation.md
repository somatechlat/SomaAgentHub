# Installation & Access

**How to access and set up SomaAgentHub for end users**

> This guide covers accessing an existing SomaAgentHub deployment, installing client tools, and initial configuration.

---

## 📋 Prerequisites

- **Network Access** to your SomaAgentHub instance
- **User Account** provided by your administrator
- **Modern Web Browser** (Chrome, Firefox, Safari, Edge)
- **Python 3.8+** (for CLI tools)

---

## 🌐 Web Interface Access

### 1. Access the Platform

Navigate to your SomaAgentHub instance:
```
https://your-somagenthub-domain.com
```

Or if using direct IP/port:
```
http://your-server-ip:10000
```

### 2. Login

1. **Enter your credentials** provided by your administrator
2. **Complete any required authentication** (SSO, MFA)
3. **Accept terms of service** if prompted
4. **Verify dashboard access** - you should see the main interface

### 3. Initial Setup

**Profile Configuration:**
1. Click your profile icon (top right)
2. Update your display name and preferences
3. Configure notification settings
4. Set your default project workspace

---

## 💻 CLI Access

### Using the SomaAgent CLI

The CLI is included in this repository and talks to the Gateway API.

```bash
# Clone the repository (if you haven't already)
git clone https://github.com/your-org/somaAgentHub
cd somaAgentHub

# Install dependencies for the Python SDK used by the CLI
pip install -r sdk/python/requirements.txt

# Authenticate and try a chat
./cli/soma login
./cli/soma chat "Hello, how can you help?"
./cli/soma capsule list
```

### Available Commands

**Authentication:**
```bash
./cli/soma login                    # Authenticate with API key
```

**Interaction:**
```bash
./cli/soma chat "message"           # Send chat message
./cli/soma capsule list             # List available capsules
./cli/soma agent create "name"      # Create new agent
./cli/soma workflow start type      # Start workflow
```

---

## 🔧 Client Configuration

### Environment Variables

The CLI uses the SDK environment variables below (matching the SDK code):

```bash
# SomaAgentHub CLI/SDK Configuration
export SOMAAGENT_API_URL="http://localhost:10000"  # Gateway API
export SOMAAGENT_API_KEY="your-api-key"           # If using API key auth
```

### Configuration File

Create `~/.soma/config.yaml`:
```yaml
endpoint: https://your-somagenthub-domain.com
auth:
  method: oauth  # or 'api_key', 'basic'
  token_file: ~/.soma/token
defaults:
  project: default
  timeout: 300
  format: json
preferences:
  editor: vim
  pager: less
  color: true
```

---

## 🔐 Authentication

Use the repository CLI to authenticate:

```bash
./cli/soma login   # prompts for API key, saves to ~/.somaagent/credentials
```

---

## 📱 Mobile Access

### Progressive Web App (PWA)

1. **Open SomaAgentHub in mobile browser**
2. **Tap "Add to Home Screen"** when prompted
3. **Launch from home screen** for app-like experience

### Mobile-Optimized Features

- **Responsive dashboard** - View workflow status
- **Push notifications** - Approval requests and updates  
- **Quick actions** - Approve/reject workflows
- **Offline viewing** - Cached workflow history

---

## 🧪 Verify Installation

### Web Interface Test
1. **Login to the web interface**
2. **Navigate to "Wizards"**
3. **Click "Test Connection"**
4. **Verify green status indicators**

### CLI Test
```bash
# Send a chat message via the gateway
./cli/soma chat "Hello from CLI"

# List available capsules (if task capsule service is enabled)
./cli/soma capsule list
```

### API Test
```bash
# Test Gateway API health directly (Gateway exposes /healthz)
curl -s http://localhost:10000/healthz | jq

# Expected response contains status: ok|degraded and checks
# { "status": "ok", "checks": { "kafka": false, "auth": true, "redis": true } }
```

---

## 🔧 Troubleshooting

### Common Issues

**Connection Refused:**
```bash
# Verify endpoint URL
echo $SOMAAGENT_API_URL
# Check gateway health endpoint
curl -v http://localhost:10000/healthz
```

**Authentication Failed:**
```bash
# Clear cached credentials
rm -f ~/.somaagent/credentials
# Re-authenticate
./cli/soma login
```

**Permission Denied:**
```bash
# Ensure your token includes required capabilities (ask your admin)
# Identity service: GET /v1/users/<id>/capabilities
# Contact administrator for role assignment
```

### Network Issues

**Firewall/Proxy:**
- Ensure port 10000 (or your custom port) is accessible
- Configure proxy settings if required:
```bash
export HTTPS_PROXY=http://your-proxy:8080
export NO_PROXY=localhost,127.0.0.1
```

**SSL Certificate Issues:**
```bash
# For self-signed certificates (development only)
export REQUESTS_CA_BUNDLE=/path/to/ca.pem
```

---

## 📞 Getting Help

**Check System Status:**
Ask your administrator for the operational dashboard URL or check health endpoints directly (e.g., `curl http://localhost:10000/healthz`).

**View Logs:**
Use your platform’s logging solution (e.g., Grafana/Loki) or `kubectl logs` for Kubernetes deployments.

**Contact Support:**
- **Internal IT**: Contact your system administrator
- **Documentation**: Check the [FAQ](faq.md) for common issues
- **Community**: Join the user forum for peer support

---

## ✅ Next Steps

Once installation is complete:

1. **Complete the [Quick Start Tutorial](quick-start-tutorial.md)**
2. **Explore [Core Features](features/index.md)**
3. **Join training sessions** offered by your organization
4. **Connect with other users** in your organization

---

**Installation complete! You're ready to start orchestrating autonomous agent workflows.**
