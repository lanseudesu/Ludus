import string

### CONSTANTS ###

NUM             = '0123456789'
ALPHA           = string.ascii_letters
ALPHANUM        = ALPHA + NUM
ASCII_PRINTABLE = ''.join(chr(i) for i in range(32, 127))
NUM_TO_6        = '0123456' 

### DELIMITERS ###

arith_op   = '+-*/%^'
relat_op   = '<>=!'
whitespace = '# \n'

id_delim       = arith_op + relat_op + whitespace + '.,:[{}()'
numlit_delim   = arith_op + relat_op + whitespace + '){}:],'
commslit_delim = whitespace + ':,={[)'
flag_delim     = whitespace + ',:])'

lparen_delim   = ALPHANUM + '_ )"+-!~'
rparen_delim   = whitespace + arith_op + relat_op + '{})],.'
lcurly_delim   = whitespace + ALPHANUM + '_{(~+-'
rcurly_delim   = whitespace + ASCII_PRINTABLE
lbracket_delim = ALPHANUM + '_ ]'
rbracket_delim = whitespace + arith_op + relat_op + ',[:).}'
comma_delim    = ALPHANUM + ' _'
period_delim   = ALPHA + '_'  

delim1 = whitespace + ','
delim2  = ' {'
delim6  = ALPHANUM + '_( '
delim7  = whitespace + ALPHANUM + '_}()'
delim9  = ALPHANUM + ' _"~+-(!'
delim10 = ALPHANUM + ' _("'
delim11 = ALPHA + '_('
delim12 = ALPHANUM + '_(.'

### TOKENS ###

# literals:
TT_HP	      = 'hp_ltr'
TT_NHP        = 'nhp_ltr'
TT_XP         = 'xp_ltr'
TT_NXP        = 'nxp_ltr'
TT_COMMS      = 'comms_ltr'

# unary operators:
TT_INC        = 'increment'
TT_DEC        = 'decrement'
TT_NEG        = 'negate'

# arithmetic operators:
TT_PLUS       = 'plus'
TT_MINUS      = 'minus'
TT_MUL        = 'multiply'
TT_DIV        = 'divide'
TT_MOD        = 'modulus'
TT_POW        = 'power'

# relational operators:
TT_EE         = 'equals equals'
TT_NE         = 'not equals'
TT_LT         = 'less than'
TT_GT         = 'greater than'
TT_LTE        = 'greater than or equal'
TT_GTE        = 'less than or equal'

# logical operators:
TT_AND        = 'AND'
TT_OR         = 'OR'
TT_NOT        = 'NOT'

# assignment operators:
TT_COLON      = 'colon'
TT_PLUS_EQ    = 'plus and equals'
TT_MINUS_EQ   = 'minus and equals'
TT_MUL_EQ     = 'multiply and equals'
TT_DIV_EQ     = 'divide and equals'
TT_MOD_EQ     = 'modulus and equals'

# other symbols:
TT_LPAREN     = 'left parenthesis'
TT_RPAREN     = 'right parenthesis'
TT_LSQUARE    = 'left square bracket'
TT_RSQUARE    = 'right square bracket'
TT_LCURLY     = 'left curly braces'  
TT_RCURLY     = 'right curly braces'  
TT_COMMA	  = 'comma'
TT_PERIOD	  = 'period'

TT_KEYWORDS   = 'keyword'

TT_NEWLINE	  = 'newline'

TT_XP_FORMATTING = 'xp formatting'

# reserved words and their delims

