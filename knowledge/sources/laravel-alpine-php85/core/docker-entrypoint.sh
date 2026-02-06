#!/bin/bash

set -e

if [ "$AWS_EXECUTION_ENV" = "AWS_ECS_FARGATE" ]; then
  # Ensure required env vars exist
  if [ -z "$NEW_RELIC_LICENSE_KEY" ] || [ -z "$NEW_RELIC_APP_NAME" ]; then
    echo "ERROR: NEW_RELIC_LICENSE_KEY and/or NEW_RELIC_APP_NAME are not set."
    exit 1
  fi
fi

# If no license key is set, remove any New Relic ini to avoid PHP startup warnings.
if [ -z "$NEW_RELIC_LICENSE_KEY" ]; then
  rm -f /etc/php85/conf.d/newrelic.ini || true
else
  # Define paths (only when New Relic is enabled)
  CLI_TARGET_PATH=$(php -i | grep conf | grep newrelic.ini | sed 's/,//g')

  # Replace license key and app name
  sed -i -e "s|REPLACE_WITH_REAL_KEY|$NEW_RELIC_LICENSE_KEY|g" \
         -e "s|PHP Application|$NEW_RELIC_APP_NAME|g" \
         "$CLI_TARGET_PATH"

  # Enable newrelic if license key length is non-zero (not empty)
  sed -i -e "s|^newrelic.enabled = false|newrelic.enabled = true|g" "$CLI_TARGET_PATH"

  # Replace daemon address if env var is set
  if [ -n "$NEW_RELIC_DAEMON_ADDRESS" ]; then
    sed -i -e "s|^;newrelic\.daemon\.address = .*|newrelic.daemon.address = \"$NEW_RELIC_DAEMON_ADDRESS\"|g" "$CLI_TARGET_PATH"
  fi
fi


# Trigger the Laravel Artisan command
/usr/bin/php /var/www/artisan cert:fetch-decode
/usr/bin/php /var/www/artisan config:clear || true
/usr/bin/php /var/www/artisan config:cache || true

# Start supervisord in the foreground
/usr/bin/supervisord -n -c /etc/supervisord.conf
