#!/bin/bash
set -e

# 1) Capture current upstream resolvers from the image (before we change resolv.conf)
#    Keep only non-loopback IPs (VPC Resolver will be here, e.g., 10.0.0.2)
UPSTREAM_TMP="/etc/dnsmasq.upstream.conf"
: > "$UPSTREAM_TMP"
grep -E '^nameserver ' /etc/resolv.conf | awk '{print $2}' | \
  grep -Ev '^(127\.|::1)' | while read -r ns; do
    echo "nameserver $ns" >> "$UPSTREAM_TMP"
  done

# Fallback if none found (rare)
if ! grep -q '^nameserver ' "$UPSTREAM_TMP"; then
  # Common VPC resolver is "VPC_CIDR_BASE + 2", but we can't know it statically.
  # Fall back to public resolvers; dnsmasq will still cache.
  echo "nameserver 1.1.1.1" >> "$UPSTREAM_TMP"
  echo "nameserver 8.8.8.8" >> "$UPSTREAM_TMP"
fi

# 2) Point the container to dnsmasq on localhost
echo "nameserver 127.0.0.1" > /etc/resolv.conf

echo "Done updating upstream resolvers."
