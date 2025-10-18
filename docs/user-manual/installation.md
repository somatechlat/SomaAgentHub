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

## 💻 CLI Installation

### Install the SomaAgent CLI

**Using pip:**
```bash
pip install somaagent-cli
```

**Using conda:**
```bash
conda install -c conda-forge somaagent-cli
```

**From source:**
```bash
git clone https://github.com/somatechlat/somaagent-cli
cd somaagent-cli
pip install -e .
```

### Configure CLI Access

**Set your endpoint:**
```bash
soma config set-endpoint https://your-somagenthub-domain.com
```

**Authenticate:**
```bash
soma auth login
# Follow the prompts to enter credentials
```

**Verify connection:**
```bash
soma status
# Should show: Connected to SomaAgentHub v1.x.x
```

---

## 🔧 Client Configuration

### Environment Variables

Set these in your shell profile (`.bashrc`, `.zshrc`):

```bash
# SomaAgentHub Configuration
export SOMA_ENDPOINT="https://your-somagenthub-domain.com"
export SOMA_API_KEY="your-api-key"  # If using API key auth
export SOMA_PROJECT="default"       # Default project workspace
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

## 🔐 Authentication Methods

### OAuth/SSO (Recommended)
```bash
soma auth login --method oauth
# Opens browser for SSO authentication
```

### API Key
```bash
soma auth login --method api-key --key YOUR_API_KEY
```

### Basic Authentication
```bash
soma auth login --method basic --username your-username
# Prompts for password
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
# Test basic connectivity
soma ping

# List available wizards
soma wizards list

# Check your permissions
soma auth whoami

# View system status
soma status --verbose
```

### API Test
```bash
# Test API access directly
curl -H "Authorization: Bearer YOUR_TOKEN" \
     https://your-somagenthub-domain.com/health

# Expected response: {"status": "healthy"}
```

---

## 🔧 Troubleshooting

### Common Issues

**Connection Refused:**
```bash
# Check if service is running
soma status
# Verify endpoint URL
soma config get-endpoint
```

**Authentication Failed:**
```bash
# Clear cached credentials
soma auth logout
# Re-authenticate
soma auth login
```

**Permission Denied:**
```bash
# Check your user permissions
soma auth whoami
# Contact administrator for role assignment
```

### Network Issues

**Firewall/Proxy:**
- Ensure port 10000 (or your custom port) is accessible
- Configure proxy settings if required:
```bash
export HTTPS_PROXY=http://your-proxy:8080
soma config set-proxy http://your-proxy:8080
```

**SSL Certificate Issues:**
```bash
# For self-signed certificates (development only)
soma config set-verify-ssl false
```

---

## 📞 Getting Help

**Check System Status:**
```bash
soma status --health-check
```

**View Logs:**
```bash
soma logs --level debug
```

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