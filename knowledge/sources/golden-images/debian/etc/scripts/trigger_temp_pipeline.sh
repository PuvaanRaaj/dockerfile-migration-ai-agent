#!/bin/bash
set -e

# Required variables: ACCESS_TOKEN, GITLAB_API, TARGET_PROJECT_PATH, TARGET_BRANCH
: "${ACCESS_TOKEN:?ACCESS_TOKEN not set}"
: "${GITLAB_API:?GITLAB_API not set}"
: "${TARGET_PROJECT_PATH:?TARGET_PROJECT_PATH not set}"
: "${TARGET_BRANCH:=main}"

echo "🌐 Getting project ID for '$TARGET_PROJECT_PATH'..."

PROJECT_RESPONSE=$(curl --silent --header "PRIVATE-TOKEN: $ACCESS_TOKEN" \
  "$GITLAB_API/projects/$TARGET_PROJECT_PATH")

TARGET_PROJECT_ID=$(echo "$PROJECT_RESPONSE" | jq -r '.id')

if [ -z "$TARGET_PROJECT_ID" ]; then
  echo "❌ Failed to get project ID. Response: $PROJECT_RESPONSE"
  exit 1
fi

echo "📦 Target project ID: [$TARGET_PROJECT_ID]"

echo "🔧 Creating temporary trigger..."

TRIGGER_RESPONSE=$(curl --silent --request POST \
  --header "PRIVATE-TOKEN: $ACCESS_TOKEN" \
  --data "description=Temp Trigger $(date +%s)" \
  "$GITLAB_API/projects/$TARGET_PROJECT_ID/triggers")

TRIGGER_TOKEN=$(echo "$TRIGGER_RESPONSE" | jq -r '.token')
TRIGGER_ID=$(echo "$TRIGGER_RESPONSE" | jq -r '.id')

if [ -z "$TRIGGER_TOKEN" ] || [ -z "$TRIGGER_ID" ]; then
  echo "❌ Failed to create trigger. Response: $TRIGGER_RESPONSE"
  exit 1
fi

echo "🚀 Triggering pipeline on branch '$TARGET_BRANCH'..."

curl --silent --request POST \
  --form token="$TRIGGER_TOKEN" \
  --form ref="$TARGET_BRANCH" \
  --form "variables[DEPLOY_ENV]=production" \
  "$GITLAB_API/projects/$TARGET_PROJECT_ID/trigger/pipeline"

echo ""
echo "🧹 Cleaning up temporary trigger..."

curl --silent --request DELETE \
  --header "PRIVATE-TOKEN: $ACCESS_TOKEN" \
  "$GITLAB_API/projects/$TARGET_PROJECT_ID/triggers/$TRIGGER_ID"

echo ""
echo "✅ Pipeline triggered and trigger cleaned up."
