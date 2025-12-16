#!/bin/bash
# Setup script for Cloudflare Tunnels (permanent HTTPS)

set -e

echo "🚀 Setting up Cloudflare Tunnels for White Agent and Green Agent"
echo ""

# Check if cloudflared is installed
if ! command -v cloudflared &> /dev/null; then
    echo "❌ cloudflared is not installed"
    echo ""
    echo "Install it with:"
    echo "  macOS: brew install cloudflared"
    echo "  Linux: sudo apt-get install cloudflared"
    echo "  Windows: Download from https://github.com/cloudflare/cloudflared/releases"
    exit 1
fi

echo "✅ cloudflared is installed"
echo ""

# Create .cloudflared directory if it doesn't exist
mkdir -p .cloudflared

echo "📋 Step 1: Login to Cloudflare"
echo "   This will open a browser window for authentication"
cloudflared tunnel login

echo ""
echo "📋 Step 2: Create named tunnel"
echo "   Creating tunnel: green-agent-tunnel"
if cloudflared tunnel create green-agent-tunnel 2>&1 | grep -q "already exists"; then
    echo "   ✅ Tunnel already exists"
else
    echo "   ✅ Tunnel created"
fi

echo ""
echo "📋 Step 3: Configure DNS"
echo ""
echo "You have two options:"
echo ""
echo "Option A: Automatic DNS (Recommended)"
echo "  cloudflared tunnel route dns green-agent-tunnel white-agent.yourdomain.com"
echo "  cloudflared tunnel route dns green-agent-tunnel green-agent.yourdomain.com"
echo ""
echo "Option B: Manual DNS"
echo "  Add CNAME records in your Cloudflare DNS dashboard:"
echo "  - white-agent.yourdomain.com -> {tunnel-id}.cfargotunnel.com"
echo "  - green-agent.yourdomain.com -> {tunnel-id}.cfargotunnel.com"
echo ""
read -p "Do you want to set up DNS automatically? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    read -p "Enter your domain (e.g., yourdomain.com): " domain
    echo "Setting up DNS for white-agent.$domain"
    cloudflared tunnel route dns green-agent-tunnel white-agent.$domain || echo "DNS route may already exist"
    echo "Setting up DNS for green-agent.$domain"
    cloudflared tunnel route dns green-agent-tunnel green-agent.$domain || echo "DNS route may already exist"
fi

echo ""
echo "📋 Step 4: Configure cloudflare-config.yml"
if [ ! -f "cloudflare-config.yml" ]; then
    echo "   Creating cloudflare-config.yml from example..."
    cp cloudflare-config.example.yml cloudflare-config.yml
fi

echo "   Please edit cloudflare-config.yml and update the hostnames to match your domain"
echo "   Current config:"
cat cloudflare-config.yml
echo ""
echo "   Replace 'yourdomain.com' with your actual domain in the hostnames"
read -p "Press Enter after you've updated the config file..."

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start the tunnels, run:"
echo "  ./start_cloudflare_tunnels.sh"
echo ""

