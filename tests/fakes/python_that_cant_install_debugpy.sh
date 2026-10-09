#!/bin/bash
# Fake python interpreter for testing debugpy installation failures.
# When called with `-c "import debugpy"`, it fails (simulating no debugpy).
# When called with `-m pip install debugpy`, it fails with specific output.

if [[ "$1" == "-c" ]]; then
  # Simulate failing to import debugpy
  exit 1
elif [[ "$2" == "pip" ]]; then
  # Simulate pip install failing with specific output
  printf "sample stdout"
  printf "sample stderr" >&2
  exit 1
else
  exit 1
fi
