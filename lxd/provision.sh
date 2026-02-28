#!/bin/bash
# Provision blog-server LXD container
# Run on lxd-host: bash lxd/provision.sh

set -euo pipefail

CONTAINER_NAME="blog-server"
IMAGE="ubuntu:24.04"

echo "=== Creating LXD container: $CONTAINER_NAME ==="

# Create container
lxc launch $IMAGE $CONTAINER_NAME --profile default --profile blog-server 2>/dev/null || \
  echo "Container already exists"

# Wait for network
echo "Waiting for network..."
sleep 5

# Install Docker CE
echo "=== Installing Docker ==="
lxc exec $CONTAINER_NAME -- bash -c '
  apt-get update
  apt-get install -y ca-certificates curl
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
  chmod a+r /etc/apt/keyrings/docker.asc

  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
    https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
    tee /etc/apt/sources.list.d/docker.list > /dev/null

  apt-get update
  apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
'

# Create app directory
lxc exec $CONTAINER_NAME -- mkdir -p /opt/blog-jun

# Setup SSH
echo "=== Setting up SSH ==="
lxc exec $CONTAINER_NAME -- bash -c '
  apt-get install -y openssh-server
  sed -i "s/#PasswordAuthentication yes/PasswordAuthentication no/" /etc/ssh/sshd_config
  mkdir -p /root/.ssh
  chmod 700 /root/.ssh
  systemctl enable ssh
  systemctl start ssh
'

# Install git
echo "=== Installing git ==="
lxc exec $CONTAINER_NAME -- apt-get install -y git

# Install cloudflared
echo "=== Installing cloudflared ==="
lxc exec $CONTAINER_NAME -- bash -c '
  curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 \
    -o /usr/local/bin/cloudflared
  chmod +x /usr/local/bin/cloudflared
'

# Install Node.js 20 + Claude Code
echo "=== Installing Node.js 20 + Claude Code ==="
lxc exec $CONTAINER_NAME -- bash -c '
  curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
  apt-get install -y nodejs
  npm install -g @anthropic-ai/claude-code
'

echo "=== Container IP ==="
lxc list $CONTAINER_NAME -c n4 --format csv

echo ""
echo "=== Next steps ==="
echo "1. Add SSH key: lxc exec $CONTAINER_NAME -- bash -c 'echo YOUR_PUBLIC_KEY >> /root/.ssh/authorized_keys'"
echo "2. Clone repo: cd /opt/blog-jun && git clone https://github.com/dorae222/blog-jun.git ."
echo "3. Setup .env: cp .env.example .env && vim .env"
echo "4. Setup Cloudflare Tunnel (see lxd/cloudflare-tunnel.md)"
echo "5. Configure SSH ProxyJump in ~/.ssh/config"
