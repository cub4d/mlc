#!/usr/bin/python3
# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8

import sys
import os
import pickle

from mlctypes import NodeAST
from mlctypes import Token

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

# {index: [type, value]}
decls = {}
errors = ''
ast = None

def ast_to_string(ast, level = 0):
    tab = '   ' * level
    nl  = '\n'

    if ast.kind == NodeAST.NUMBER:
        return tab + '(' + keywords[ast.type] + ')' + str(numbers[ast.args[0]]) + nl

    if ast.kind == NodeAST.ID:
        return tab + '(' + keywords[ast.type] + ')' + ids[ast.args[0]] + nl

    if ast.kind == NodeAST.BOOL:
        return tab + keywords[ast.args[0]] + nl

    if ast.kind == NodeAST.OP:
        if ast.args[0] == TABLE_SEPARATOR:
            return tab + separators[ast.args[1] - Token.PLUS] + nl
        else:
            return tab + keywords[ast.args[1]] + nl

    if ast.kind == NodeAST.EXPR:
        result = tab + '(' + keywords[ast.type] + ')' + ast_to_string(ast.args[0]) +\
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
        return tab + '[ass] -> ' + keywords[ast.args[0].type] + nl +\
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
        result = tab + '[statements]' + nl
        for item in ast.args[1]:
            result += ast_to_string(item, level + 1)
        return result.rstrip('\n')

def get_id_type(ast):
    if ast.args[0] in decls:
        ast.type = decls[ast.args[0]][0]
        return ast.type
    return None

def get_number_type(ast):
    num = numbers[ast.args[0]]
    if type(num) is int:
        return Token.INT
    if type(num) is float:
        return Token.FLOAT

def verify_decl(decl):
    global decls
    global errors

    for var in decl[1:]:
        if var in decls:
            errors += 'Error: redeclaration of \'' + ids[var] + '\'\n'
        else:
            if decl[0] == Token.BOOL:
                decls[var] = [decl[0], True]
            else:
                decls[var] = [decl[0], False]

# Expression specification:
# e1 [*,/,+,-] e2: e1 and e2 are numbers
# e1 [and,or,not] e2: e1 and e2 are bools
def verify_expr(expr):
    global errors

    if expr == None:
        return None
    if expr.kind == NodeAST.ID:
        expr.type = get_id_type(expr)
        if not expr.type:
            errors += 'Error [line ' + str(expr.line) + '] undeclared identificator \'' + ids[expr.args[0]] + '\'\n'
        if expr.args[0] in decls and not decls[expr.args[0]][1]:
            errors += 'Error [line ' + str(expr.line) + '] uninitialized variable \'' + ids[expr.args[0]] + '\'\n'
            return None
        return expr.type
    if expr.kind == NodeAST.NUMBER:
        expr.type = get_number_type(expr)
        return expr.type
    if expr.kind == NodeAST.BOOL:
        expr.type = Token.BOOL
        return expr.type

    op = expr.args[0]
    ltype = verify_expr(expr.args[1])
    rtype = verify_expr(expr.args[2])

    if op.args[0] == TABLE_KEYWORD:
        if (ltype == Token.BOOL and rtype == Token.BOOL) or\
           (ltype == Token.BOOL and rtype == None):
            expr.type = Token.BOOL
            return expr.type
        errors += 'Error [line ' + str(expr.line) + ']: number can not be converted to boolean\n'
        return None

    if op.args[1] == Token.MUL or op.args[1] == Token.DIV or\
       op.args[1] == Token.PLUS or op.args[1] == Token.MINUS:
        if (ltype == Token.BOOL) or (rtype == Token.BOOL):
            errors += 'Error [line ' + str(expr.line) +']: boolean can not be converted to number\n'
            return None
        if (ltype == Token.FLOAT) or (rtype == Token.FLOAT):
            expr.type = Token.FLOAT
        else:
            expr.type = Token.INT

    if op.args[1] == Token.LESS or op.args[1] == Token.GREAT or\
       op.args[1] == Token.LESSEQUAL or op.args[1] == Token.GREATEQUAL:
        if ltype == Token.BOOL or rtype == Token.BOOL:
            errors += 'Error [line ' + str(expr.line) +']: boolean can not be converted to number\n'
            return None
        expr.type = Token.BOOL

    if op.args[1] == Token.EQUAL or op.args[1] == Token.NOTEQUAL:
        if (ltype == Token.BOOL and rtype != Token.BOOL) or\
           (ltype != Token.BOOL and rtype == Token.BOOL):
            errors += 'Error [line ' + str(expr.line) + ']: number can not be converted to boolean\n'
            return None
        expr.type = Token.BOOL

    return expr.type

