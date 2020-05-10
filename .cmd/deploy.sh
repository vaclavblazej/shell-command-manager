#!/usr/bin/env bash

echo 'Deploying to the TEST pypi server'
python3 -m twine upload --repository testpypi dist/* \
&& echo 'Deployment successful'
