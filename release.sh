#!/bin/bash
set -euo pipefail
IFS=$'\n\t'

API_BASE="https://api.github.com"
UPLOAD_BASE="https://uploads.github.com"
# TODO, rename this to alphapapa/solarized-everything-css
OWNER="alphapapa"
# REPO="solarized-everything-css"
REPO="solarized-everything-css"
REPO_BASE="${OWNER}/${REPO}"
TARGET_ZIP_NAME="solarized-everything.zip"

# USAGE:
# ./release.sh [tag-name] [tag-message]
#
# To upload releases, please put a github token in the GH_TOKEN env var, or run with
# GH_TOKEN="<TOKEN>" ./release.sh hello "my message"
#
# For a unofficial release: ./release.sh
#
# Dependencies: curl, jq, and git

# Check depdencies
if ! command -v curl >/dev/null 2>&1 \
       || ! command -v jq >/dev/null 2>&1 \
       || ! command -v git >/dev/null 2>&1; then
    echo "Please install curl, jq, and git to continue" >&2
    exit 1
fi

GIT_COMMIT="$(git rev-parse HEAD)"

echo "Running make..."
echo

make

mkdir -p dist

echo "zipping files..."

zip "dist/$TARGET_ZIP_NAME" -r css/

if [ -z "${GH_TOKEN:-}" ]; then
    echo "No GH_TOKEN provided, exiting"
    exit 2
fi

# Check if we have tag info
if [ -z "${1:-}" ]; then
    echo
    echo "Please provide a tag for this release" 2>&1
    exit 1
elif [ -z "${2:-}" ]; then
    echo
    echo "Please provide a tag message this release" 2>&1
    exit 1
else
    TAG="$1"
    MESSAGE="$2"
fi

echo "Creating release..."
echo

RELEASE_OBJECT="$(curl -X POST "$API_BASE/repos/$REPO_BASE/releases" \
     -H "Authorization: token $GH_TOKEN" \
     -d "{
    \"tag_name\": \"$TAG\",
    \"target_commitish\": \"$GIT_COMMIT\",
    \"name\": \"$TAG\",
    \"body\": \"$MESSAGE\",
    \"draft\": true,
    \"prerelease\": false
}")"

RELEASE_ID="$(echo "$RELEASE_OBJECT" | jq -r '.id')"

echo "Uploading release assets..."

curl -X POST "$UPLOAD_BASE/repos/$REPO_BASE/releases/$RELEASE_ID/assets?name=$TARGET_ZIP_NAME" \
     -H "Authorization: token $GH_TOKEN" \
     -H "Content-Type: application/zip" \
     --data-binary "@dist/${TARGET_ZIP_NAME}" >/dev/null

echo
echo "Release created successfuly!"
echo "Please verify and publish the draft."
