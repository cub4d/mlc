#!/usr/bin/python3
# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8

import sys
import os
import pickle

from mlctypes import Token

FETCH, STORE, PUSH, POP, ADD, SUB, MUL, DIV, JL, JG, JLE, JGE, JE, JNE, JMP, CMP, HALT,\
WRITE, READ, AND, OR, NOT = range(22)

# Commands sequence
program = []

# {index, value}
decls = {}

def run():
    # [less, great, equal]
    flags = [0, 0, 0]
    stack = []
    pc = 0

    while True:
        op = program[pc]

        if op == FETCH:
            if decls[program[pc + 1]][0] == Token.FLOAT:
                stack.append(float(decls[program[pc + 1]][1]))
            elif decls[program[pc + 1]][0] == Token.INT:
                stack.append(int(decls[program[pc + 1]][1]))
            else:
                stack.append(decls[program[pc + 1]][1])
            pc += 2
        elif op == STORE:
            if decls[program[pc + 1]][0] == Token.FLOAT:
                decls[program[pc + 1]][1] = float(stack.pop())
            elif decls[program[pc + 1]][0] == Token.INT:
                decls[program[pc + 1]][1] = int(stack.pop())
            else:
                decls[program[pc + 1]][1] = stack.pop()
            pc += 2
        elif op == PUSH:
            stack.append(program[pc + 1])
            pc += 2
        elif op == POP:
            stack.pop()
            pc += 1
        elif op == ADD:
            stack[-2] += stack[-1]
            stack.pop()
            pc += 1
        elif op == SUB:
            stack[-2] -= stack[-1]
            stack.pop()
            pc += 1
        elif op == MUL:
            stack[-2] *= stack[-1]
            stack.pop()
            pc += 1
        elif op == DIV:
            stack[-2] /= stack[-1]
            stack.pop()
            pc += 1
        elif op == AND:
            stack[-2] = stack[-2] and stack[-1]
            stack.pop()
            pc += 1
        elif op == OR:
            stack[-2] = stack[-2] or stack[-1]
            stack.pop()
            pc += 1
        elif op == NOT:
            stack[-1] = not stack[-1]
            pc += 1
        elif op == CMP:
            flags = [0, 0, 0]
            if stack[-1] == stack[-2]:
                flags[2] = 1
                flags[1] = 0
                flags[0] = 0
            if stack[-2] < stack[-1]:
                flags[0] = 1
                flags[1] = 0
            if stack[-2] > stack[-1]:
                flags[1] = 1
                flags[0] = 0
            pc += 1
        elif op == JL:
            if flags[0] == 1 and flags[2] == 0:
                pc = program[pc + 1]
            else:
                pc += 2
        elif op == JG:
            if flags[1] == 1 and flags[2] == 0:
                pc = program[pc + 1]
            else:
                pc += 2
        elif op == JLE:
            if flags[0] == 1 or flags[2] == 1:
                pc = program[pc + 1]
            else:
                pc += 2
        elif op == JGE:
            if flags[1] == 1 or flags[2] == 1:
                pc = program[pc + 1]
            else:
                pc += 2
        elif op == JNE:
            if flags[2] == 0:
                pc = program[pc + 1]
            else:
                pc += 2
        elif op == JMP:
            pc = program[pc + 1]
        elif op == WRITE:
            print(stack[-1])
            stack.pop()
            pc += 1
        elif op == HALT:
            break

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Error: required program file')
        print('mlvm FILE')
        sys.exit(1)
    if not os.path.isfile(sys.argv[1]):
        print('Error: file \'' + sys.argv[1] + '\' does not exist')
        sys.exit(1)
    with open(sys.argv[1], 'rb') as handle:
        decls, program = pickle.load(handle)
    run()
