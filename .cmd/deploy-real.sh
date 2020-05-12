#!/usr/bin/env bash

cd $project_root

echo 'Deploying to the PUBLIC pypi server!'
echo 'Content to be deployed:'
ls ./dist/
echo 'Are you sure you want to continue? (y/N): '
read res
echo $res
if [ "$res" == 'y' ]; then
    python3 -m twine upload --repository pypi dist/* \
    && echo 'Deployment successful'
else
    echo 'Deployment canceled'
fi

