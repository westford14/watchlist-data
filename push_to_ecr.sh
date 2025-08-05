#!/bin/bash

# Variables
AWS_REGION="eu-north-1"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REPO_NAME="watchlist-data-cli"
IMAGE_TAG="latest"

# Full image URI
IMAGE_URI="$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$REPO_NAME:$IMAGE_TAG"

echo "Logging in to ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin "$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"

echo "Building Docker image..."
docker build -t $REPO_NAME .

echo "Tagging image with ECR URI..."
docker tag $REPO_NAME:latest $IMAGE_URI

echo "Pushing image to ECR..."
docker push $IMAGE_URI

echo "Done. Image pushed to $IMAGE_URI"