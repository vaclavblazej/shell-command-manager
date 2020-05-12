#!/usr/bin/env bash

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
export PYTHONPATH
PACKAGE="$(dirname "$(dirname "$(dirname "$(readlink -f "$DIR")")")")"
PYTHONPATH="$PACKAGE:$PYTHONPATH"

function _shcmdmgr_completion_func {
    trimmed="${COMP_LINE:0:$COMP_POINT}"
    comp=($trimmed)
    comp=('--complete' "${comp[@]:1}") # remove the program name and add a flag
    if [ "${trimmed: -1}" = ' ' ]; then comp+=(''); fi
    COMPREPLY=()
    reply=($(python3 "$DIR/run.py" "${comp[@]}"))
    for reply_word in "${reply[@]}"; do COMPREPLY+=("$reply_word "); done
}

complete -o nospace -F _shcmdmgr_completion_func "$1"
