#!/bin/bash

# Get the last tag
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null)

if [ -z "$LAST_TAG" ]; then
    echo "No tags found. Retrieving all commits."
    LOG_RANGE="HEAD"
else
    echo "Generating changelog from last tag: $LAST_TAG"
    LOG_RANGE="$LAST_TAG..HEAD"
fi

# Retrieve commit messages excluding merge commits and format them with author names and stripped email domain as nickname
CHANGELOG=$(git log --pretty=format:"- %s by %an, @%ae)" --no-merges $LOG_RANGE | sed -E 's/@([^@]+)@([^@]+)\..*/@\1/')

# Output the changelog
if [ -n "$CHANGELOG" ]; then
    echo "# Changelog"
    echo "
## Changes since $LAST_TAG"
    echo "$CHANGELOG"
else
    echo "No new commits since last tag."
fi
