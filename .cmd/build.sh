#!/usr/bin/env bash
cd $project_root
rm -rf ./shcmdmgr.egg-info/ ./dist/ ./build/

python3 setup.py sdist bdist_wheel
