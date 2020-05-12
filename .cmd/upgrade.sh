#!/usr/bin/env bash
echo 'upgrading from test server, enter version'
read version
echo "install '$version', run:"
echo "pip3 install --upgrade --index-url https://test.pypi.org/simple/ \"shcmdmgr==$version\""
#pip3 install --upgrade --index-url https://test.pypi.org/simple/ "shcmdmgr==$version"
