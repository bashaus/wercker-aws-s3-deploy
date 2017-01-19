#!/bin/bash

# Property: aws-access-key-id
# Check if the Access Key ID exists
if [[ -z "$WERCKER_AWS_S3_DEPLOY_AWS_ACCESS_KEY_ID" ]];
then
  fail "Property aws-access-key-id or environment variable AWS_ACCESS_KEY_ID required"
fi

# Property: aws-secret-access-key
# Check if the Secret Access Key exists
if [[ -z "$WERCKER_AWS_S3_DEPLOY_AWS_SECRET_ACCESS_KEY" ]];
then
  fail "Property aws-secret-access-key or environment variable AWS_SECRET_ACCESS_KEY required"
fi

# Property: aws-region
# Check if the Region exists
if [[ -z "$WERCKER_AWS_S3_DEPLOY_AWS_REGION" ]];
then
  fail "Property aws-region or environment variable AWS_DEFAULT_REGION required"
fi

# Property: target-bucket
# Ensure that a taget-bucket has been provided
if [[ ! -n "$WERCKER_AWS_S3_DEPLOY_TARGET_BUCKET" ]];
then
  fail "Property target-bucket must be defined"
fi

# Property: configuration-file
# Ensure that a taget-bucket has been provided
if [[ ! -n "$WERCKER_AWS_S3_DEPLOY_CONFIGURATION_FILE" ]];
then
  fail "Property configuration-file must be defined"
fi

# Task: S3 upload
# Offload to the python script
($WERCKER_STEP_ROOT/dist/run/run)
WERCKER_AWS_S3_DEPLOY_RESULT=$?

# Task: Response
if [ "$WERCKER_AWS_S3_DEPLOY_RESULT" -eq 0 ]; then
  success "ok"
else
  fail "there was a problem uploading files"
fi
