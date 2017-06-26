#!/usr/bin/python3
# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8

TABLE_KEYWORD   = 1
TABLE_SEPARATOR = 2
TABLE_NUMBER    = 3
TABLE_ID        = 4

class Token:
    PROGRAM, BEGIN, END, VAR, TRUE, FALSE, ASS, IF, ELSE, THEN, \
    FOR, TO, DO, WHILE, READ, WRITE, INT, FLOAT, BOOL, AND, OR, NOT, \
    PLUS, MINUS, EQUAL, LESS, GREAT, MUL, DIV, LPAR, RPAR, SEMICOLON, DOT, \
    COLON, LESSEQUAL, GREATEQUAL, NOTEQUAL, COMMA = range(38)

    value = None

    def __init__(self, table, index):
        self.table = table
        self.index = index

        if self.table == TABLE_SEPARATOR:

            self.value = index + self.PLUS
        elif self.table == TABLE_KEYWORD:
            self.value = index

############################################
#            AST Specification                   
############################################

# kind: NUMBER,   args: 0 - index
# kind: ID,       args: 0 - index
# kind: BOOL,     args: 0 - index
# kind: OP,       args: 0 - TSEPARATOR/TKEYWORD, 1 - index

# kind: EXPR,     args: 0 - operation, 1 - left EXRP, 2 - right EXPR/None(unary operation)
# kind: STMT_SEQ, args: 0 - STMT list
# kind: ASS,      args: 0 - id, 1 - EXPR
# kind: IF,       args: 0 - EXPR(condition), 1 - STMT, 2 - STMT(else)/None
# kind: WRITE,    args: 0 - EXPR list
# kind: READ,     args: 0 - id list
# kind: FOR,      args: 0 - ASS(begin), 1 - EXPR(end), 2 - STMT_SEQ
# kind: WHILE,    args: 0 - EXPR(condition), 1 - STMT_SEQ
# kind: PROGRAM,  args: 0 - declarations list, 1 - STMT_SEQ 

############################################

class NodeAST:
    PROGRAM, DECLARATIONS, \
    NUMBER, ID, BOOL, OP, EXPR, \
    WHILE, FOR, IF, ASS, READ, WRITE, STMT_SEQ = range(14)

    def __init__(self, kind, line, *args):
        self.kind = kind
        self.line = line
        self.args = list(args)
        self.type = None
