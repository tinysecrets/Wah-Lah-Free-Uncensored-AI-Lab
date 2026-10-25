#!/usr/bin/env bash
set -euo pipefail
ROOT="$(dirname -- "$0")"
ROOT="$(cd -- "$ROOT" && pwd)"
cd "$ROOT"
if [ "$#" -gt 0 ]; then arg="$1"; else arg=""; fi
case "$arg" in
  --cli)
    shift
    exec /usr/bin/python3 "$ROOT/app/lab.py" "$@"
    ;;
  --setup-key|--check|--list-models|--help)
    exec /usr/bin/python3 "$ROOT/app/lab.py" "$@"
    ;;
  *)
    exec /usr/bin/python3 "$ROOT/app/galaxy.py" "$@"
    ;;
esac
