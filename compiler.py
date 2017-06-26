#!/usr/bin/python3
# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8

import sys
import os
import pickle

from mlctypes import NodeAST
from mlctypes import Token

FETCH, STORE, PUSH, POP, ADD, SUB, MUL, DIV, JL, JG, JLE, JGE, JE, JNE, JMP, CMP, HALT,\
WRITE, READ, AND, OR, NOT = range(22)

ast = None
decls = None
ids = None
numbers = None
pc = 0
program = []

TABLE_KEYWORD   = 1
TABLE_SEPARATOR = 2
TABLE_NUMBER    = 3
TABLE_ID        = 4

def add_command(command):
    global progam, pc
    program.append(command)
    pc += 1

def compile_ast(ast):
    if ast.kind == NodeAST.NUMBER:
        add_command(PUSH)
        add_command(numbers[ast.args[0]])

    elif ast.kind == NodeAST.ID:
        add_command(FETCH)
        add_command(ast.args[0])

    elif ast.kind == NodeAST.BOOL:
        add_command(PUSH)
        if ast.args[0] == Token.TRUE:
            add_command(True)
        else:
            add_command(False)

    elif ast.kind == NodeAST.OP:
        if ast.args[0] == TABLE_SEPARATOR:
            if ast.args[1] == Token.PLUS:
                add_command(ADD)
            elif ast.args[1] == Token.MINUS:
                add_command(SUB)
            elif ast.args[1] == Token.DIV:
                add_command(DIV)
            elif ast.args[1] == Token.MUL:
                add_command(MUL)
            else:
                add_command(CMP)
                if ast.args[1] == Token.LESS:
                    add_command(JGE)
                elif ast.args[1] == Token.GREAT:
                    add_command(JLE)
                elif ast.args[1] == Token.LESSEQUAL:
                    add_command(JG)
                elif ast.args[1] == Token.GREATEQUAL:
                    add_command(JL)
                elif ast.args[1] == Token.EQUAL:
                    add_command(JNE)
                elif ast.args[1] == Token.NOTEQUAL:
                    add_command(JE)
                add_command(pc + 7)
                add_command(POP)
                add_command(POP)
                add_command(PUSH)
                add_command(True)
                add_command(JMP)
                add_command(pc + 5)
                add_command(POP)
                add_command(POP)
                add_command(PUSH)
                add_command(False)
        else:
            if ast.args[1] == Token.AND:
                add_command(AND)
            elif ast.args[1] == Token.OR:
                add_command(OR)
            elif ast.args[1] == Token.NOT:
                add_command(NOT)

    elif ast.kind == NodeAST.EXPR:
        compile_ast(ast.args[1])
        if ast.args[2]:
            compile_ast(ast.args[2])
        compile_ast(ast.args[0])

    elif ast.kind == NodeAST.ASS:
        compile_ast(ast.args[1])
        add_command(STORE)
        add_command(ast.args[0].args[0])

    elif ast.kind == NodeAST.WRITE:
        for e in ast.args:
            compile_ast(e)
            add_command(WRITE)

    elif ast.kind == NodeAST.READ:
        for i in ast.args:
            compile_ast(i)
            add_command(READ)

    elif ast.kind == NodeAST.IF:
        compile_ast(ast.args[0])
        add_command(PUSH)
        add_command(True)
        add_command(CMP)
        add_command(POP)
        add_command(POP)
        add_command(JNE)

        addr = pc
        add_command(0)
        
        compile_ast(ast.args[1])
        program[addr] = pc
        if ast.args[2]:
            program[addr] += 2
            add_command(JMP)
            addr = pc
            add_command(0)
            compile_ast(ast.args[2])
            program[addr] = pc

    elif ast.kind == NodeAST.FOR:
        compile_ast(ast.args[0])
        compile_ast(ast.args[1])
        compile_ast(ast.args[0].args[0])
        add_command(CMP)
        add_command(JLE)
        addr = pc
        add_command(0)
        compile_ast(ast.args[2])
        add_command(PUSH)
        add_command(1)
        add_command(ADD)
        add_command(STORE)
        add_command(ast.args[0].args[0].args[0])
        add_command(JMP)
        add_command(addr - 4)
        program[addr] = pc
        add_command(POP)
        add_command(POP)

    elif ast.kind == NodeAST.WHILE:
        begin = pc
        compile_ast(ast.args[0])
        add_command(PUSH)
        add_command(True)
        add_command(CMP)
        add_command(POP)
        add_command(POP)
        add_command(JNE)

        addr = pc
        add_command(0)
        compile_ast(ast.args[1])
        add_command(JMP)
        add_command(begin)
        program[addr] = pc

    elif ast.kind == NodeAST.STMT_SEQ:
        for stmt in ast.args:
            compile_ast(stmt)

