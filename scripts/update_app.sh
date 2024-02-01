#!/bin/bash
set -e

# ================= README =================
# Updates an app to the desired version.

# Required exports.
# APP: the name of the app to update.
# VERSION: the version to update to.

# ================= Checks =================
# Checks that APP is set.
echo "🐰 Checking the value of APP"
if [[ -z "${APP}" ]]; then
    echo "❌ APP must be set"
    exit -1
fi

# Checks that VERSION is set.
echo "🐰 Checking the value of VERSION"
if [[ -z "${VERSION}" ]]; then
    echo "❌ VERSION must be set"
    exit -1
fi

# ================= App info =================
# Get the info of the app from the configuration file.
WORFKLOW_CONFIGURATION="workflow-configuration.yml"
INFO=$(yq '.apps[] | select(.name == strenv(APP))' workflow-configuration.yml)
echo "🐰 App info:"
echo "$INFO" | yq .

# ================= Directory =================
# Change to the APP directory.
cd "$(dirname "$0")/.."
echo "🐰 Current dir is: $(pwd)"
echo "🐰 Changing to dir $APP"
cd $APP

# ================= Update =================
# Update the VERSION file to the VERSION.
OLD=$(cat VERSION)
echo "🐰 Updating the VERSION file from $OLD to $VERSION"
echo $VERSION > VERSION

# If the app is a Go app, update the go.mod file.
TYPE=$(echo "$INFO" | yq .type)
echo "🐰 App type is $TYPE"
if [[ $TYPE == "go" ]]; then
    SDK_VERSION=$(echo "$INFO" | yq .sdk_version)
    echo "🐰 SDK version is $SDK_VERSION"
    echo "🐰 Updating the go.mod file"
    go get github.com/nextmv-io/sdk@$SDK_VERSION
    go mod tidy
fi