KEYWORDS_DELIMS = {
    # terminator
    'gameOver'  : whitespace,
    # data types
    'xp'        : ' ',
    'hp'        : ' ',
    'comms'     : ' ',
    'flag'      : ' ',
    # bool
    'true'      : flag_delim,
    'false'     : flag_delim,
    # struct words
    'build'     : ' ',
    'access'    : ' ',
    # logical 
    'AND'       : ' ',
    'OR'        : ' ',
    # constants declaration
    'immo'      : ' ',
    # conditional
    'if'        : ' ',
    'elif'      : ' ',
    'else'      : delim2,
    'flank'     : ' ',
    'choice'    : ' ',
    'backup'    : ':',
    # looping
    'for'       : ' ',
    'while'     : ' ',
    'grind'     : delim2,
    # loop control
    'checkpoint': whitespace,
    'resume'    : whitespace,
    # return
    'recall'    : ' ',
    # others
    'dead'      : delim1,
    'generate'  : ' ',
    'play'      : '(',
    # built-in funcs
    'load'      : '(',
    'loadNum'   : '(',
    'shoot'     : '(',
    'shootNxt'  : '(',
    'rounds'    : '(',
    'wipe'      : '(',
    'join'      : '(',
    'drop'      : '(',
    'seek'      : '(',
    'levelUp'   : '(',
    'levelDown' : '(',
    'toHp'      : '(',
    'toXp'      : '(',
    'toComms'   : '(',
}

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
    
    def invalid_delim_error(self, lexeme):
        error_msg = f"Invalid delimiter for '{lexeme}'. Cause: '{self.current_char}'"
        return f"{error_msg} at line {self.pos.ln + 1}, column {self.pos.col + 1}"
    
    def process_token(self, lexeme, token, valid_delims, errors, tokens):
        if (self.current_char == '\n' and '\n' not in valid_delims) or (self.current_char is None and '\n' not in valid_delims):
            error_msg = f"Invalid delimiter for '{lexeme}'. Cause: '\\n'"
            error_msg = f"{error_msg} at line {self.pos.ln + 1}, column {self.pos.col + 1}"
            self.advance()
            errors.append(error_msg)
        elif self.current_char is not None and self.current_char not in valid_delims:
            errors.append(self.invalid_delim_error(lexeme))
            self.advance()
        else:
            tokens.append(Token(lexeme, token)) 

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

            elif self.current_char in NUM:
                result, error = self.make_number('')

                if error:
                   errors.extend(error)
                   continue  
                
                self.process_token(result.lexeme, result.token, numlit_delim, errors, tokens)

            elif self.current_char in ALPHA or self.current_char == '_':
                result, error, is_keywords = self.make_identifier()

                if error:
                   errors.extend(error)
                   continue

                if not is_keywords:   
                    self.process_token(result.lexeme, result.token, id_delim, errors, tokens)
                else:
                    self.process_token(result.lexeme, result.token, KEYWORDS_DELIMS[result.lexeme], errors, tokens)
            
            elif self.current_char == '"':
                result, error = self.make_string()

                if error:
                   errors.extend(error)
                   continue

                self.process_token(result.lexeme, result.token, commslit_delim, errors, tokens)

            elif self.current_char in '+-':
                token_map = {
                    '+': [(TT_PLUS_EQ, '=', delim6), (TT_INC, '+', delim7), (TT_PLUS, None, delim6)],
                    '-': [(TT_MINUS_EQ, '=', delim6), (TT_DEC, '-', delim7), (TT_MINUS, None, delim6)],
                }
                char = self.current_char
                self.advance()
                for token_type, next_char, valid_delims in token_map[char]:
                    if next_char is None:  
                        self.process_token(char, token_type, valid_delims, errors, tokens)
                        break
                    elif self.current_char == next_char:  
                        self.advance()
                        self.process_token(char + next_char, token_type, valid_delims, errors, tokens)
                        break

            elif self.current_char in '*/%<>':
                token_map = {
                    '*': [(TT_MUL_EQ, '='), (TT_MUL, None)],
                    '/': [(TT_DIV_EQ, '='), (TT_DIV, None)],
                    '%': [(TT_MOD_EQ, '='), (TT_MOD, None)],
                    '<': [(TT_LT, '='), (TT_LTE, None)],
                    '>': [(TT_GT, '='), (TT_GTE, None)],
                }
                char = self.current_char
                self.advance()
                for token_type, next_char in token_map[char]:
                    if next_char is None:  
                        self.process_token(char, token_type, delim6, errors, tokens)
                        break
                    elif self.current_char == '=':  
                        self.advance()
                        self.process_token(char + next_char, token_type, delim6, errors, tokens)
                        break

            elif self.current_char == '~':
                num_str = '~'
                self.advance()
                if self.current_char in NUM + '.':
                    result, error = self.make_number(num_str)

                    if error:
                        errors.extend(error)
                        continue  

                    self.process_token(result.lexeme, result.token, numlit_delim, errors, tokens)
                else: 
                    self.process_token('~', TT_NEG, delim12, errors, tokens)

            elif self.current_char in '^:()[]{},':
                token_map = {
                    '^': [(TT_POW, delim6)],
                    ':': [(TT_COLON, delim9)],
                    '(': [(TT_LPAREN, lparen_delim)],
                    ')': [(TT_RPAREN, rparen_delim)],
                    '[': [(TT_LSQUARE, lbracket_delim)],
                    ']': [(TT_RSQUARE, rbracket_delim)],
                    '{': [(TT_LCURLY, lcurly_delim)],
                    '}': [(TT_RCURLY, rcurly_delim)],
                    ',': [(TT_COMMA, comma_delim)],
                }
                char = self.current_char
                self.advance()
                for token_type, valid_delims in token_map[char]:
                    self.process_token(char, token_type, valid_delims, errors, tokens)
                    break

            elif self.current_char == '.':
                self.advance()

                if self.current_char is not None and self.current_char in NUM_TO_6:
                    result = self.current_char
                    self.advance()
                    if self.current_char is not None and self.current_char == 'f':
                        result = '.' + result + 'f'
                        self.advance()
                        self.process_token(result, TT_XP_FORMATTING, '}', errors, tokens)
                    else:
                        result, error = self.make_number('.' + result)

                        if error:
                            errors.extend(error)
                            continue  

                        self.process_token(result.lexeme, result.token, numlit_delim, errors, tokens)        

                elif self.current_char is not None and self.current_char in NUM:
                    result, error = self.make_number('.')

                    if error:
                        errors.extend(error)
                        continue  

                    self.process_token(result.lexeme, result.token, numlit_delim, errors, tokens)

                else:
                    self.process_token('.', TT_PERIOD, period_delim, errors, tokens)

            elif self.current_char in '=&|':
                token_map = {
                    '=': [(TT_EE, delim6)],
                    '&': [(TT_AND, ' ')],
                    '|': [(TT_OR, ' ')],
                }
                char = self.current_char
                self.advance()
                for token_type, valid_delims in token_map[char]:
                    if self.current_char == char:
                        self.advance()
                        self.process_token(char + char, token_type, valid_delims, errors, tokens)
                    else:
                        errors.append(f"Invalid character error at line {self.pos.ln+1}, column {self.pos.col}. Cause: '{char}'")

            elif self.current_char == '!':
                char = self.current_char
                self.advance()
                if self.current_char == '=':
                    self.advance()
                    self.process_token('!=', TT_NE, delim10, errors, tokens)
                else:
                    self.process_token('!', TT_NOT, delim11, errors, tokens)   
            else:
                #todo mag-eextend lng error
                # pos_start = self.pos.copy()
                # char = self.current_char
                self.advance()
                #return [], IllegalCharError(pos_start, self.pos, "'" + char + "'")
        
        return tokens, errors
    
    def make_number(self, num_str): 
        negate = False
        dot_count = 0
        int_len = 0
        dec_len = 0
        errors = []

        def add_error(message):
            errors.append(f"{message} at line {self.pos.ln + 1}, column {self.pos.col - len(num_str) + 1}")
        
        if num_str != '':
            if num_str == '~':
                negate = True
            else:
                dot_count = 1
                dec_len = 1    
            
        while self.current_char is not None and self.current_char in NUM + '.':
            if self.current_char == '.':
                if dot_count == 1:  
                    num_str += self.current_char
                    self.advance()
                    while self.current_char is not None and self.current_char not in numlit_delim:
                        num_str += self.current_char
                        self.advance()
                    add_error(f"Too many decimal points in {num_str}")
                    return [], errors
                dot_count += 1
                num_str += '.'
            else:  
                if dot_count == 0:  
                    if int_len < 10:
                        num_str += self.current_char
                        int_len += 1
                    else:  
                        while self.current_char is not None and self.current_char not in numlit_delim:
                            num_str += self.current_char
                            self.advance()
                        add_error(f"Maximum number of whole numbers reached in {num_str}")
                        return [], errors
                else:  
                    if dec_len < 7:
                        num_str += self.current_char
                        dec_len += 1
                    else:  
                        while self.current_char is not None and self.current_char not in numlit_delim:
                            num_str += self.current_char
                            self.advance()
                        add_error(f"Maximum number of decimal numbers reached in {num_str}")
                        return [], errors
            self.advance()

        if dot_count > 0 and num_str.endswith('.'):
            add_error(f"Invalid number '{num_str}'. Trailing decimal point without digits")
            return [], errors
        
        if not negate:
            token_type = TT_XP if dot_count > 0 else TT_HP
        else:
            if num_str == '~0':
                add_error(f"Invalid number '{num_str}'. Zero can't be negative")
                return [], errors
            token_type = TT_NXP if dot_count > 0 else TT_NHP

        return Token(num_str, token_type), errors

    def make_identifier(self): # todo
        id_str = ''
        id_len = 0
        errors = []
        is_keywords = False

        def add_error(message):
            errors.append(f"{message} at line {self.pos.ln + 1}, column {self.pos.col - len(id_str) + 1}")

        while self.current_char != None and self.current_char in ALPHANUM + '_':
            if id_len < 30:
                id_str += self.current_char
                id_len += 1
                self.advance()
            else:
                while self.current_char is not None and self.current_char not in id_delim:
                        id_str += self.current_char
                        self.advance()
                add_error(f"Maximum number characters reached in {id_str}")
                return [], errors, None
            
        if id_str in KEYWORDS_DELIMS:
            is_keywords = True
            return Token(id_str, TT_KEYWORDS), errors, is_keywords
        else:
            return Token(id_str, self.identifiers(id_str)), errors, is_keywords

    def identifiers(self, id_str):
        if id_str not in self.identifier_map:
            self.identifier_map[id_str] = f'identifier_{self.current_id}'
            self.current_id += 1

        return self.identifier_map[id_str]

    def make_string(self): 
        string = ''  
        escape_character = False  
        errors = []
        self.advance()  

        escape_characters = {
            'n': '\n',   
            't': '\t',   
            '{': '{',    
            '}': '}',    
            '"': '"',    
            '\\': '\\' 
        }

        while self.current_char is not None:
            if escape_character:
                resolved_char = escape_characters.get(self.current_char, self.current_char)
                string += resolved_char 
                escape_character = False  
            else:
                if self.current_char == '\\':  
                    escape_character = True
                elif self.current_char == '"':  
                    self.advance() 
                    return Token('"' + string + '"', TT_COMMS), errors  
                elif self.current_char == '\n':
                    errors.append(f'Unclosed string literal "{string} at line {self.pos.ln + 1}, column {self.pos.col - len(string)}')
                    return [], errors
                else:
                    string += self.current_char  
            self.advance()

        errors.append(f'Unclosed string literal "{string} at line {self.pos.ln + 1}, column {self.pos.col - len(string)}')
        return [], errors
    
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

