#!/usr/bin/python3
# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8

import sys
import os
import pickle

import mlctypes
from mlctypes import Token
from mlctypes import NodeAST

# Keywords
keywords = ['program', 'begin', 'end', 'var', 'true', 'false', 'ass', 'if', 'else',
            'then', 'for', 'to', 'do', 'while', 'read', 'write', 'int', 'float',
            'bool', 'and', 'or', 'not']

# Separators
separators = ['+', '-', '=', '<', '>', '*', '/', '(', ')', ';', '.', ':', '<=', '>=', '<>', ',']
numbers = []
ids = []

TABLE_KEYWORD   = 1
TABLE_SEPARATOR = 2
TABLE_NUMBER    = 3
TABLE_ID        = 4

# lexer token = [line, table_index, token_index]
tokens = []
tokens_iterator = None
token = Token(0, 0)
token_line = 0
errors = False

def ast_to_string(ast, level = 0):
    tab = '   ' * level
    nl  = '\n'

    if ast.kind == NodeAST.NUMBER:
        return tab + str(numbers[ast.args[0]]) + nl

    if ast.kind == NodeAST.ID:
        return tab + ids[ast.args[0]] + nl

    if ast.kind == NodeAST.BOOL:
        return tab + keywords[ast.args[0]] + nl

    if ast.kind == NodeAST.OP:
        if ast.args[0] == TABLE_SEPARATOR:
            return tab + separators[ast.args[1] - Token.PLUS] + nl
        else:
            return tab + keywords[ast.args[1]] + nl

    if ast.kind == NodeAST.EXPR:
        result = ast_to_string(ast.args[0], level) +\
                 ast_to_string(ast.args[1], level + 1)
        if ast.args[2]:
            result += ast_to_string(ast.args[2], level + 1)
        return result

    if ast.kind == NodeAST.STMT_SEQ:
        result = ast_to_string(ast.args[0], level)
        for item in ast.args[1:]:
            result += ast_to_string(item, level)
        return result

    if ast.kind == NodeAST.IF:
        result = tab + '[if]' + nl +\
                 ast_to_string(ast.args[0], level + 1) +\
                 tab + '[then]' + nl +\
                 ast_to_string(ast.args[1], level + 1)
        if ast.args[2]:
            result += tab + '[else]' + nl
            result += ast_to_string(ast.args[2], level + 1)
        return result

    if ast.kind == NodeAST.FOR:
        return tab + '[for]' + nl +\
               ast_to_string(ast.args[0], level + 1) +\
               tab + '[to]' + nl +\
               ast_to_string(ast.args[1], level + 1) +\
               tab + '[do]' + nl +\
               ast_to_string(ast.args[2], level + 1)

    if ast.kind == NodeAST.WHILE:
        return tab + '[while]' + nl +\
               ast_to_string(ast.args[0], level + 1) +\
               tab + '[do]' + nl +\
               ast_to_string(ast.args[1], level + 1)

    if ast.kind == NodeAST.ASS:
        return tab + '[ass]' + nl +\
               ast_to_string(ast.args[0], level + 1) +\
               ast_to_string(ast.args[1], level + 1)

    if ast.kind == NodeAST.WRITE:
        result = tab + '[write]' + nl
        for item in ast.args:
            result += ast_to_string(item, level + 1)
        return result

    if ast.kind == NodeAST.READ:
        result = tab + '[read]' + nl
        for item in ast.args:
            result += ast_to_string(item, level + 1)
        return result

    if ast.kind == NodeAST.PROGRAM:
        result = tab + '[declarations]' + nl
        for item in ast.args[0]:
            result += '   ' + keywords[item[0]] + ' '
            for var in item[1:]:
                result += ids[var] + ' '
            result += nl
        result += tab + '[statements]' + nl
        for item in ast.args[1]:
            result += ast_to_string(item, level + 1)
        return result.rstrip('\n')

def next_token():
    global token
    global token_line
    t = next(tokens_iterator, None)
    if t:
        token = Token(t[1], t[2])
        token_line = t[0]
    else:
        token = Token(None, None)

