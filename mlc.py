#!/usr/bin/python3
# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8

import sys
import os
import subprocess

lexer_filename = 'lexer.out'
parser_filename = 'parser.out'
semantic_filename = 'semantic.out'

def make(filename, program_filename):
    exit_code = subprocess.call(['./main', filename, lexer_filename])
    if exit_code:
        sys.exit(1)

    exit_code = subprocess.call(['./parser.py', lexer_filename])
    if exit_code:
        sys.exit(1)

    exit_code = subprocess.call(['./semantic.py', lexer_filename, parser_filename])
    if exit_code:
        sys.exit(1)

    exit_code = subprocess.call(['./compiler.py', lexer_filename, semantic_filename, program_filename])
    if exit_code:
        sys.exit(1)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Error: too few arguments')
        print('mlc INPUT_FILE [OUTPUT_FILE]')
        sys.exit(1)

    if len(sys.argv) == 2:
        if os.path.isfile(sys.argv[1]):
            make(sys.argv[1], 'a.out')
            sys.exit(0)
        else:
            print('Error: file \'' + sys.argv[1] + '\' does not exist')
            sys.exit(1)
    if len(sys.argv) == 3:
        if os.path.isfile(sys.argv[1]):
            make(sys.argv[1], sys.argv[2])
            sys.exit(0)
        else:
            print('Error: file \'' + sys.argv[1] + '\' does not exist')
            sys.exit(1)
    print('Error: too many arguments')
    print('mlc INPUT_FILE [OUTPUT_FILE]')
    sys.exit(1)
