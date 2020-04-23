#!/usr/bin/env python3

import sys

# the real strenght comes from generating this list dynamically
possible_words = ['thursday', 'third', 'fouth']

last_arg = sys.argv[-1]
# print(sys.argv)

for word in possible_words:
    if word.startswith(last_arg):
        print(word, end=' ')