# <mulop> ::= * | / | and
def mulop():
    if token.value == token.MUL or token.value == token.DIV:
        return NodeAST(NodeAST.OP, token_line, TABLE_SEPARATOR, token.value)
    if token.value == token.AND:
        return NodeAST(NodeAST.OP, token_line, TABLE_KEYWORD, token.value)
    return None

# <sumop> ::= + | - | or
def sumop():
    if token.value == token.PLUS or token.value == token.MINUS:
        return NodeAST(NodeAST.OP, token_line, TABLE_SEPARATOR, token.value)
    if token.value == token.OR:
        return NodeAST(NodeAST.OP, token_line, TABLE_KEYWORD, token.value)
    return None

# <relop> ::= <> | = | < | >= | > | >=
def relop():
    if (token.value == token.NOTEQUAL) or (token.value == token.EQUAL) or \
       (token.value == token.LESS) or (token.value == token.GREAT) or     \
       (token.value == token.LESSEQUAL) or (token.value == token.GREATEQUAL):
        return NodeAST(NodeAST.OP, token_line, TABLE_SEPARATOR, token.value)
    return None

# <expr> ::= <operand> {<relations_op> <operand>}
def expr():
    lhs = operand()
    if lhs:
        op = relop()
        if op:
            next_token()
            rhs = expr()
            if rhs:
                return NodeAST(NodeAST.EXPR, token_line, op, lhs, rhs)
            return None
        return lhs
    return None

# <operand> ::= <summand> {<sumop> <operand>}
def operand():
    lhs = summand()
    if lhs:
        op = sumop()
        if op:
            next_token()
            rhs = operand()
            if rhs:
                return NodeAST(NodeAST.EXPR, token_line, op, lhs, rhs)
            return None
        return lhs
    return None

# <summand> ::= <multiplier> {<mulop> <summand>}
def summand():
    lhs = multiplier()
    if lhs:
        next_token()
        op = mulop()
        if op:
            next_token()
            rhs = summand()
            if rhs:
                return NodeAST(NodeAST.EXPR, token_line, op, lhs, rhs)
            return None
        return lhs
    return None

def convert_to_number(snum):
    if snum[-1] == 'H' or snum[-1] == 'h':
        return int('0x' + snum[:-1], 16)
    if snum[-1] == 'O' or snum[-1] == 'o':
        return int('0' + snum[:-1], 8)
    if snum[-1] == 'B' or snum[-1] == 'b':
        return int('0b' + snum[:-1], 2)
    if 'E' in snum or 'e' in snum or '+' in snum or \
       '-' in snum or '.' in snum:
       return float(snum)
    if snum[-1] == 'D' or snum[-1] == 'd':
        snum = snum[:-1]
    return int(snum)

# <multiplier> ::= <id> | <number> | <logical> | <unary multiplier> | (<expr>)
def multiplier():
    if token.table == TABLE_ID:
        return NodeAST(NodeAST.ID, token_line, token.index)

    if token.table == TABLE_NUMBER:
        return NodeAST(NodeAST.NUMBER, token_line, token.index)

    if token.value == token.TRUE or token.value == token.FALSE:
        return NodeAST(NodeAST.BOOL, token_line, token.index)

    if token.value == token.NOT:
        next_token()
        m = multiplier()
        if not m:
            return None
        return NodeAST(NodeAST.EXPR, token_line, NodeAST(NodeAST.OP, token_line, TABLE_KEYWORD, token.NOT), m, None)

    if token.value == token.LPAR:
        next_token()
        e = expr()
        if e and token.value == token.RPAR:
            return e

    return None

# <stmt> ::= <stmt> { : <stmt> } | <ass_stmt> | <if_stmt> | <for_stmt> | <while_stmt> | <write_stmt> | <read_stmt>
def stmt():
    args = []
    node = None
    if token.table == TABLE_ID:
        node = ass_stmt()
    elif token.value == token.IF:
        node = if_stmt()
    elif token.value == token.WRITE:
        node = write_stmt()
    elif token.value == token.READ:
        node = read_stmt()
    elif token.value == token.FOR:
        node = for_stmt()
    elif token.value == token.WHILE:
        node = while_stmt()
    if node:
        if token.value == token.COLON:
            args.append(node)
            while token.value == token.COLON:
                next_token()
                if token.table == TABLE_ID:
                    node = ass_stmt()
                elif token.value == token.IF:
                    node = if_stmt()
                elif token.value == token.WRITE:
                    node = write_stmt()
                elif token.value == token.READ:
                    node = read_stmt()
                elif token.value == token.FOR:
                    node = for_stmt()
                elif token.value == token.WHILE:
                    node = while_stmt()
                if not node:
                    return None
                args.append(node)
            return NodeAST(NodeAST.STMT_SEQ, token_line, *args)
        return node
    return None

