#!/usr/bin/env bash

cd $project_root

pylint --rcfile="$PWD/.cmd/lint.rc" shcmdmgr
