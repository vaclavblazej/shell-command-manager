#!/usr/bin/env zsh

DIR=$(dirname $0:A)
SCRIPT="$DIR/../cmd/__main__.py" # relative to the script location

function _my_custom_completion_func {
    local cmd_string
    cmd_string="$PREBUFFER$LBUFFER"
    cmd_string=${cmd_string/$'\\\n'/' '}
    IFS=$' ' comp=($(echo $cmd_string))
    comp=('--complete' ${comp[@]:1})
    if [[ "${cmd_string: -1}" == ' ' ]]; then comp+=(''); fi
    ans_str=($($SCRIPT "${comp[@]}"))
    local ans
    IFS=$' ' ans=($(echo $ans_str))
    _describe 'cmd' ans
}

compdef _my_custom_completion_func cmd

