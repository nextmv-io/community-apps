#!/usr/env/bin bash
set -e

# Checks that APP_DIR is set.
if [[ -z "${APP_DIR}" ]]; then
    >&2 echo "❌ APP_DIR must be set"
    exit -1
fi

# Checks that APP_ID is set.
if [[ -z "${APP_ID}" ]]; then
    >&2 echo "❌ APP_ID must be set"
    exit -1
fi

# Checks that MARKETPLACE_APP_ID is set.
if [[ -z "${MARKETPLACE_APP_ID}" ]]; then
    >&2 echo "❌ MARKETPLACE_APP_ID must be set"
    exit -1
fi

# Checks that VERSION_ID is set.
if [[ -z "${VERSION_ID}" ]]; then
    >&2 echo "❌ VERSION_ID must be set"
    exit -1
fi

# Pushes app to Marketplace.
cd $APP_DIR
nextmv cloud app push \
    --app-id $APP_ID \
    --version-no
nextmv cloud version create \
    --app-id $APP_ID \
    --version-id $VERSION_ID \
    --name $VERSION_ID \
    --description "Version ${VERSION_ID}"
nextmv cloud instance create \
    --app-id $APP_ID \
    --version-id $VERSION_ID \
    --name $VERSION_ID \
    --description "Instance ${VERSION_ID}" \
    --instance-id $VERSION_ID
nextmv cloud app update \
    --app-id $APP_ID \
    --default-instance-id $VERSION_ID
nextmv cloud marketplace version create \
    --app-id $MARKETPLACE_APP_ID \
    --change-log "Version ${VERSION_ID}" \
    --partner-id "nextmv" \
    --reference-version-id $VERSION_ID \
    --version-id $VERSION_ID
