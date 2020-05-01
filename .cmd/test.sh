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
cmd --complete '' && \
cmd --complete --complete '' && \
cmd --complete --save '' && \
cmd --complete -s '' && \
cmd --complete 'e' && \
cmd --complete 'a' && \
cmd --complete 't' && \
echo '>>> Basic tests completed SUCCESFULLY' || \
echo '>>> Encountered ERROR! see above for what happened'
