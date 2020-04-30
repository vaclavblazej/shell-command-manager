#!/usr/bin/env bash

cmd && \
cmd --version && \
cmd -v && \
cmd --help && \
cmd -h && \
cmd --quiet && \
cmd -q && \
cmd --verbose && \
cmd -v && \
cmd --debug && \
cmd -d && \
cmd --project && \
cmd -p && \
cmd -pd && \
echo '>>> Basic tests completed SUCCESFULLY' || \
echo '>>> Encountered ERROR! see above for what happened'
