#!/usr/bin/env python

"""
-----------------------------------------------------------------------------
calc.py

A simple calculator with variables.   This is from O'Reilly's
"Lex and Yacc", p. 63.

Class-based example contributed to PLY by David McNab
-----------------------------------------------------------------------------
Compiler Name : Javascript Compiler
Author : Arav De
Created : 3/24/25
Course : CSC 420 S25
Purpose : To make a interpreter for Js
    3/24/25
        * Added to tokens
    3/28/25
        * Added zero divison checking for / and %. // not implemented yet 
    3/30/25 
        * Attempted to write 'write' function, unsuccessfully, not sure why.
        * updated source to be code that is to be tested. Could not figure out how to use an external file
        * uminus implemented effectively
-----------------------------------------------------------------------------
Updates by Deanna M. Wilborne
    2025-03-21
        * converted to an Interpreter for 25SP.CSC420
    2025-03-21
        * added push followed by pop optimization to Emitter class
        * added option to turn off assembly line comments
    2025-03-20
        * converted to use Abstract Syntax Tree for Intermediate Representation
        * added Emitter class to emit MIPS 32 Assembly Language
        * restructured comments output by Emitter class
    2025-03-19
        * updated to create an expression compiler, "exc"
        * removed the exponentiation operator
        * updated to use an abstract syntax tree
        * renamed NAME to ID, which changed t_NAME to t_ID
        * adding keywords required adding the reserved_words dictionary, and updating the t_ID method
        * added lexer token output to the REPL to when debug is set to 1
        * literal characters preferred over tokens where possible to simplify the grammar
    2024-07-27
        * added ctrl-c handling to the interpreter REPL
        * created the yacc_obj field for holding the yacc parser object
    2024-04-29
        * # noinspection PyMethodMayBeStatic added to methods that look static
        * renamed debugfile to debug_file
        * # noinspection SpellCheckingInspection added where needed
        * # noqa added to __init__() for exception handling to supress warning
        * # noinspection PyPep8Naming added where needed
        * single quoted document strings converted to triple quoted
-----------------------------------------------------------------------------
"""

import signal
import sys
import ply.lex as lex
import ply.yacc as yacc
import os
from ReadFile import ReadFile
from AST import AST
from Stack import Stack
# from icecream import ic  # 2024-07-27, DMW, useful for debugging


class Parser:
    """
    Base class for a lexer/parser that has the rules defined as methods
    """
    tokens = ()
    precedence = ()
    repl_prompt: str = None
    yacc_obj: yacc = None

    def __init__(self, **kw):
        self.source_ast = None
        self.debug = kw.get('debug', 1)
        self.names = {}
        try:
            modname = os.path.split(os.path.splitext(__file__)[0])[
                1] + "_" + self.__class__.__name__
        # 2024-04-29, DMW, TODO: figure out the appropriate exceptions to handle and narrow
        except:  # noqa
            modname = "parser" + "_" + self.__class__.__name__
        self.debug_file = modname + ".dbg"
        # print self.debug_file

        # Build the lexer and parser
        self.lexer_obj = lex.lex(module=self, debug=self.debug)
        self.yacc_obj = yacc.yacc(module=self,
                                  debug=self.debug,
                                  debugfile=self.debug_file)

    # the run method is for writing an AST driven interpreter
    # noinspection PyMethodMayBeStatic
    def run(self):
        def signal_handler(sig, frame):
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)

        while True:
            try:
                s = input(self.repl_prompt)
            except EOFError:
                break
            if not s:
                continue

            if self.debug == 1:
                self.lexer_obj.input(s)
                # Tokenize
                while True:
                    tok = self.lexer_obj.token()
                    if not tok:
                        break  # No more input
                    print(tok)

            root = self.yacc_obj.parse(s)
            AST.render_tree(root)

    def make_ast(self, source: str) -> AST:
        return self.yacc_obj.parse(source)

    def compile(self, source: str) -> AST:
        self.source_ast = self.yacc_obj.parse(source)
        # add in the code for emitting assembly language
        return self.source_ast


