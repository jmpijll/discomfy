#!/bin/bash
# Script to push Docker image to ghcr.io
# Requires: GITHUB_TOKEN environment variable with write:packages permission

set -e

IMAGE_NAME="ghcr.io/jmpijll/discomfy"
VERSION="v2.0.0"

echo "🔐 Logging in to GitHub Container Registry..."
echo "$GITHUB_TOKEN" | docker login ghcr.io -u jmpijll --password-stdin

echo "🏷️  Tagging image as $VERSION and latest..."
docker tag discomfy:test ${IMAGE_NAME}:${VERSION}
docker tag discomfy:test ${IMAGE_NAME}:latest

echo "📤 Pushing ${IMAGE_NAME}:${VERSION}..."
docker push ${IMAGE_NAME}:${VERSION}

echo "📤 Pushing ${IMAGE_NAME}:latest..."
docker push ${IMAGE_NAME}:latest

echo "✅ Successfully pushed ${IMAGE_NAME}:${VERSION} and ${IMAGE_NAME}:latest to ghcr.io!"
echo ""
echo "View your package at: https://github.com/users/jmpijll/packages/container/discomfy"