# <ass_stmt> ::= <id> ass <expr>
def ass_stmt():
    lhs = NodeAST(NodeAST.ID, token_line, token.index)
    next_token()
    if token.value == token.ASS:
        next_token()
        rhs = expr()
        if rhs:
            return NodeAST(NodeAST.ASS, token_line, lhs, rhs)
        print('Error [line ' + str(token_line) + ']: expected expression after \'ass\'')
        return None
    print('Error [line ' + str(token_line) + ']: expected \'ass\'')
    return None

# <if_stmt> ::= if <expr> then <stmt> [else <stmt>]
def if_stmt():
    next_token()
    cond = expr()
    if cond:
        if token.value == token.THEN:
            next_token()
            lhs = stmt()
            if lhs:
                if token.value == token.ELSE:
                    next_token()
                    rhs = stmt()
                    if rhs:
                        return NodeAST(NodeAST.IF, token_line, cond, lhs, rhs)
                    print('Error [line ' + str(token_line) + ']: expected statement after \'else\'')
                    return None
                return NodeAST(NodeAST.IF, token_line, cond, lhs, None)
            print('Error [line ' + str(token_line) + ']: expected statement after \'then\'')
            return None
        print('Error [line ' + str(token_line) + ']: expected \'then\' in \'if\' statement')
        return None
    print('Error [line ' + str(token_line) + ']: expected expression after \'if\'')
    return None

# <for_stmt> ::= for <ass_stmt> to <expr> do <stmt>
def for_stmt():
    next_token()
    begin = ass_stmt()
    if begin:
        if token.value == token.TO:
            next_token()
            end = expr()
            if end:
                if token.value == token.DO:
                    next_token()
                    stmts = stmt()
                    if stmts:
                        return NodeAST(NodeAST.FOR, token_line, begin, end, stmts)
                    print('Error [line ' + str(token_line) + ']: expected statement after \'do\'')
                    return None
                print('Error [line ' + str(token_line) + ']: expected \'do\' in \'for\' statement')
                return None
            print('Error [line ' + str(token_line) + ']: expected expression after \'to\'')
            return None
        print('Error [line ' + str(token_line) + ']: expected \'to\' in \'for\' statement')
        return None
    print('Error [line ' + str(token_line) + ']: expected statement after \'for\'')
    return None

# <while_stmt> ::= while <expr> do <stmt>
def while_stmt():
    next_token()
    cond = expr()
    if cond:
        if token.value == token.DO:
            next_token()
            stmts = stmt()
            if stmts:
                return NodeAST(NodeAST.WHILE, token_line, cond, stmts)
            print('Error [line ' + str(token_line) + ']: expected statement after \'do\'')
            return None
        print('Error [line ' + str(token_line) + ']: expected \'do\' in \'while\' statement')
        return None
    print('Error [line ' + str(token_line) + ']: expected expression after \'while\'')
    return None

# <write_stmt> ::= write(<expr> {, <expr>})
def write_stmt():
    next_token()
    args = []
    if token.value == token.LPAR:
        next_token()
        args.append(expr())
        if not args[-1]:
            print('Error [line ' + str(token_line) + ']: expected expression after \'(\'')
            return None

        while token.value == token.COMMA:
            next_token()
            args.append(expr())
            if not args[-1]:
                print('Error [line ' + str(token_line) + ']: expected expression')
                return None

        if token.table == TABLE_ID:
            print('Error [line ' + str(token_line) + ']: expected \',\'')
            return None
        elif token.value == token.RPAR:
            next_token()
            return NodeAST(NodeAST.WRITE, token_line, *args)
        else:
            print('Error [line ' + str(token_line) + ']: expected \')')
            return None
    print('Error [line ' + str(token_line) + ']: expected \'(\'')
    return None

