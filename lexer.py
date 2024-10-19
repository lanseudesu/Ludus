import string

arith_op = '+-*/%^'
relat_op = '<>=!'
numlit_delim = arith_op + relat_op + '){}:], \n'

# constants

DIGITS = '0123456789'
LETTERS = string.ascii_letters
LETTERS_DIGITS = LETTERS + DIGITS

# tokens

TT_INT		  = 'hp_literal'
TT_FLOAT      = 'xp_literal'
TT_STRING     = 'comms_literal'
TT_COLON      = ':'
TT_PLUS       = '+'
TT_MINUS      = '-'
TT_MUL        = '*'
TT_DIV        = '/'
TT_POW        = '^'
TT_LPAREN     = '('
TT_RPAREN     = ')'
TT_LSQUARE    = '['
TT_RSQUARE    = ']'
TT_LCURLY     = '{'  
TT_RCURLY     = '}'  
TT_EE         = '=='
TT_NE         = '!='
TT_LT         = '<'
TT_GT         = '>'
TT_LTE        = '<='
TT_GTE        = '>='
TT_COMMA	  = ','
TT_NEWLINE	  = 'newline'


# reserved words

KEYWORDS = [
    # terminator
    'gameOver',
    # data types
    'xp',
    'hp',
    'comms',
    'flag',
    # bool
    'true',
    'false',
    # struct words
    'build',
    'access',
    'default',
    # logical 
    'AND',
    'OR',
    # constants declaration
    'immo',
    # conditional
    'if',
    'elif',
    'else',
    'flank',
    'choice',
    'backup',
    # looping
    'for',
    'while',
    'grind',
    # loop control
    'checkpoint',
    'resume',
    # return
    'recall',
    # others
    'dead',
    'generate',
    'play',
    '*args',
    # built-in funcs
    'load',
    'loadNum'
    'shoot',
    'shootNxt',
    'rounds',
    'wipe',
    'join',
    'drop',
    'seek',
    'levelUp',
    'levelDown',
]

# errors

class Error:
    def __init__(self, pos_start, pos_end, error_name, details):
        self.pos_start = pos_start
        self.pos_end = pos_end
        self.error_name = error_name
        self.details = details
    
    def as_string(self):
        result  = f'{self.error_name}: {self.details}\n'
        result += f'File {self.pos_start.fn}, line {self.pos_start.ln + 1}'
        return result

class IllegalCharError(Error):
    def __init__(self, pos_start, pos_end, details):
        super().__init__(pos_start, pos_end, 'Illegal Character', details)

# position

class Position:
    def __init__(self, idx, ln, col, fn, ftxt):
        self.idx = idx
        self.ln = ln
        self.col = col
        self.fn = fn
        self.ftxt = ftxt

    def advance(self, current_char):
        self.idx += 1
        self.col += 1

        if current_char == '\n':
            self.ln += 1
            self.col = 0

        return self

    def copy(self):
        return Position(self.idx, self.ln, self.col, self.fn, self.ftxt)


class Token:
    def __init__(self, lexeme, token):
        self.lexeme = lexeme
        self.token = token
    
    def __repr__(self):
        return f'{self.lexeme}:{self.token}'

# lexer

