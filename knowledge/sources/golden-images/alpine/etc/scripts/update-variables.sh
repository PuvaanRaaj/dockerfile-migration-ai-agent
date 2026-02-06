#!/bin/bash
set -e

# === CONFIGURATION ===
GITLAB_API="${CI_API_V4_URL}"
ACCESS_TOKEN="${ACCESS_TOKEN:-your_gitlab_access_token}"  # fallback if not passed from CI/CD
TARGET_BRANCH="${TARGET_BRANCH:-main}" # Default to 'main' if not provided

echo "GITLAB_API (inside script): $GITLAB_API"
echo "ACCESS_TOKEN: $ACCESS_TOKEN"
echo "TARGET_BRANCH: $TARGET_BRANCH"

# Add validation for variables.txt
if [ ! -f variables.txt ]; then
  echo "Error: variables.txt not found! Please create this file with your CI/CD variables."
  exit 1
fi

# === VARIABLE LIST ===
# Format: PROJECT_PATH|KEY|VALUE|PROTECTED|MASKED
# Note: PROJECT_PATH must be URL-encoded (e.g., mygroup%2Fmyproject)
VARIABLES=()
while IFS= read -r line; do
  VARIABLES+=("$line")
done < variables.txt

# === FUNCTION TO UPDATE VARIABLE ===
update_variable() {
  local PROJECT="$1"
  local KEY="$2"
  local VALUE="$3"
  local PROTECTED="$4"
  local MASKED="$5"

  RESPONSE=$(curl --silent --write-out "HTTPSTATUS:%{http_code}" -X PUT "$GITLAB_API/projects/$PROJECT/variables/$KEY" \
    --header "PRIVATE-TOKEN: $ACCESS_TOKEN" \
    --data-urlencode "value=$VALUE" \
    --data "protected=$PROTECTED" \
    --data "masked=$MASKED")

  BODY=$(echo "$RESPONSE" | sed -e 's/HTTPSTATUS\:.*//g')
  STATUS=$(echo "$RESPONSE" | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')

  if [ "$STATUS" -eq 200 ]; then
    echo "✅ [$PROJECT] Updated '$KEY'"
    chmod +x "$(dirname "$0")"/trigger_temp_pipeline.sh
    ACCESS_TOKEN="$ACCESS_TOKEN" GITLAB_API="$GITLAB_API" TARGET_PROJECT_PATH="$PROJECT" TARGET_BRANCH="$TARGET_BRANCH" "$(dirname "$0")"/trigger_temp_pipeline.sh
  elif [ "$STATUS" -eq 404 ]; then
    echo "⚠️  [$PROJECT] '$KEY' not found. Creating..."
    create_variable "$PROJECT" "$KEY" "$VALUE" "$PROTECTED" "$MASKED"
  else
    echo "❌ [$PROJECT] Failed to update '$KEY' (HTTP $STATUS): $BODY"
    exit 1
  fi
}

# === FUNCTION TO CREATE VARIABLE ===
create_variable() {
  local PROJECT="$1"
  local KEY="$2"
  local VALUE="$3"
  local PROTECTED="$4"
  local MASKED="$5"

  RESPONSE=$(curl --silent --write-out "HTTPSTATUS:%{http_code}" -X POST "$GITLAB_API/projects/$PROJECT/variables" \
    --header "PRIVATE-TOKEN: $ACCESS_TOKEN" \
    --data-urlencode "key=$KEY" \
    --data-urlencode "value=$VALUE" \
    --data "protected=$PROTECTED" \
    --data "masked=$MASKED")

  BODY=$(echo "$RESPONSE" | sed -e 's/HTTPSTATUS\:.*//g')
  STATUS=$(echo "$RESPONSE" | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')

  if [ "$STATUS" -eq 201 ]; then
    echo "✅ [$PROJECT] Created '$KEY'"
    chmod +x "$(dirname "$0")"/trigger_temp_pipeline.sh
    ACCESS_TOKEN="$ACCESS_TOKEN" GITLAB_API="$GITLAB_API" TARGET_PROJECT_PATH="$PROJECT" TARGET_BRANCH="$TARGET_BRANCH" "$(dirname "$0")"/trigger_temp_pipeline.sh
  else
    echo "❌ [$PROJECT] Failed to create '$KEY' (HTTP $STATUS): $BODY"
    exit 1
  fi
}

# === FUNCTION TO URL ENCODE STRING ===
urlencode() {
    local string="$1"
    local strlen=${#string}
    local encoded_string=""
    local pos c o
    for (( pos=0 ; pos<strlen ; pos++ )); do
        c=${string:$pos:1}
        case "$c" in
            [-._~0-9a-zA-Z] ) o="${c}" ;;
            * )               printf -v o '%%%02x' "'$c"
        esac
        encoded_string+="${o}"
    done
    echo "${encoded_string}"
}


# === MAIN LOOP ===
echo "🔁 Starting CI/CD variable updates..."
for VAR in "${VARIABLES[@]}"; do
  IFS='|' read -r PROJECT KEY VALUE PROTECTED MASKED <<< "$VAR"
  # URL encode the project path
  ENCODED_PROJECT=$(urlencode "$PROJECT")
  update_variable "$ENCODED_PROJECT" "$KEY" "$VALUE" "${PROTECTED:-0}" "${MASKED:-0}"
done
