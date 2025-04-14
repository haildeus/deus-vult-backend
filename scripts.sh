#!/bin/bash

set -e # Exit immediately if a command exits with a non-zero status.

if [ "$1" == "run" ]; then
  uv run -- bash -c "uvicorn app:app --reload"
elif [ "$1" == "deploy" ]; then
  if [ "$2" == "dev" ]; then
    gcloud app deploy dev.yaml
  elif [ "$2" == "prod" ]; then
    gcloud app deploy prod.yaml
  else
    echo "Error: Invalid or missing environment for deploy. Use 'dev' or 'prod'." >&2
    exit 1
  fi
else
  echo "Usage: $0 {run|deploy [dev|prod]}" >&2
  exit 1
fi