def verify_stmt(stmt):
    global errors

    if stmt.kind == NodeAST.ASS:
        ltype = get_id_type(stmt.args[0])
        rtype = verify_expr(stmt.args[1])

        if ltype == None:
            errors += 'Error [line ' + str(stmt.line) + '] ' + 'undeclared identificator \'' + ids[stmt.args[0].args[0]] + '\'\n'
            return
        if rtype == None:
            errors += 'Error [line ' + str(stmt.line) + '] ' + 'expected expression\n' 
            return

        if ltype == Token.BOOL:
            if rtype != Token.BOOL:
                errors += 'Error [line ' + str(stmt.line) + ']: number can not be converted to boolean\n'
            stmt.args[0].type = Token.BOOL
            decls[stmt.args[0].args[0]][1] = True
            return

        if rtype == Token.BOOL:
            errors += 'Error [line ' + str(stmt.line) + ']: boolean can not be converted to number\n'
            return

        if ltype == Token.INT and rtype == Token.FLOAT:
            stmt.args[1].type = Token.INT
        elif ltype == Token.FLOAT and rtype == Token.INT:
            stmt.args[1].type = Token.FLOAT
        decls[stmt.args[0].args[0]][1] = True
        return

    if stmt.kind == NodeAST.READ:
        for var in stmt.args:
            if not get_id_type(var):
                errors += 'Error: undeclared identificator \'' + ids[var.args[0]] + '\'\n'
            else:
                decls[var.args[0]][1] = True
        return

    if stmt.kind == NodeAST.WRITE:
        for expr in stmt.args:
            verify_expr(expr)
        return

    if stmt.kind == NodeAST.IF:
        condition_type = verify_expr(stmt.args[0])
        if not condition_type or condition_type != Token.BOOL:
            errors += 'Error [line ' + str(stmt.args[0].line) + ']: expected boolean after \'if\''
        verify_stmt(stmt.args[1])
        if stmt.args[2]:
            verify_stmt(stmt.args[2])

    if stmt.kind == NodeAST.FOR:
        verify_stmt(stmt.args[0])
        if stmt.args[0].args[0].type == Token.BOOL:
            errors += 'Error [line ' + str(stmt.args[0].line) + ']: counter must be a number\n'
        verify_expr(stmt.args[1])
        if stmt.args[1].type == Token.BOOL:
            errors += 'Error [line ' + str(stmt.args[0].line) + ']: limit must be a number\n'
        verify_stmt(stmt.args[2])

    if stmt.kind == NodeAST.WHILE:
        verify_expr(stmt.args[0])
        if stmt.args[0].type != Token.BOOL:
            errors += 'Error [line ' + str(stmt.args[0].line) + ']: expected boolean after \'while\''
        verify_stmt(stmt.args[1])

    if stmt.kind == NodeAST.STMT_SEQ:
        for s in stmt.args:
            verify_stmt(s)

def semantic():
    global decls

    decls_from_ast = ast.args[0]
    for decl in decls_from_ast:
        verify_decl(decl)

    stmts_from_ast = ast.args[1]
    for stmt in stmts_from_ast:
        verify_stmt(stmt)

def decls_to_str():
    result = '\n[declarations]\n' +\
             '[Name]\t[Type]\t[Init]\n'
    for var, values in decls.items():
        result += ids[var] + '\t' + keywords[values[0]] + '\t' + str(values[1]) + '\n'
    return result.rstrip('\n')

def init(lexer_filename, parser_filename):
    global numbers, ids, ast
    with open(parser_filename, 'rb') as handle:
        numbers, ast = pickle.load(handle)
    with open(lexer_filename, 'r') as handle:
        handle.readline()
        ids     = handle.readline().split()

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('semantic: Error. Required input file.')
    else:
        lexer_filename = sys.argv[1]
        parser_filename = sys.argv[2]
        if not os.path.isfile(parser_filename):
            print('parser: Error. File \'' + parser_filename + '\' is not exist.')
            sys.exit(1)
        if not os.path.isfile(lexer_filename):
            print('parser: Error. File \'' + lexer_filename + '\' is not exist.')
            sys.exit(1)

        init(lexer_filename, parser_filename)
        semantic()

        if not errors:
            for key in decls:
                if decls[key][0] == Token.BOOL:
                    decls[key][1] = False
                else:
                    decls[key][1] = None
            with open('semantic.out', 'wb') as handle:
                pickle.dump([numbers, decls, ast.args[1]], handle)
            with open('astext.tree', 'w') as handle:
                handle.write(ast_to_string(ast) + '\n')
            sys.exit(0)
        print('\n' + errors)
        sys.exit(1)

