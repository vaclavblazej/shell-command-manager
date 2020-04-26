#!/usr/bin/env bash

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
SCRIPT="$DIR/../cmd.py" # relative to the script location

function _my_custom_completion_func {
    trimmed="${COMP_LINE:0:$COMP_POINT}"
    comp=($trimmed)
    comp=('--complete' "${comp[@]:1}") # remove the program name and add a flag
    if [ "${trimmed: -1}" = ' ' ]; then comp+=(''); fi
    COMPREPLY=()
    reply=($("$SCRIPT" "${comp[@]}"))
    for reply_word in "${reply[@]}"; do COMPREPLY+=("$reply_word "); done
}

complete -o nospace -F _my_custom_completion_func cmd

