#!/usr/bin/env python

"""
-----------------------------------------------------------------------------
calc.py

A simple calculator with variables.   This is from O'Reilly's
"Lex and Yacc", p. 63.

Class-based example contributed to PLY by David McNab
-----------------------------------------------------------------------------

-----------------------------------------------------------------------------
Updates by Deanna M. Wilborne
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
        self.debug = kw.get('debug', 0)
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
        lex.lex(module=self, debug=self.debug)
        self.yacc_obj = yacc.yacc(module=self,
                                  debug=self.debug,
                                  debugfile=self.debug_file)

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
            self.yacc_obj.parse(s)


class Interpreter(Parser):

    def __init__(self, repl_prompt: str = "Ready >"):
        super().__init__()  # add debug=1 to get .dbg file with grammar
        self.repl_prompt = repl_prompt

    # helper function create a Python int or float as needed
    # 2024-04-27, DMW, converted return value to dictionary
    @staticmethod
    def string_to_number(s):
        try:
            # ans = {'value': int(s), 'type': 'int'}
            ans = int(s)
        except ValueError:
            # ans = {'value': float(s), 'type': 'float'}
            ans = float(s)

        return ans

    # noinspection SpellCheckingInspection
    tokens = (
        'NAME', 'NUMBER',
        'PLUS', 'MINUS', 'EXP', 'TIMES','FL_DIVIDE', 'DIVIDE','EQUALS',
        'LPAREN', 'RPAREN'
    )

    # Tokens

    t_PLUS = r'\+'
    t_MINUS = r'-'
    t_EXP = r'\*\*'
    t_TIMES = r'\*'
    t_FL_DIVIDE = r'//'
    t_DIVIDE = r'/'
    t_EQUALS = r'='
    t_LPAREN = r'\('
    t_RPAREN = r'\)'
    t_NAME = r'[a-zA-Z_][a-zA-Z0-9_]*'
    

    # noinspection PyPep8Naming
    # noinspection PyMethodMayBeStatic
    # 2025-03-10, DMW, remarked (commented) out the following method
    # def t_NUMBER(self, t):
    #     r"""\d+"""
    #     try:
    #         t.value = int(t.value)
    #     except ValueError:
    #         print("Integer value too large %s" % t.value)
    #         t.value = 0
    #     # print "parsed number %s" % repr(t.value)
    #     return t

    # 2025-03-10, DMW, added the following and updated method from CSC486 Compiler Course
    # 2024-04-27, DMW, added source line number and character position within source relative to
    #                  the beginning of the source to dictionary for the number token
    # noinspection PyPep8Naming
    # noinspection PySingleQuotedDocstring
    def t_NUMBER(self, t):
        r'[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?'  # 2024-02-14, DMW, we'll save floating point for later
        # https://www.regular-expressions.info/floatingpoint.html
        # r'\d+'  # original regular expression -- allow integers only
        # token_value = Interpreter.string_to_number(t.value)  # int(t.value)
        # token_value['line_no'] = t.lexer.lineno
        # token_value['src_pos'] = t.lexpos
        t.value = Interpreter.string_to_number(t.value)

        return t

    t_ignore = " \t"

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
        ('left', 'PLUS', 'MINUS'),
        ('left', 'TIMES', 'DIVIDE'),
        ('left', 'FL_DIVIDE'),
        ('left', 'EXP'),
        ('right', 'UMINUS'),
    )

    def p_statement_assign(self, p):
        """statement : NAME EQUALS expression"""
        self.names[p[1]] = p[3]

    # noinspection PyMethodMayBeStatic
    def p_statement_expr(self, p):
        """statement : expression"""
        print(p[1], 'Hekko')

    def p_statement_quit(self, p):
        '''statement : NAME'''
        if p[1] == "quit":
            print("Exiting...")
            sys.exit()
        else:
            try:
                p[0] = self.names[p[1]]
            except LookupError:
                print(f"Undefined name '{p[1]}'")
                p[0] = 0
    # noinspection SpellCheckingInspection
    # noinspection PyMethodMayBeStatic
    def p_expression_binop(self, p):
        """
        expression : expression PLUS expression
                   | expression MINUS expression
                   | expression TIMES expression
                   | expression DIVIDE expression
                   | expression EXP expression
                   | expression FL_DIVIDE expression
        """
        # print [repr(p[i]) for i in range(0,4)]
        if p[2] == '+':
            p[0] = p[1] + p[3]
        elif p[2] == '-':
            p[0] = p[1] - p[3]
        elif p[2] == '*':
            p[0] = p[1] * p[3]
        elif p[2] == '/':
            try:
                p[0] = p[1] / p[3]
            except ZeroDivisionError:
                print("Division by zero is not a valid mathematical operation")
                p[0] = "undefined"
        elif p[2] == '**':
            p[0] = p[1] ** p[3]
        elif p[2] == '//':
            try:
                p[0] = p[1] // p[3]
            except ZeroDivisionError:
                print("Division by zero is not a valid mathematical operation")
                p[0] = "undefined"
    
    # noinspection PyMethodMayBeStatic
    # noinspection SpellCheckingInspection
    def p_expression_uminus(self, p):
        """expression : MINUS expression %prec UMINUS"""
        p[0] = -p[2]

    # noinspection SpellCheckingInspection
    # noinspection PyMethodMayBeStatic
    def p_expression_group(self, p):
        """expression : LPAREN expression RPAREN"""
        p[0] = p[2]

    # noinspection PyMethodMayBeStatic
    def p_expression_number(self, p):
        """expression : NUMBER"""
        p[0] = p[1]

    def p_expression_name(self, p):
        """expression : NAME"""
        try:
            p[0] = self.names[p[1]]
        except LookupError:
            print("Undefined name '%s'" % p[1])
            p[0] = 0

    # noinspection PyMethodMayBeStatic
    def p_error(self, p):
        if p:
            print("Syntax error at '%s'" % p.value)
        else:
            print("Syntax error at EOF")


if __name__ == '__main__':
    calc = Interpreter(repl_prompt="Calc >")
    # ic(calc.yacc_obj)  # show yacc_obj created
    calc.run()
