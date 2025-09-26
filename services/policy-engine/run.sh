#!/usr/bin/env bash
uvicorn policy_app:app --host 127.0.0.1 --port 8100 --reload
