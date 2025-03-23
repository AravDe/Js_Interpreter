from enum import Enum

class tokenKind(Enum):

        IDENTIFIER = 'IDENTIFIER'  
        NUMBER = 'NUMBER' 
        STRING = 'STRING'
        
        PLUS = 'PLUS'  
        MINUS = 'MINUS'  
        EXP = 'EXP' 
        TIMES = 'TIMES' 
        FL_DIVIDE = 'FL_DIVIDE'  
        DIVIDE = 'DIVIDE' 
        ASSIGN = 'ASSIGN'  # =
        INCREMENT = 'INCREMENT' 
        DECREMENT = 'DECREMENT' 

        LPAREN = 'LPAREN'  
        RPAREN = 'RPAREN' 
        RCURLY = 'RCURLY' 
        LCURLY = 'LCURLY' 


        # RESERVED WORDS
        FUNCTION = 'FUNCTION' 
        RETURN = 'RETURN' 
        BREAK = 'BREAK' 
        PASS = 'PASS'
        IF = 'IF' 
        ELSE = 'ELSE' 
        WHILE = 'WHILE' 
        FOR = 'FOR' 

        EQUALS = 'EQUALS'  # ==
        LESSER = 'LESSER' 
        LESSER_EQ = 'LESSER_EQ'
        GREATER = 'GREATER' 
        GREATER_EQ = 'GREATER_EQ' 
        NOT = 'NOT'  
        NOT_EQ = 'NOT_EQ' 
        AND = 'AND' 
        OR = 'OR'
class Token:
    def __init__(self, value, kind):
        self.kind = kind  
        self.value = value

def tokenCnvrtStr(tokenKind)->str:
    if tokenKind == 'IDENTIFIER':
        return 'IDENTIFIER'
    elif tokenKind == 'STRING':
        return 'STRING'
    elif tokenKind == 'NUMBER':
        return 'NUMBER'
    else:
        return 'UNKNOWN'
def debug(token):
    kind = token.kind
    if kind == "IDENTIFIER" or kind == "NUMBER" or kind == "STRING":
          print(tokenCnvrtStr(token.kind), token.value)
    else:
         print(tokenCnvrtStr(token.kind)) 
