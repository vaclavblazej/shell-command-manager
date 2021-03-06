#!/usr/bin/env bash

cd $project_root

echo 'Deploying to the TEST pypi server'
python3 -m twine upload --repository test-pypi dist/* \
&& echo 'Deployment successful'