class Compiler(Parser):

    def __init__(self, repl_prompt: str = "Ready >"):
        super().__init__(debug=1)  # add debug=1 to get .dbg file with grammar
        self.repl_prompt = repl_prompt
        self.object_counter = 0
        self.symbol_table = {}

    def get_obj_ctr(self, label: str) -> str:
        if label in self.symbol_table:
            # this error occurs if a parser production attempts to recreate a previously created global_var
            # solution: test the symbol_table dictionary before calling get_obj_ctr.
            raise ValueError("Compile Error: value previously allocated in global vars: {}".format(label))
        out_label = "{}_{:05d}".format(label, self.object_counter)
        self.object_counter = self.object_counter + 1
        return out_label

    # reserved words are words used in the source code that should not be assigned to.
    # reserved words are generally called keywords, if, for, while, etc. are generally keywords
    reserved_words = {
        'write': 'WRITE',
        'writeln': 'WRITELN',
        'while': 'WHILE',
        'quit': 'QUIT',
        'sin':'SIN',
        'cos':'COS',
        'tan':'TAN',
        'asin':'ASIN',
        'acos':'ACOS',
        'atan':'ATAN',
        'atan2':'ATAN2',
        'if' : 'IF',
        'else':'ELSE',
        'while':'WHILE',
        'for':'FOR',                         #3/24/25 Added tokens 
        'fun':'FUNCTION',
        'return':'RETURN',
        'break':'BREAK',
        'pass':'PASS'
    }

    # tokens are internal names used by the grammar; these differ from reserved words by the fact
    # that they can be used as variable names in the source language the compiler processes; tokens
    # are only used internally as part of the parser, and are not visible to the source language like
    # reserved words (keywords) are.
    # noinspection SpellCheckingInspection
    tokens = [
        'ID', 
        'NUMBER',
        'SQ_STRING',
        'DQ_STRING',
        'FL_DIVIDE',
    ]

    tokens += list(reserved_words.values())

    literals = ['(', ')', '+', '-', '*', '/', '%', '=', '{', '}', '<','>']

    # Tokens
    
    t_WRITELN = r'writeln'
    t_WRITE = r'write'
    t_FL_DIVIDE = r'//'


    # noinspection PyPep8Naming
    # noinspection PyMethodMayBeStatic

    def t_SQ_STRING(self, t):
        r"'[^'\\]*(?:\\.[^'\\]*)*'"
        t.value = { "value": t.value[1: -1], "type": "string" }  # remove quote characters from t.value
        # t.value = t.value[1:-1]
        return t
    
    def t_DQ_STRING(self, t):
        r'"[^"\\]*(?:\\.[^"\\]*)*"'
        t.value = {"value": t.value[1: -1], "type": "string"}
        return t

    def t_NUMBER(self, t):
        r"""\d+(\.\d+)?""" # Added grammar so that function can also use floating point values : 3/30 Arav De
        try:
            t.value = int(t.value)
        except ValueError:
            try:
                t.value = float(t.value)
            except ValueError:
                t.value = 0
        return t

    # create symbol table for use by the emitter for multiple scopes this will need to be done in the emitter
    # this is a global symbol table that doesn't support multiple scopes
    def t_ID(self, t):
        r"""[a-zA-Z_][a-zA-Z0-9_]*"""
        id_name = str(t.value)
        t.type = self.reserved_words.get(id_name, 'ID')  # Check for reserved words, it's an ID if it isn't a name
        if t.type == 'ID':
            if t.value in self.symbol_table:
                symbol = self.symbol_table[id_name]['symbol']
            else:
                symbol = self.get_obj_ctr(id_name)
                self.symbol_table[id_name] = { 'symbol': symbol, 'value': 0 }
            t.value = {'id': t.value, 'symbol': symbol}
        return t

    t_ignore = " \t\v\f"

    # noinspection PyMethodMayBeStatic
    def t_newline(self, t):
        r"""\n+"""
        t.lexer.lineno += t.value.count("\n")

    # noinspection PyMethodMayBeStatic
    def t_error(self, t):
        print("Illegal character '%s'" % t.value[0])
        t.lexer.skip(1)

    # Parsing rules

    # noinspection SpellCheckingInspection
    precedence = (
        ('left', '<'),
        ('left', '+', '-'),
        ('left', '*', '/', '%'),
        # ('left', 'EXP'),
        ('right', 'UMINUS'),
    )

    start = "program"  # this is where the grammar starts, i.e., the start symbol

    def p_program(self, p):
        """program : opt_stmts"""
        p[0] = AST("program", children=[p[1]])

    def p_opt_stmts(self, p):
        """opt_stmts : stmt_list"""
        p[0] = AST("opt_stmts", children=[p[1]])

    def p_opt_stmts2(self, p):
        """opt_stmts : """
        p[0] = AST("nop")

    def p_stmt_list(self, p):
        """stmt_list : statement"""
        p[0] = AST("stmt_list", children=[p[1]])

    def p_stmt_list2(self, p):
        """stmt_list : stmt_list statement"""
        p[0] = AST("stmt_list", children=[p[1], p[2]])

    def p_statement_assign(self, p):
        """statement : ID '=' expr"""
        p[0] = AST("asgn", value=p[1], children=[p[3]])

    def p_statement_write(self, p):
        """statement : WRITE '(' expr ')'
        """
        p[0] = AST("write", children=[p[3]])

    def p_statement_writeln(self, p):
        """statement : WRITELN '(' expr ')'"""
        p[0] = AST("writeln", children=[p[3]])

    def p_statement_while(self, p):
        """statement : WHILE expr '{' stmt_list '}'"""
        p[0] = AST("while", children=[p[2], p[4]])

    # noinspection SpellCheckingInspection
    # noinspection PyMethodMayBeStatic
    def p_expr_binop(self, p):
        """
        expr : expr '+' expr
             | expr '-' expr
             | expr '*' expr
             | expr '/' expr
             | expr '%' expr
             | expr '<' expr
        """
        #              | expr EXP expr
        p[0] = AST("binop", value=p[2], children=[p[1], p[3]])

    # noinspection PyMethodMayBeStatic
    # noinspection SpellCheckingInspection
    def p_expr_uminus(self, p):
        """expr : '-' expr %prec UMINUS"""
        p[0] = AST("uminus", children=[p[2]])

    # noinspection SpellCheckingInspection
    # noinspection PyMethodMayBeStatic
    def p_expr_group(self, p):
        """expr : '(' expr ')'"""
        p[0] = p[2]

    # noinspection PyMethodMayBeStatic
    def p_expr_number(self, p):
        """expr : NUMBER"""
        # p[0] = p[1]
        p[0] = AST("number", value=p[1])

    def p_expr_string(self, p):
        """expr : SQ_STRING
                | DQ_STRING
        """
        p[0] = AST("string", value = p[1])

    def p_expr_id(self, p):
        """expr : ID"""
        p[0] = AST("ID", value = p[1])

    # noinspection PyMethodMayBeStatic
    def p_error(self, p):
        if p:
            print("Syntax error at '%s'" % p.value)
        else:
            print("Syntax error at EOF")


