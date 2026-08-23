#!/bin/bash
# Install Caddy checkout config
set -e
echo "Installing Caddy checkout configuration..."
cp caddy-checkout.patch /etc/caddy/Caddyfile.d/checkout.conf
systemctl reload caddy
echo "Done."
