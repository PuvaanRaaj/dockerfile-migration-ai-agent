#!/bin/bash

set -e


# supervisor handler
## if no value set to true
if [ -z "$POSTFIX_SUPERVISOR_AUTOSTART" ]; then
  export POSTFIX_SUPERVISOR_AUTOSTART=true
fi
if [ -z "$DNSMASQ_SUPERVISOR_AUTOSTART" ]; then
  export DNSMASQ_SUPERVISOR_AUTOSTART=true
fi

if [ "$AWS_EXECUTION_ENV" = "AWS_ECS_FARGATE" ]; then
  # Configure dnsmasq upstream server
  if [ "$DNSMASQ_SUPERVISOR_AUTOSTART" = "true" ] && [ -f /etc/dnsmasq/update_dnsmasq_upstream.sh ]; then
    echo "Running dnsmasq upstream configuration..."
    /etc/dnsmasq/update_dnsmasq_upstream.sh
  fi

  # Ensure required env vars exist
  if [ -z "$NEW_RELIC_LICENSE_KEY" ] || [ -z "$NEW_RELIC_APP_NAME" ]; then
    echo "ERROR: NEW_RELIC_LICENSE_KEY and/or NEW_RELIC_APP_NAME are not set."
    exit 1
  fi
fi

# Define paths
CLI_TARGET_PATH=$(php -i | grep conf | grep newrelic.ini | sed 's/,//g')

# Replace license key and app name
sed -i -e "s|REPLACE_WITH_REAL_KEY|$NEW_RELIC_LICENSE_KEY|g" \
       -e "s|PHP Application|$NEW_RELIC_APP_NAME|g" \
       "$CLI_TARGET_PATH"

# Enable newrelic if license key length is non-zero (not empty)
if [ -n "$NEW_RELIC_LICENSE_KEY" ]; then
  sed -i -e "s|^newrelic.enabled = false|newrelic.enabled = true|g" "$CLI_TARGET_PATH"
fi
# Replace daemon address if env var is set
if [ -n "$NEW_RELIC_DAEMON_ADDRESS" ]; then
  sed -i -e "s|^;newrelic\.daemon\.address = .*|newrelic.daemon.address = \"$NEW_RELIC_DAEMON_ADDRESS\"|g" "$CLI_TARGET_PATH"
fi

/usr/bin/supervisord -n -c /etc/supervisord.conf
