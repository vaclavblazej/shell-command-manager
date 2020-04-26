#!/usr/bin/env zsh

DIR=$(dirname $0:A)
SCRIPT="$DIR/test_completion.py" # relative to the script location

function _my_custom_completion_func {
    local cmd_string
    cmd_string="$PREBUFFER$LBUFFER"
    cmd_string=${cmd_string/$'\\\n'/' '}
    IFS=$' ' comp=($(echo $cmd_string))
    if [[ "${cmd_string: -1}" == ' ' ]]; then comp+=(''); fi
    ans_str=($($SCRIPT "${comp[@]}"))
    local ans
    IFS=$' ' ans=($(echo $ans_str))
    _describe 'test' ans
}

#compdef _gnu_generic test
compdef _my_custom_completion_func test


#change the first line to this, to make the script autoloadable; and name the function _test
#compdef test