class Lexer:
    def __init__(self, fn, text):
        self.fn = fn
        self.text = text
        self.pos = Position(-1, 0, -1, fn, text)
        self.identifier_map = {}
        self.current_id = 1
        self.current_char = None
        self.advance()
    
    def advance(self):
        self.pos.advance(self.current_char)
        self.current_char = self.text[self.pos.idx] if self.pos.idx < len(self.text) else None

    def add_error_with_position(self, error_msg):
        return f"{error_msg} at line {self.pos.ln + 1}, column {self.pos.col + 1}"

    def make_tokens(self):
        tokens = []
        errors = []
    
        while self.current_char is not None:
            if self.current_char in ' \t':
                self.advance()
            elif self.current_char == '#':
                self.skip_comment()
            elif self.current_char == '\n':
                tokens.append(Token('\\n', TT_NEWLINE))
                self.advance()
            elif self.current_char in DIGITS:
                result, error = self.make_number()

                if error:
                   errors.extend(error)
                   continue  

                if self.current_char is not None and self.current_char not in numlit_delim:
                    errors.append(self.add_error_with_position(f"Invalid delimiter for {result.lexeme}. Cause: '{self.current_char}'"))
                    self.advance()
                else:
                    tokens.append(result)
                    self.advance()
            elif self.current_char in LETTERS or self.current_char == '_':
                tokens.append(self.make_identifier())
            elif self.current_char == '"':
                tokens.append(self.make_string())
            elif self.current_char == '+':
                tokens.append(Token(TT_PLUS, TT_PLUS))
                self.advance()
            elif self.current_char == '-':
                tokens.append(Token(TT_MINUS, TT_MINUS))
                self.advance()
            elif self.current_char == '*':
                tokens.append(Token(TT_MUL, TT_MUL))
                self.advance()
            elif self.current_char == '/':
                tokens.append(Token(TT_DIV, TT_DIV))
                self.advance()
            elif self.current_char == '^':
                tokens.append(Token(TT_POW, TT_POW))
                self.advance()
            elif self.current_char == '(':
                tokens.append(Token(TT_LPAREN, TT_LPAREN))
                self.advance()
            elif self.current_char == ')':
                tokens.append(Token(TT_RPAREN, TT_RPAREN))
                self.advance()
            elif self.current_char == '[':
                tokens.append(Token(TT_LSQUARE, TT_LSQUARE))
                self.advance()
            elif self.current_char == ']':
                tokens.append(Token(TT_RSQUARE, TT_RSQUARE))
                self.advance()
            elif self.current_char == '{':
                tokens.append(Token(TT_LCURLY, TT_LCURLY))
                self.advance()
            elif self.current_char == '}':
                tokens.append(Token(TT_RCURLY, TT_RCURLY))
                self.advance()
            elif self.current_char == '!':
                result, error = self.make_not_equals()
                if error: return [], error
                tokens.append(result)
            elif self.current_char == '=':
                tokens.append(self.make_equals())
                self.advance()
            elif self.current_char == '<':
                tokens.append(self.make_less_than())
            elif self.current_char == '>':
                tokens.append(self.make_greater_than())
            elif self.current_char == ',':
                tokens.append(Token(TT_COMMA, TT_COMMA))
                self.advance()
            elif self.current_char == ':':
                tokens.append(Token(TT_COLON, TT_COLON))
                self.advance()
            else:
                #todo mag-eextend lng error
                # pos_start = self.pos.copy()
                # char = self.current_char
                self.advance()
                #return [], IllegalCharError(pos_start, self.pos, "'" + char + "'")
        
        return tokens, errors
    
    def make_number(self):
        num_str = ''
        dot_count = 0
        int_len = 0
        dec_len = 0
        errors = []

        while self.current_char != None and self.current_char in DIGITS + '.':
            if self.current_char == '.':
                if dot_count == 1:
                    num_str += self.current_char
                    self.advance()
                    while self.current_char is not None and self.current_char not in numlit_delim:
                        num_str += self.current_char
                        self.advance()
                    errors.append(f"Too many decimal points in {num_str} at line {self.pos.ln + 1}, column {self.pos.col - len(num_str) + 1}")
                    return [], errors
                dot_count += 1
                num_str += '.'
            else:
                # have a number after '.' and should be less than 8
                if dot_count == 0:
                    if int_len < 9:
                        num_str += self.current_char
                        int_len += 1
                    else:
                        return Token(int(num_str), TT_INT), errors
                else:    
                    if dec_len < 7:
                        num_str += self.current_char
                        dec_len += 1
                    else:
                        return Token(float(num_str), TT_FLOAT), errors

            self.advance()
        
        if dot_count > 0 and num_str.endswith('.'):
            errors.append(f"Invalid number '{num_str}' at line {self.pos.ln + 1}, column {self.pos.col - len(num_str) + 1}. Trailing decimal point without digits.")
            return [], errors 

        token_type = TT_FLOAT if dot_count > 0 else TT_INT
        value = float(num_str) if dot_count > 0 else int(num_str)

        return Token(value, token_type), errors
        
    def make_identifier(self):
        id_str = ''

        while self.current_char != None and self.current_char in LETTERS_DIGITS + '_':
            id_str += self.current_char
            self.advance()

        if id_str in KEYWORDS:
            return Token(id_str, id_str)
        else:
            return Token(id_str, self.identifiers(id_str))
        
    def identifiers(self, id_str):
        if id_str not in self.identifier_map:
            self.identifier_map[id_str] = f'id{self.current_id}'
            self.current_id += 1

        return self.identifier_map[id_str]
    
    def make_string(self):
        string = ''
        escape_character = False
        self.advance()

        escape_characters = {
            'n': '\n',
            't': '\t'
        }

        while self.current_char != None and (self.current_char != '"' or escape_character):
            if escape_character:
                string += escape_characters.get(self.current_char, self.current_char)
                escape_character = False
            else:
                if self.current_char == '\\':
                    escape_character = True
                else:
                    string += self.current_char
            self.advance()

        self.advance()
        return Token(string, TT_STRING)
        
    def make_not_equals(self):
        pos_start = self.pos.copy()
        self.advance()

        if self.current_char == '=':
            self.advance()
            return Token(TT_NE, TT_NE), None

        # self.advance()
        # return None, ExpectedCharError(pos_start, self.pos, "'=' (after '!')")

    def make_equals(self):
        #tok_type = TT_EQ
        self.advance()

        if self.current_char == '=':
            self.advance()
            tok_type = TT_EE

        return Token(tok_type, tok_type)

    def make_less_than(self):
        tok_type = TT_LT
        self.advance()

        if self.current_char == '=':
            self.advance()
            tok_type = TT_LTE

        return Token(tok_type, tok_type)

    def make_greater_than(self):
        tok_type = TT_GT
        self.advance()

        if self.current_char == '=':
            self.advance()
            tok_type = TT_GTE

        return Token(tok_type, tok_type)
    
    def make_newLine(self):
        tok_type = TT_NEWLINE
        return Token(tok_type, tok_type)

    def skip_comment(self):
        self.advance()

        while self.current_char != '\n':
            self.advance()

        self.advance()
    
# run

def run(fn, text):
    lexer = Lexer(fn, text)
    tokens, error = lexer.make_tokens()

    return tokens, error