def init(lexer_filename, semantic_filename):
    global ids, numbers, ast, decls
    with open(semantic_filename, 'rb') as handle:
        numbers, decls, ast = pickle.load(handle)
    with open(lexer_filename, 'r') as handle:
        handle.readline()
        ids = handle.readline().split()

if __name__ == '__main__':
    if len(sys.argv) != 4:
        print('compiler: Error: Required input files.')
        sys.exit(1)
    else:
        lexer_filename = sys.argv[1]
        semantic_filename = sys.argv[2]
        program_filename = sys.argv[3]
        if not os.path.isfile(semantic_filename):
            print('compiler: Error: File \'' + semantic_filename + '\' is not exist.')
            sys.exit(1)
        if not os.path.isfile(lexer_filename):
            print('compiler: Error: File \'' + lexer_filename + '\' is not exist.')
            sys.exit(1)

        init(lexer_filename, semantic_filename)
        for item in ast:
            compile_ast(item)
        program.append(HALT)

    with open(program_filename, 'wb') as handle:
        pickle.dump([decls, program], handle)

    with open(program_filename + '.S', 'w') as handle:
        i = 0
        while i < len(program):
            if program[i] == FETCH:
                handle.write(str(i) + ':' + str(i + 1) + '\tFETCH\t' + ids[program[i + 1]] + '\n')
                i += 2
            elif program[i] == STORE:
                handle.write(str(i) + ':' + str(i + 1) + '\tSTORE\t' + ids[program[i + 1]] + '\n')
                i += 2
            elif program[i] == PUSH:
                handle.write(str(i) + ':' + str(i + 1) + '\tPUSH\t' + str(program[i + 1]) + '\n')
                i += 2
            elif program[i] == POP:
                handle.write(str(i) + '\tPOP' + '\n')
                i += 1
            elif program[i] == ADD:
                handle.write(str(i) + '\tADD' + '\n')
                i += 1
            elif program[i] == SUB:
                handle.write(str(i) + '\tSUB' + '\n')
                i += 1
            elif program[i] == MUL:
                handle.write(str(i) + '\tMUL' + '\n')
                i += 1
            elif program[i] == DIV:
                handle.write(str(i) + '\tDIV' + '\n')
                i += 1
            elif program[i] == NOT:
                handle.write(str(i) + '\tNOT' + '\n')
                i += 1
            elif program[i] == AND:
                handle.write(str(i) + '\tAND' + '\n')
                i += 1
            elif program[i] == OR:
                handle.write(str(i) + '\tOR' + '\n')
                i += 1
            elif program[i] == JL:
                handle.write(str(i) + ':' + str(i + 1) + '\tJL\t' + str(program[i + 1]) + '\n')
                i += 2
            elif program[i] == JG:
                handle.write(str(i) + ':' + str(i + 1) + '\tJG\t' + str(program[i + 1]) + '\n')
                i += 2
            elif program[i] == JLE:
                handle.write(str(i) + ':' + str(i + 1) + '\tJLE\t' + str(program[i + 1]) + '\n')
                i += 2
            elif program[i] == JGE:
                handle.write(str(i) + ':' + str(i + 1) + '\tJGE\t' + str(program[i + 1]) + '\n')
                i += 2
            elif program[i] == JE:
                handle.write(str(i) + ':' + str(i + 1) + '\tJE\t' + str(program[i + 1]) + '\n')
                i += 2
            elif program[i] == JNE:
                handle.write(str(i) + ':' + str(i + 1) + '\tJNE\t' + str(program[i + 1]) + '\n')
                i += 2
            elif program[i] == JMP:
                handle.write(str(i) + ':' + str(i + 1) + '\tJMP\t' + str(program[i + 1]) + '\n')
                i += 2
            elif program[i] == CMP:
                handle.write(str(i) + '\tCMP' + '\n')
                i += 1
            elif program[i] == WRITE:
                handle.write(str(i) + '\tWRITE' + '\n')
                i += 1
            elif program[i] == READ:
                handle.write(str(i) + '\tREAD' + '\n')
                i += 1
            elif program[i] == HALT:
                handle.write(str(i) + '\tHALT' + '\n')
                i += 1

        sys.exit(0)

