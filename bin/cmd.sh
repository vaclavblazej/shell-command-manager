#!/usr/bin/env bash

export PYTHONPATH
PYTHONPATH="$(dirname "$(dirname "$(readlink -f "$0")")"):$PYTHONPATH"
exec python3 -m shcmdmgr "$@"
