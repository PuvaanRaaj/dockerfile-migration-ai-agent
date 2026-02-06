#!/bin/bash
set -e

# Inside .gitlab-ci.yml
# create_image_tag_issue_notification:
#   stage: production
#   image: curlimages/curl:latest # A lightweight image with curl
#   variables:
#     GITLAB_API: "https://${CI_SERVER_HOST}/api/v4"
#     ACCESS_TOKEN: "${ISSUE_CREATION_ACCESS_TOKEN}" # Define this in your CI/CD variables with API scope
#     NEW_IMAGE_TAG: "${CI_APPLICATION_TAG}"
#     ISSUE_ASSIGNEE_IDS: "${ISSUE_ASSIGNEE_IDS}" # Optional: Comma-separated user IDs to assign the issue to
#   before_script:
#     - chmod +x create-issue-notification.sh
#   script:
#     - ./create-issue-notification.sh

echo "Creating issues for image tag: $NEW_IMAGE_TAG"

if [ ! -f repos_to_create_issue.txt ]; then
  echo "Error: repos_to_create_issue.txt not found!"
  exit 1
fi

while IFS= read -r line; do
  IFS='|' read -r PROJECT KEY <<< "$line"
  ENCODED_PROJECT=$(echo "$PROJECT" | sed 's|/|%2F|g') # URL-encode project path
  ISSUE_TITLE="Action Required: Update SERVER_IMAGE_TAG for production to ${NEW_IMAGE_TAG}"
  ISSUE_DESCRIPTION="A new image tag has been generated for production deployment:

**\`${NEW_IMAGE_TAG}\`**

Please update the \`SERVER_IMAGE_TAG\` variable in the following repository:

**\`$PROJECT\`**

Once updated, proceed with the deployment to production to ensure the system runs the latest server image."
  LABELS="Type::enhancement,Severity::2 - Medium,P2,Pillar::Internal"

  CURL_DATA_PARAMS=(
    "--data-urlencode" "title=${ISSUE_TITLE}"
    "--data-urlencode" "description=${ISSUE_DESCRIPTION}"
    "--data-urlencode" "labels=${LABELS}"
  )

  if [ -n "$ISSUE_ASSIGNEE_IDS" ]; then
    CURL_DATA_PARAMS+=( "--data-urlencode" "assignee_id=${ISSUE_ASSIGNEE_IDS}" )
  fi

  echo "Attempting to create issue in project: $PROJECT ($ENCODED_PROJECT)"
  RESPONSE=$(curl -s --write-out "\n%{http_code}" \
    --request POST \
    --header "PRIVATE-TOKEN: ${ACCESS_TOKEN}" \
    "${CURL_DATA_PARAMS[@]}" \
    "${GITLAB_API}/projects/${ENCODED_PROJECT}/issues")

  HTTP_STATUS=$(echo "$RESPONSE" | tail -n1)
  BODY=$(echo "$RESPONSE" | sed '$d')

  if [ "$HTTP_STATUS" -eq 201 ]; then
    echo "✅ Successfully created issue in $PROJECT"
  else
    echo "❌ Failed to create issue in $PROJECT (HTTP $HTTP_STATUS): $BODY"
    exit 1
  fi
done < repos_to_create_issue.txt 