class Interpreter:
    def __init__(self, ast: AST = None, symbol_table: {} = None, comments: bool = True) -> None:
        self.ast = ast
        self.symbol_table = symbol_table
        self.asm_text = ""
        self.comments = comments  # if true, comments are added to assembly language output
        self.exec_ast()

    def exec_ast(self) -> None:
        stack = Stack()

        def exec_children(children: []) -> None:
            for child in children:
                exec_node(child)

        def exec_node(node: AST) -> None:
            match node.name:
                case "program":
                    exec_children(node.children)
                case "opt_stmts": exec_children(node.children)
                case "stmt_list": exec_children(node.children)
                case "asgn":
                        # print(self.symbol_table)
                        # print(self.symbol_table[node.value['id']])
                        exec_children(node.children)
                        self.symbol_table[node.value['id']]['value'] = stack.pop()
                case "while":
                    while True:
                        exec_node(node.children[0])  # holds conditional
                        cond_value = stack.pop()
                        if cond_value:
                            exec_node(node.children[1])
                        else:
                            break
                case "writeln":
                        exec_children(node.children)
                        print(stack.pop())
                case "write":
                        exec_children(node.children) 
                        print(stack.pop(), end = " " )
                case "number":
                        stack.push(node.value)
                case "binop":
                    exec_children(node.children)  # should leave two values on the CPU stack
                    rhs = stack.pop()
                    lhs = stack.pop()
                    match node.value:
                        case "+": stack.push(lhs + rhs)
                        case "-": stack.push(lhs - rhs)
                        case "*": stack.push(lhs * rhs)
                        case "/": 
                            try:
                                stack.push(lhs / rhs)  # Added zero divison checking for / and %. // not implemented yet : 3/28 Arav De
                            except ZeroDivisionError:
                                stack.push(None)
                                print('Cannot divide by zero')
                        case "%":
                            try:
                                stack.push(lhs % rhs)   
                            except ZeroDivisionError:
                                stack.push(None)
                                print('Cannot divide by zero')
                        case "<": stack.push(lhs < rhs)  # I don't remember if I added this, leaving comment just in case : 3/30 Arav De
                        case ">": stack.push(lhs > rhs)
                        case _: raise SyntaxWarning("Binary operator not implemented: {}".format(node.name))
                case "ID":
                    stack.push(self.symbol_table[node.value['id']]['value'])
                case "uminus":
                    exec_node(node.children[0])
                    stack.push(-stack.pop()) # uminus implemented effectively : 3/30 Arav De
                case "string":
                    stack.push(node.value["value"])
                case _:
                    raise SyntaxWarning("Interpreter error: AST node unknown: {}".format(node.name))

        # Interpret the AST
        exec_node(self.ast)


if __name__ == '__main__':
    def main():
        # Using both user input and file input.
        sourceFile = input("Enter your file or statements: ")
        if os.path.isfile(sourceFile):
            source = ReadFile(sourceFile)
            cmp_obj = Compiler()  # yes, this is a compiler, translates source to AST
            ast = cmp_obj.make_ast(source.raw_text)  # parse source and create AST, an intermediate representation
            AST.render_tree(ast)
            ast_inter = Interpreter(ast, cmp_obj.symbol_table)
            print(cmp_obj.symbol_table) #Printing out data structure with values stored : 3/30 Arav De
        else:
            source = sourceFile 
            cmp_obj = Compiler()  # yes, this is a compiler, translates source to AST
            ast = cmp_obj.make_ast(source)  # parse source and create AST, an intermediate representation
            AST.render_tree(ast)
            ast_inter = Interpreter(ast, cmp_obj.symbol_table)
            print(cmp_obj.symbol_table) #Printing out data structure with values stored : 3/30 Arav De
    main()
