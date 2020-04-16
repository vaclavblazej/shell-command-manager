_cmd_complete()
{
    local cur prev opts node_names
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    opts=$($CHEF_DIR/repo_scripts/show.py --help | grep '  --' | awk '{print $1}')
    node_names=$(python $CHEF_DIR/repo_scripts/node_names.py)

    if [[ ${cur} == -* ]] ; then
        COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
        return 0
    fi

    COMPREPLY=( $(compgen -W "${node_names}" -- ${cur}) )
}

complete -F _cmd_complete cmd
