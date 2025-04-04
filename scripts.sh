#!/bin/bash

if [ "$1" == "dev" ]; then
  uv run -- bash -c "uvicorn app:app --reload"
fi
