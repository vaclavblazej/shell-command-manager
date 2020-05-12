#!/usr/bin/env zsh

DIR=$(dirname $0:A)
export PYTHONPATH
PACKAGE="$(dirname "$(dirname "$(dirname "$(readlink -f "$DIR")")")")"
PYTHONPATH="$PACKAGE:$PYTHONPATH"

function _my_custom_completion_func {
    local cmd_string
    cmd_string="$PREBUFFER$LBUFFER"
    cmd_string=${cmd_string/$'\\\n'/' '}
    IFS=$' ' comp=($(echo $cmd_string))
    comp=('--complete' ${comp[@]:1})
    if [[ "${cmd_string: -1}" == ' ' ]]; then comp+=(''); fi
    ans_str=($(python3 "$DIR/run.py" "${comp[@]}"))
    local ans
    IFS=$' ' ans=($(echo $ans_str))
    _describe 'cmd' ans
}

compdef _my_custom_completion_func $1
