#!/usr/bin/env bash

# FIRST VERSION (simple but with imperfections) ##############################

#function _my_custom_completion_func {
    #COMPREPLY=($(compgen -W "thursday third fouth" "${COMP_WORDS[$COMP_CWORD]}"))
#}
#complete -F _my_custom_completion_func test


# SECOND VERSION (good for a fixed set of completed words) ###################

#function _my_custom_completion_func {
    #comp=(${COMP_LINE:0:$COMP_POINT})
    #COMPREPLY=()
    #reply=($(compgen -W "thursday third fouth" "${comp[$COMP_CWORD]}"))
    #for reply_word in "${reply[@]}"; do COMPREPLY+=("$reply_word "); done
#}
#complete -o nospace -F _my_custom_completion_func test


# THIRD VERSION (calling another script for the completion) ##################

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
SCRIPT="$DIR/test_completion.py" # relative to the script location

function _my_custom_completion_func {
    trimmed="${COMP_LINE:0:$COMP_POINT}"
    comp=($trimmed)
    if [ "${trimmed: -1}" = ' ' ]; then comp+=(''); fi
    COMPREPLY=()
    reply=($("$SCRIPT" "${comp[@]}"))
    for reply_word in "${reply[@]}"; do COMPREPLY+=("$reply_word "); done
}

complete -o nospace -F _my_custom_completion_func test


# to test this file you have to source it by running
# $ source test_completion.bash
# then you can try running
# $ test <tab><tab>  # etc.

