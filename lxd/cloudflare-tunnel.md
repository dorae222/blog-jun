# Cloudflare Tunnel Setup

## On blog-server container:

```bash
# Install cloudflared
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o /usr/local/bin/cloudflared
chmod +x /usr/local/bin/cloudflared

# Login and create tunnel
cloudflared tunnel login
cloudflared tunnel create blog-jun

# Configure tunnel
cat > /etc/cloudflared/config.yml << EOF
tunnel: 079ef309-aa65-4739-a851-bdcd0a7fb14b
credentials-file: /root/.cloudflared/079ef309-aa65-4739-a851-bdcd0a7fb14b.json

ingress:
  - hostname: blog.dorae222.com
    service: http://localhost:80
  - service: http_status:404
EOF

# Install as service
cloudflared service install
systemctl enable cloudflared
systemctl start cloudflared

# Add DNS record
cloudflared tunnel route dns blog-jun blog.dorae222.com
```
