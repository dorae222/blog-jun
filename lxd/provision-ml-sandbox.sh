#!/bin/bash
# Provision ml-sandbox LXD container
# Run on lxd-host (hj-remote): bash lxd/provision-ml-sandbox.sh

set -euo pipefail

CONTAINER_NAME="ml-sandbox"
IMAGE="ubuntu:24.04"

echo "=== Creating LXD container: $CONTAINER_NAME ==="

# Create profile if not exists
lxc profile show $CONTAINER_NAME >/dev/null 2>&1 || \
  lxc profile create $CONTAINER_NAME

# Apply profile config
cat <<'PROFILE' | lxc profile edit $CONTAINER_NAME
name: ml-sandbox
description: ML code sandbox (4 CPU, 16GB RAM)
config:
  limits.cpu: "4"
  limits.memory: 16GB
devices:
  root:
    type: disk
    pool: default
    path: /
    size: 50GB
  eth0:
    type: nic
    network: lxdbr0
    ipv4.address: 10.10.10.32
PROFILE

# Launch container
lxc launch $IMAGE $CONTAINER_NAME --profile default --profile $CONTAINER_NAME 2>/dev/null || \
  echo "Container already exists"

# Wait for network
echo "Waiting for network..."
sleep 5

# Install Python + ML packages
echo "=== Installing Python + ML packages ==="
lxc exec $CONTAINER_NAME -- bash -c '
  apt-get update
  apt-get install -y python3 python3-venv python3-pip python3-dev
  apt-get install -y pkg-config libfreetype6-dev libpng-dev

  # matplotlib 한글 폰트 지원
  apt-get install -y fonts-noto-cjk

  # Python 패키지 (system-wide)
  pip3 install --break-system-packages \
    numpy scipy scikit-learn pandas \
    matplotlib seaborn
'

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

# Create workspace
lxc exec $CONTAINER_NAME -- mkdir -p /workspace

echo "=== Container IP ==="
lxc list $CONTAINER_NAME -c n4 --format csv

echo ""
echo "=== Next steps ==="
echo "1. Add SSH key: lxc exec $CONTAINER_NAME -- bash -c 'echo YOUR_PUBLIC_KEY >> /root/.ssh/authorized_keys'"
echo "2. Add to ~/.ssh/config:"
echo "   Host ml-sandbox"
echo "     HostName 10.10.10.32"
echo "     User root"
echo "     ProxyJump hj-remote"
echo "3. Test: ssh ml-sandbox 'python3 -c \"import matplotlib; print(matplotlib.__version__)\"'"