# <read_stmt> ::= read(<id> {, <id>})
def read_stmt():
    args = []
    next_token()
    if token.value == token.LPAR:
        next_token()
        if token.table != TABLE_ID:
            print('Error [line ' + str(token_line) + ']: expected variable after \'(\'')
            return None
        args.append(NodeAST(NodeAST.ID, token_line, token.index))
        next_token()
        while token.value == token.COMMA:
            next_token()
            if token.table != TABLE_ID:
                print('Error [line ' + str(token_line) + ']: expected variable after \'(\'')
                return None
            args.append(NodeAST(NodeAST.ID, token_line, token.index))
            next_token()
        if token.value == token.RPAR:
            next_token()
            return NodeAST(NodeAST.READ, token_line, *args)
    print('Error [line ' + str(token_line) + ']: expected \'(\' after \'read\'')
    return None

# <declaration> ::= (int | float | bool) <id> {, <id>}
def declaration():
    if (token.value == token.INT) or (token.value == token.FLOAT) or (token.value == token.BOOL):
        decl = [token.value]
        next_token()
        if token.table == TABLE_ID:
            decl.append(token.index)
            next_token()
            if token.table == TABLE_ID:
                print('Error [line ' + str(token_line) + ']: ' + 'expected \',\'')
                return None
            while token.value == token.COMMA:
                next_token()
                if token.table != TABLE_ID:
                    print('Error [line ' + str(token_line) + ']: ' + 'expected variable')
                    return None
                decl.append(token.index)
                next_token()
            if token.table == TABLE_ID:
                print('Error [line ' + str(token_line) + ']: ' + 'expected \',\'')
                return None
            return decl
    print('Error [line ' + str(token_line) + ']: ' + 'expected variable')
    return None

# <program> = program var <declaration> {; <declaration>} begin <stmt> {; <stmt>} end.
def parse():
    global errors

    if token.value != token.PROGRAM:
        print('Error [line ' + str(token_line) + ']: expected \'program\'')
        return None
    next_token()

    if token.value != token.VAR:
        print('Error [line ' + str(token_line) + ']: expected \'var\'')
        return None
    next_token()

    decls = []
    decls.append(declaration())
    while decls[-1]:
        if token.value == token.BEGIN:
            break
        decls.append(declaration())
    if not decls:
        print('Error [line ' + str(token_line) + ']: expected declarations')
        return None

    next_token()
    stmts = []
    result = stmt()
    while True:
        if not result:
            if token.value == token.END or not token.value:
                break
            errors = True
            while token.value != token.SEMICOLON:
                next_token()
                if not token.value: 
                    break
            next_token()
            if token.value == token.END or not token.value:
                break
            result = stmt()

        stmts.append(result)
        if token.value != token.SEMICOLON:
            print('Error [line ' + str(token_line) + ']: ' + 'expected \';\' after statement')
            return None
        next_token()
        result = stmt()

    if token.value != token.END:
        print('Error [line ' + str(token_line) + ']: ' + 'expected \'end\'')
        return None
    next_token()

    if token.value != token.DOT:
        print('Error [line ' + str(token_line) + ']: ' + 'expected \'.\' after \'end\'')
        return None

    return NodeAST(NodeAST.PROGRAM, token_line, decls, stmts)

def init(filename):
    global numbers
    global ids
    with open(filename, 'r') as file:
        numbers = file.readline().split()
        ids     = file.readline().split()

        items = file.readline().split()
        for item in items:
            item = item.split(',')
            tokens.append([int(item[0]), int(item[1]), int(item[2])])

        for i in range(len(numbers)):
            numbers[i] = convert_to_number(numbers[i])

    global tokens_iterator
    tokens_iterator = iter(tokens)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('parser: Error. Required input file.')
    else:
        lexer_filename = sys.argv[1]
        if not os.path.isfile(lexer_filename):
            print('parser: Error. File \'' + lexer_filename + '\' is not exist.')

        init(lexer_filename)
        next_token()
        program = parse()
        if not errors and program:
            with open('parser.out', 'wb') as handle:
                pickle.dump([numbers, program], handle)
            with open('ast.tree', 'w') as handle:
                handle.write(ast_to_string(program) + '\n')
            sys.exit(0)
        sys.exit(1)
