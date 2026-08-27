#!/usr/bin/env bash
set -euo pipefail

image=glove80-zmk-config
branch="${1:-main}"

docker build -t "$image" .
docker run --rm \
    -v "$PWD:/config" \
    -e UID="$(id -u)" \
    -e GID="$(id -g)" \
    -e BRANCH="$branch" \
    "$image"
