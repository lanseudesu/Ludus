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

id_delim       = arith_op + relat_op + whitespace + ',.:[]{}()'
numlit_delim   = arith_op + relat_op + whitespace + ',){}:]'
commslit_delim = whitespace + ',:={])'
flag_delim     = whitespace + arith_op + ',:])=!'
nl_delim       = ALPHANUM + '_{#`'

lparen_delim   = ALPHANUM + '_ .)"+-!~['
rparen_delim   = whitespace + arith_op + relat_op + '{})],.'
lcurly_delim   = whitespace + ALPHANUM + '_{(~+-!'
rcurly_delim   = whitespace 
lbracket_delim = ALPHANUM + '_ .]+-("~'
rbracket_delim = whitespace + arith_op + relat_op + ',[:).}'
comma_delim    = ALPHANUM + whitespace + '_['
period_delim   = ALPHA + '_'  
nl_delim       = whitespace + ALPHA + '_{}`'
space_delim    = whitespace + ALPHANUM + arith_op + relat_op + '_,.&|!:()[]{}"`'

delim1 = whitespace + ',:'
delim2  = ' {'
delim3  = ALPHANUM + '_ ("'
delim4  = ALPHANUM + '_ .('
delim5  = whitespace + ALPHANUM + '_}()]'
delim6  = whitespace + ALPHANUM + '_."~+-(!['
delim7 = ALPHANUM + ' _.("!~+-'
delim8 = ALPHA + '_('
delim9 = ALPHANUM + '_(.'

delim10 = delim4 + '-' #not final, wip

valid_lhs = ALPHANUM + '_)]'

### TOKENS ###

# literals:
TT_HP	      = 'hp_ltr'
TT_NHP        = 'nhp_ltr'
TT_XP         = 'xp_ltr'
TT_NXP        = 'nxp_ltr'
TT_COMMS      = 'comms_ltr'
TT_FLAG       = 'flag_ltr'

# negate:
TT_NEG        = '-'

# arithmetic operators:
TT_PLUS       = '+'
TT_MINUS      = '-'
TT_MUL        = '*'
TT_DIV        = '/'
TT_MOD        = '%'
TT_POW        = '^'

# relational operators:
TT_EE         = '=='
TT_NE         = '!='
TT_LT         = '<'
TT_GT         = '>'
TT_LTE        = '<='
TT_GTE        = '>='

# logical operators:
TT_AND        = 'AND'
TT_OR         = 'OR'
TT_NOT        = 'NOT'

# assignment operators:
TT_COLON      = ':'
TT_PLUS_EQ    = '+='
TT_MINUS_EQ   = '-='
TT_MUL_EQ     = '*='
TT_DIV_EQ     = '/='
TT_MOD_EQ     = '%='

# other symbols:
TT_LPAREN     = '('
TT_RPAREN     = ')'
TT_LSQUARE    = '['
TT_RSQUARE    = ']'
TT_LCURLY     = '{'  
TT_RCURLY     = '}'  
TT_COMMA	  = ','
TT_PERIOD	  = '.'

# others:
TT_COMMENTS1  = 'single-line comment'
TT_COMMENTS2  = 'multi-line comment'
TT_NEWLINE	  = 'newline'
TT_SPACE	  = 'space'
TT_XP_FORMATTING = 'xp formatting'

### POSITION ###

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
        self.prev_char = None
        self.advance()
    
    def advance(self):
        self.prev_char = self.current_char
        self.pos.advance(self.current_char)
        self.current_char = self.text[self.pos.idx] if self.pos.idx < len(self.text) else None
    
    def invalid_delim_error(self, lexeme):
        error_msg = f"Invalid delimiter for ' {lexeme} '. Cause: ' {self.current_char} '"
        return f"{error_msg} at line {self.pos.ln + 1}, column {self.pos.col + 1}"
    
    def process_token(self, lexeme, token, valid_delims, errors, tokens):
        if (self.current_char == '\n' and '\n' not in valid_delims) or (self.current_char is None and '\n' not in valid_delims):
            error_msg = f"Invalid delimiter for ' {lexeme} '. Cause: ' \\n '"
            error_msg = f"{error_msg} at line {self.pos.ln + 1}, column {self.pos.col + 1}."
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
            if self.current_char == '\n': 
                while self.current_char == '\n':
                    self.advance()
                self.process_token('\\n', TT_NEWLINE, nl_delim, errors, tokens)
            elif self.current_char == ' ': 
                while self.current_char == ' ':
                    self.advance()  
                self.process_token(' ', TT_SPACE, space_delim, errors, tokens)
            elif self.current_char in NUM:
                result, error = self.make_number('')

                if error:
                   errors.extend(error)
                   continue  
                
                self.process_token(result.lexeme, result.token, numlit_delim, errors, tokens)
            elif self.current_char in ALPHA:
                char_str = ''
                if self.current_char == 'A':
                    char_str += 'A'
                    self.advance()
                    if self.current_char == 'N':
                        char_str += 'N'
                        self.advance()
                        if self.current_char == 'D':
                            char_str += 'D'
                            self.advance()
                            self.tokenize_keyword(char_str, ' ', errors, tokens)
                        else:
                            self.tokenize_id(char_str, id_delim, errors, tokens)
                    else:
                        self.tokenize_id(char_str, id_delim, errors, tokens)        
                elif self.current_char == 'O':
                    char_str += 'O'
                    self.advance()
                    if self.current_char == 'R':
                        char_str += 'R'
                        self.advance()
                        self.tokenize_keyword(char_str, ' ', errors, tokens)
                    else:
                         self.tokenize_id(char_str, id_delim, errors, tokens)      
                elif self.current_char == 'a':
                    char_str += 'a'
                    self.advance()
                    if self.current_char == 'c':
                        char_str += 'c'
                        self.advance()
                        if self.current_char == 'c':
                            char_str += 'c'
                            self.advance()
                            if self.current_char == 'e':
                                char_str += 'e'
                                self.advance()
                                if self.current_char == 's':
                                    char_str += 's'
                                    self.advance()
                                    if self.current_char == 's':
                                        char_str += 's'
                                        self.advance()
                                        self.tokenize_keyword(char_str, ' ', errors, tokens)
                                    else:
                                        self.tokenize_id(char_str, id_delim, errors, tokens)
                                else:
                                    self.tokenize_id(char_str, id_delim, errors, tokens)
                            else:
                                self.tokenize_id(char_str, id_delim, errors, tokens)
                        else:
                            self.tokenize_id(char_str, id_delim, errors, tokens)
                    else:
                        self.tokenize_id(char_str, id_delim, errors, tokens)  
                elif self.current_char == 'b':
                    char_str += 'b'
                    self.advance()
                    if self.current_char == 'a':
                        char_str += 'a'
                        self.advance()
                        if self.current_char == 'c':
                            char_str += 'c'
                            self.advance()
                            if self.current_char == 'k':
                                char_str += 'k'
                                self.advance()
                                if self.current_char == 'u':
                                    char_str += 'u'
                                    self.advance()
                                    if self.current_char == 'p':
                                        char_str += 'p'
                                        self.advance()
                                        self.tokenize_keyword(char_str, ':', errors, tokens)
                                    else:
                                        self.tokenize_id(char_str, id_delim, errors, tokens)
                                else:
                                    self.tokenize_id(char_str, id_delim, errors, tokens)
                            else:
                                self.tokenize_id(char_str, id_delim, errors, tokens)
                        else:
                            self.tokenize_id(char_str, id_delim, errors, tokens)
                    elif self.current_char == 'u':
                        char_str += 'u'
                        self.advance()
                        if self.current_char == 'i':
                            char_str += 'i'
                            self.advance()
                            if self.current_char == 'l':
                                char_str += 'l'
                                self.advance()
                                if self.current_char == 'd':
                                    char_str += 'd'
                                    self.advance()
                                    self.tokenize_keyword(char_str, ' ', errors, tokens)
                                else:
                                    self.tokenize_id(char_str, id_delim, errors, tokens)
                            else:
                                self.tokenize_id(char_str, id_delim, errors, tokens)
                        else:
                            self.tokenize_id(char_str, id_delim, errors, tokens)
                    else:
                        self.tokenize_id(char_str, id_delim, errors, tokens)
                elif self.current_char == 'c':
                    char_str += 'c'
                    self.advance()
                    if self.current_char == 'h':
                        char_str += 'h'
                        self.advance()
                        if self.current_char == 'e':
                            char_str += 'e'
                            self.advance()
                            if self.current_char == 'c':
                                char_str += 'c'
                                self.advance()
                                if self.current_char == 'k':
                                    char_str += 'k'
                                    self.advance()
                                    if self.current_char == 'p':
                                        char_str += 'p'
                                        self.advance()
                                        if self.current_char == 'o':
                                            char_str += 'o'
                                            self.advance()
                                            if self.current_char == 'i':
                                                char_str += 'i'
                                                self.advance()
                                                if self.current_char == 'n':
                                                    char_str += 'n'
                                                    self.advance()
                                                    if self.current_char == 't':
                                                        char_str += 't'
                                                        self.advance()
                                                        self.tokenize_keyword(char_str, whitespace, errors, tokens)
                                                    else:
                                                        self.tokenize_id(char_str, id_delim, errors, tokens)
                                                else:
                                                    self.tokenize_id(char_str, id_delim, errors, tokens)
                                            else:
                                                self.tokenize_id(char_str, id_delim, errors, tokens)
                                        else:
                                            self.tokenize_id(char_str, id_delim, errors, tokens)
                                    else:
                                        self.tokenize_id(char_str, id_delim, errors, tokens)
                                else:
                                    self.tokenize_id(char_str, id_delim, errors, tokens)
                            else:
                                self.tokenize_id(char_str, id_delim, errors, tokens)
                        elif self.current_char == 'o':
                            char_str += 'o'
                            self.advance()
                            if self.current_char == 'i':
                                char_str += 'i'
                                self.advance()
                                if self.current_char == 'c':
                                    char_str += 'c'
                                    self.advance()
                                    if self.current_char == 'e':
                                        char_str += 'e'
                                        self.advance()
                                        self.tokenize_keyword(char_str, ' ', errors, tokens)
                                    else:
                                        self.tokenize_id(char_str, id_delim, errors, tokens)
                                else:
                                    self.tokenize_id(char_str, id_delim, errors, tokens)
                            else:
                                self.tokenize_id(char_str, id_delim, errors, tokens)
                        else:
                            self.tokenize_id(char_str, id_delim, errors, tokens)
                    elif self.current_char == 'o':
                        char_str += 'o'
                        self.advance()
                        if self.current_char == 'm':
                            char_str += 'm'
                            self.advance()
                            if self.current_char == 'm':
                                char_str += 'm'
                                self.advance()
                                if self.current_char == 's':
                                    char_str += 's'
                                    self.advance()
                                    self.tokenize_keyword(char_str, ' ', errors, tokens)
                                else:
                                    self.tokenize_id(char_str, id_delim, errors, tokens)
                            else:
                                self.tokenize_id(char_str, id_delim, errors, tokens)
                        else:
                            self.tokenize_id(char_str, id_delim, errors, tokens)
                    else:
                            self.tokenize_id(char_str, id_delim, errors, tokens)    
                elif self.current_char == 'd':
                    char_str += 'd'
                    self.advance()
                    if self.current_char == 'e':
                        char_str += 'e'
                        self.advance()
                        if self.current_char == 'a':
                            char_str += 'a'
                            self.advance()
                            if self.current_char == 'd':
                                char_str += 'd'
                                self.advance()
                                self.tokenize_keyword(char_str, delim1, errors, tokens)
                            else:
                                self.tokenize_id(char_str, id_delim, errors, tokens)
                        else:
                            self.tokenize_id(char_str, id_delim, errors, tokens)
                    elif self.current_char == 'r':
                        char_str += 'r'
                        self.advance()
                        if self.current_char == 'o':
                            char_str += 'o'
                            self.advance()
                            if self.current_char == 'p':
                                char_str += 'p'
                                self.advance()
                                self.tokenize_keyword(char_str, '(', errors, tokens)
                            else:
                                self.tokenize_id(char_str, id_delim, errors, tokens)
                        else:
                            self.tokenize_id(char_str, id_delim, errors, tokens)
                    else:
                        self.tokenize_id(char_str, id_delim, errors, tokens)
                elif self.current_char == 'e':
                    char_str += 'e'
                    self.advance()
                    if self.current_char == 'l':
                        char_str += 'l'
                        self.advance()
                        if self.current_char == 'i':
                            char_str += 'i'
                            self.advance()
                            if self.current_char == 'f':
                                char_str += 'f'
                                self.advance()
                                self.tokenize_keyword(char_str, ' ', errors, tokens)
                            else:
                                self.tokenize_id(char_str, id_delim, errors, tokens)
                        elif self.current_char == 's':
                            char_str += 's'
                            self.advance()
                            if self.current_char == 'e':
                                char_str += 'e'
                                self.advance()
                                self.tokenize_keyword(char_str, delim2, errors, tokens)
                            else:
                                self.tokenize_id(char_str, id_delim, errors, tokens)
                        else:
                            self.tokenize_id(char_str, id_delim, errors, tokens)
                    else:
                        self.tokenize_id(char_str, id_delim, errors, tokens)
                elif self.current_char == 'f':
                    char_str += 'f'
                    self.advance()
                    if self.current_char == 'a':
                        char_str += 'a'
                        self.advance()
                        if self.current_char == 'l':
                            char_str += 'l'
                            self.advance()
                            if self.current_char == 's':
                                char_str += 's'
                                self.advance()
                                if self.current_char == 'e':
                                    char_str += 'e' 
                                    self.advance()
                                    if self.current_char in ALPHANUM or self.current_char == '_':
                                        self.tokenize_id(char_str, id_delim, errors, tokens)
                                    else:
                                        self.process_token(TT_FLAG, TT_FLAG, flag_delim, errors, tokens)
                                else: 
                                    self.tokenize_id(char_str, id_delim, errors, tokens)
                            else: 
                                self.tokenize_id(char_str, id_delim, errors, tokens)
                        else:
                            self.tokenize_id(char_str, id_delim, errors, tokens)
                    elif self.current_char == 'l':
                        char_str += 'l'
                        self.advance()
                        if self.current_char == 'a':
                            char_str += 'a'
                            self.advance()
                            if self.current_char == 'g':
                                char_str += 'g'
                                self.advance()
                                self.tokenize_keyword(char_str, ' ', errors, tokens)
                            elif self.current_char == 'n':
                                char_str += 'n'
                                self.advance()
                                if self.current_char == 'k':
                                    char_str += 'k'
                                    self.advance()
                                    self.tokenize_keyword(char_str, ' ', errors, tokens)
                                else:
                                    self.tokenize_id(char_str, id_delim, errors, tokens)
                            else:
                                self.tokenize_id(char_str, id_delim, errors, tokens)
                        else:
                            self.tokenize_id(char_str, id_delim, errors, tokens)
                    elif self.current_char == 'o':
                        char_str += 'o'
                        self.advance()
                        if self.current_char == 'r':
                            char_str += 'r'
                            self.advance()
                            self.tokenize_keyword(char_str, ' ', errors, tokens)
                        else:
                            self.tokenize_id(char_str, id_delim, errors, tokens)
                    else:
                        self.tokenize_id(char_str, id_delim, errors, tokens)  
                elif self.current_char == 'g':
                    char_str += 'g'
                    self.advance()
                    if self.current_char == 'a':
                        char_str += 'a'
                        self.advance()
                        if self.current_char == 'm':
                            char_str += 'm'
                            self.advance()
                            if self.current_char == 'e':
                                char_str += 'e'
                                self.advance()
                                if self.current_char == 'O':
                                    char_str += 'O'
                                    self.advance()
                                    if self.current_char == 'v':
                                        char_str += 'v'
                                        self.advance()
                                        if self.current_char == 'e':
                                            char_str += 'e'
                                            self.advance()
                                            if self.current_char == 'r':
                                                char_str += 'r'
                                                self.advance()
                                                self.tokenize_keyword(char_str, whitespace, errors, tokens)
                                            else:
                                                self.tokenize_id(char_str, id_delim, errors, tokens)
                                        else:
                                            self.tokenize_id(char_str, id_delim, errors, tokens)
                                    else:
                                        self.tokenize_id(char_str, id_delim, errors, tokens)
                                else:
                                    self.tokenize_id(char_str, id_delim, errors, tokens)
                            else:
                                self.tokenize_id(char_str, id_delim, errors, tokens)
                        else:
                            self.tokenize_id(char_str, id_delim, errors, tokens)
                    elif self.current_char == 'e':
                        char_str += 'e'
                        self.advance()
                        if self.current_char == 'n':
                            char_str += 'n'
                            self.advance()
                            if self.current_char == 'e':
                                char_str += 'e'
                                self.advance()
                                if self.current_char == 'r':
                                    char_str += 'r'
                                    self.advance()
                                    if self.current_char == 'a':
                                        char_str += 'a'
                                        self.advance()
                                        if self.current_char == 't':
                                            char_str += 't'
                                            self.advance()
                                            if self.current_char == 'e':
                                                char_str += 'e'
                                                self.advance()
                                                self.tokenize_keyword(char_str, ' ', errors, tokens)
                                            else:
                                                self.tokenize_id(char_str, id_delim, errors, tokens)
                                        else:
                                            self.tokenize_id(char_str, id_delim, errors, tokens)
                                    else:
                                        self.tokenize_id(char_str, id_delim, errors, tokens)
                                else:
                                    self.tokenize_id(char_str, id_delim, errors, tokens)
                            else:
                                self.tokenize_id(char_str, id_delim, errors, tokens)
                        else:
                            self.tokenize_id(char_str, id_delim, errors, tokens)
                    elif self.current_char == 'r':
                        char_str += 'r'
                        self.advance()
                        if self.current_char == 'i':
                            char_str += 'i'
                            self.advance()
                            if self.current_char == 'n':
                                char_str += 'n'
                                self.advance()
                                if self.current_char == 'd':
                                    char_str += 'd'
                                    self.advance()
                                    self.tokenize_keyword(char_str, delim2, errors, tokens)
                                else:
                                    self.tokenize_id(char_str, id_delim, errors, tokens)
                            else:
                                self.tokenize_id(char_str, id_delim, errors, tokens)
                        else:
                            self.tokenize_id(char_str, id_delim, errors, tokens)
                    else:
                            self.tokenize_id(char_str, id_delim, errors, tokens)
                elif self.current_char == 'h':
                    char_str += 'h' 
                    self.advance()
                    if self.current_char == 'p':
                        char_str += 'p'
                        self.advance()
                        self.tokenize_keyword(char_str, ' ', errors, tokens)
                    else:
                        self.tokenize_id(char_str, id_delim, errors, tokens)
                elif self.current_char == 'i':
                    char_str += 'i' 
                    self.advance()
                    if self.current_char == 'f':
                        char_str += 'f'
                        self.advance()
                        self.tokenize_keyword(char_str, ' ', errors, tokens)
                    elif self.current_char == 'm':
                        char_str += 'm'
                        self.advance()
                        if self.current_char == 'm':
                            char_str += 'm'
                            self.advance()
                            if self.current_char == 'o':
                                char_str += 'o'
                                self.advance()
                                self.tokenize_keyword(char_str, ' ', errors, tokens)
                            else:
                                self.tokenize_id(char_str, id_delim, errors, tokens)
                        else:
                            self.tokenize_id(char_str, id_delim, errors, tokens)
                    else:
                        self.tokenize_id(char_str, id_delim, errors, tokens)
                elif self.current_char == 'j':
                    char_str += 'j' 
                    self.advance()
                    if self.current_char == 'o':
                        char_str += 'o' 
                        self.advance()
                        if self.current_char == 'i':
                            char_str += 'i' 
                            self.advance()
                            if self.current_char == 'n':
                                char_str += 'n' 
                                self.advance()
                                self.tokenize_keyword(char_str, '(', errors, tokens)
                            else:
                                self.tokenize_id(char_str, id_delim, errors, tokens)
                        else:
                            self.tokenize_id(char_str, id_delim, errors, tokens)
                    else:
                        self.tokenize_id(char_str, id_delim, errors, tokens)
                elif self.current_char == 'l':
                    char_str += 'l' 
                    self.advance()
                    if self.current_char == 'e':
                        char_str += 'e' 
                        self.advance()
                        if self.current_char == 'v':
                            char_str += 'v' 
                            self.advance()
                            if self.current_char == 'e':
                                char_str += 'e' 
                                self.advance()
                                if self.current_char == 'l':
                                    char_str += 'l' 
                                    self.advance()
                                    if self.current_char == 'D':
                                        char_str += 'D' 
                                        self.advance()
                                        if self.current_char == 'o':
                                            char_str += 'o' 
                                            self.advance()
                                            if self.current_char == 'w':
                                                char_str += 'w' 
                                                self.advance()
                                                if self.current_char == 'n':
                                                    char_str += 'n' 
                                                    self.advance()
                                                    self.tokenize_keyword(char_str, '(', errors, tokens)
                                                else:
                                                    self.tokenize_id(char_str, id_delim, errors, tokens)
                                            else:
                                                self.tokenize_id(char_str, id_delim, errors, tokens)
                                        else:
                                            self.tokenize_id(char_str, id_delim, errors, tokens)
                                    elif self.current_char == 'U':
                                        char_str += 'U' 
                                        self.advance()
                                        if self.current_char == 'p':
                                            char_str += 'p' 
                                            self.advance()
                                            self.tokenize_keyword(char_str, '(', errors, tokens)
                                        else:
                                            self.tokenize_id(char_str, id_delim, errors, tokens)
                                    else:
                                        self.tokenize_id(char_str, id_delim, errors, tokens)
                                else:
                                    self.tokenize_id(char_str, id_delim, errors, tokens)
                            else:
                                self.tokenize_id(char_str, id_delim, errors, tokens)
                        else:
                            self.tokenize_id(char_str, id_delim, errors, tokens)
                    elif self.current_char == 'o':
                        char_str += 'o'
                        self.advance()
                        if self.current_char == 'a':
                            char_str += 'a' 
                            self.advance()
                            if self.current_char == 'd':
                                char_str += 'd' 
                                self.advance()
                                if self.current_char == 'N':
                                    char_str += 'N'
                                    self.advance()
                                    if self.current_char == 'u':
                                        char_str += 'u'
                                        self.advance()
                                        if self.current_char == 'm':
                                            char_str += 'm'
                                            self.advance()
                                            self.tokenize_keyword(char_str, '(', errors, tokens)
                                        else:
                                            self.tokenize_id(char_str, id_delim, errors, tokens)
                                    else:
                                        self.tokenize_id(char_str, id_delim, errors, tokens)
                                elif self.current_char in ALPHANUM or self.current_char == '_':
                                    self.tokenize_id(char_str, id_delim, errors, tokens)
                                else:
                                    self.tokenize_keyword(char_str, '(', errors, tokens) 
                            else:
                                self.tokenize_id(char_str, id_delim, errors, tokens)    
                        else:
                            self.tokenize_id(char_str, id_delim, errors, tokens)   
                    else:
                        self.tokenize_id(char_str, id_delim, errors, tokens) 
      
                elif self.current_char == 'p':
                    char_str += 'p'
                    self.advance() 
                    if self.current_char == 'l':
                        char_str += 'l'
                        self.advance()
                        if self.current_char == 'a':
                            char_str += 'a'
                            self.advance()
                            if self.current_char == 'y':
                                char_str += 'y'
                                self.advance()
                                self.tokenize_keyword(char_str, '(', errors, tokens)
                            else:
                                self.tokenize_id(char_str, id_delim, errors, tokens)
                        else:
                            self.tokenize_id(char_str, id_delim, errors, tokens)
                    else:
                        self.tokenize_id(char_str, id_delim, errors, tokens)
                elif self.current_char == 'r':
                    char_str += 'r' 
                    self.advance()
                    if self.current_char == 'e':
                        char_str += 'e' 
                        self.advance()
                        if self.current_char == 'c':
                            char_str += 'c' 
                            self.advance()
                            if self.current_char == 'a':
                                char_str += 'a' 
                                self.advance()
                                if self.current_char == 'l':
                                    char_str += 'l' 
                                    self.advance()
                                    if self.current_char == 'l':
                                        char_str += 'l' 
                                        self.advance()
                                        self.tokenize_keyword(char_str, ' ', errors, tokens)
                                    else:
                                        self.tokenize_id(char_str, id_delim, errors, tokens)
                                else:
                                    self.tokenize_id(char_str, id_delim, errors, tokens)
                            else:
                                self.tokenize_id(char_str, id_delim, errors, tokens)
                        elif self.current_char == 's': 
                            char_str += 's' 
                            self.advance()  
                            if self.current_char == 'u': 
                                char_str += 'u' 
                                self.advance()
                                if self.current_char == 'm': 
                                    char_str += 'm' 
                                    self.advance()
                                    if self.current_char == 'e': 
                                        char_str += 'e' 
                                        self.advance()
                                        self.tokenize_keyword(char_str, whitespace, errors, tokens)
                                    else:
                                        self.tokenize_id(char_str, id_delim, errors, tokens)
                                else:
                                    self.tokenize_id(char_str, id_delim, errors, tokens)
                            else:
                                self.tokenize_id(char_str, id_delim, errors, tokens) 
                        else:
                            self.tokenize_id(char_str, id_delim, errors, tokens)  
                    elif self.current_char == 'o':
                        char_str += 'o' 
                        self.advance()
                        if self.current_char == 'u': 
                            char_str += 'u' 
                            self.advance()
                            if self.current_char == 'n': 
                                char_str += 'n' 
                                self.advance()
                                if self.current_char == 'd': 
                                    char_str += 'd' 
                                    self.advance()
                                    if self.current_char == 's': 
                                        char_str += 's' 
                                        self.advance()
                                        self.tokenize_keyword(char_str, '(', errors, tokens)
                                    else:
                                        self.tokenize_id(char_str, id_delim, errors, tokens)
                                else:
                                    self.tokenize_id(char_str, id_delim, errors, tokens)
                            else:
                                self.tokenize_id(char_str, id_delim, errors, tokens)
                        else:
                            self.tokenize_id(char_str, id_delim, errors, tokens)
                    else:
                        self.tokenize_id(char_str, id_delim, errors, tokens)
                elif self.current_char == 's':
                    char_str += 's'
                    self.advance()
                    if self.current_char == 'e': 
                        char_str += 'e' 
                        self.advance()
                        if self.current_char == 'e': 
                            char_str += 'e' 
                            self.advance()
                            if self.current_char == 'k': 
                                char_str += 'k' 
                                self.advance()
                                self.tokenize_keyword(char_str, '(', errors, tokens)
                            else:
                                self.tokenize_id(char_str, id_delim, errors, tokens)
                        else:
                            self.tokenize_id(char_str, id_delim, errors, tokens)
                    elif self.current_char == 'h':
                        char_str += 'h'
                        self.advance()
                        if self.current_char == 'o': 
                            char_str += 'o' 
                            self.advance()
                            if self.current_char == 'o': 
                                char_str += 'o' 
                                self.advance()
                                if self.current_char == 't': 
                                    char_str += 't' 
                                    self.advance()
                                    if self.current_char == 'N': 
                                        char_str += 'N' 
                                        self.advance()
                                        if self.current_char == 'x': 
                                            char_str += 'x' 
                                            self.advance()
                                            if self.current_char == 't': 
                                                char_str += 't' 
                                                self.advance()
                                                self.tokenize_keyword(char_str, '(', errors, tokens)
                                            else:
                                                self.tokenize_id(char_str, id_delim, errors, tokens)
                                        else:
                                            self.tokenize_id(char_str, id_delim, errors, tokens)
                                    elif self.current_char in ALPHANUM or self.current_char == '_':
                                        self.tokenize_id(char_str, id_delim, errors, tokens)
                                    else:
                                        self.tokenize_keyword(char_str, '(', errors, tokens)
                                else:
                                    self.tokenize_id(char_str, id_delim, errors, tokens)
                            else:
                                self.tokenize_id(char_str, id_delim, errors, tokens)
                        else:
                            self.tokenize_id(char_str, id_delim, errors, tokens)
                    else:
                            self.tokenize_id(char_str, id_delim, errors, tokens)
                elif self.current_char == 't':
                    char_str += 't' 
                    self.advance()
                    if self.current_char == 'o': 
                        char_str += 'o' 
                        self.advance()
                        if self.current_char == 'H': 
                            char_str += 'H' 
                            self.advance()
                            if self.current_char == 'p': 
                                char_str += 'p' 
                                self.advance()
                                self.tokenize_keyword(char_str, '(', errors, tokens)
                            else: 
                                self.tokenize_id(char_str, id_delim, errors, tokens)
                        elif self.current_char == 'X':
                            char_str += 'X' 
                            self.advance()
                            if self.current_char == 'p':
                                char_str += 'p' 
                                self.advance()
                                self.tokenize_keyword(char_str, '(', errors, tokens)
                            else: 
                                self.tokenize_id(char_str, id_delim, errors, tokens)
                        elif self.current_char == 'C':
                            char_str += 'C' 
                            self.advance()
                            if self.current_char == 'o':
                                char_str += 'o' 
                                self.advance()
                                if self.current_char == 'm':
                                    char_str += 'm' 
                                    self.advance()
                                    if self.current_char == 'm':
                                        char_str += 'm' 
                                        self.advance()
                                        if self.current_char == 's':
                                            char_str += 's' 
                                            self.advance()
                                            self.tokenize_keyword(char_str, '(', errors, tokens)
                                        else: 
                                            self.tokenize_id(char_str, id_delim, errors, tokens)
                                    else: 
                                        self.tokenize_id(char_str, id_delim, errors, tokens)
                                else: 
                                    self.tokenize_id(char_str, id_delim, errors, tokens)
                            else: 
                                self.tokenize_id(char_str, id_delim, errors, tokens)
                        else: 
                            self.tokenize_id(char_str, id_delim, errors, tokens)
                    elif self.current_char == 'r':
                        char_str += 'r' 
                        self.advance()
                        if self.current_char == 'u':
                            char_str += 'u' 
                            self.advance()
                            if self.current_char == 'e':
                                char_str += 'e' 
                                self.advance()
                                if self.current_char in ALPHANUM or self.current_char == '_':
                                    self.tokenize_id(char_str, id_delim, errors, tokens)
                                else:
                                    self.process_token(TT_FLAG, TT_FLAG, flag_delim, errors, tokens)
                            else: 
                                self.tokenize_id(char_str, id_delim, errors, tokens)
                        else: 
                            self.tokenize_id(char_str, id_delim, errors, tokens)
                    else: 
                        self.tokenize_id(char_str, id_delim, errors, tokens)
                elif self.current_char == 'w':
                    char_str += 'w' 
                    self.advance()
                    if self.current_char == 'h':
                        char_str += 'h' 
                        self.advance()
                        if self.current_char == 'i':
                            char_str += 'i' 
                            self.advance()
                            if self.current_char == 'l':
                                char_str += 'l' 
                                self.advance()
                                if self.current_char == 'e':
                                    char_str += 'e' 
                                    self.advance()
                                    self.tokenize_keyword(char_str, ' ', errors, tokens)
                                else: 
                                    self.tokenize_id(char_str, id_delim, errors, tokens)
                            else: 
                                self.tokenize_id(char_str, id_delim, errors, tokens)
                        else: 
                            self.tokenize_id(char_str, id_delim, errors, tokens)
                    elif self.current_char == 'i':
                        char_str += 'i'  
                        self.advance()
                        if self.current_char == 'p':
                            char_str += 'p' 
                            self.advance()
                            if self.current_char == 'e':
                                char_str += 'e' 
                                self.advance()
                                self.tokenize_keyword(char_str, '(', errors, tokens)
                            else: 
                                self.tokenize_id(char_str, id_delim, errors, tokens)
                        else: 
                            self.tokenize_id(char_str, id_delim, errors, tokens)
                    else: 
                            self.tokenize_id(char_str, id_delim, errors, tokens)
                elif self.current_char == 'x':
                    char_str += 'x' 
                    self.advance()
                    if self.current_char == 'p':
                        char_str += 'p' 
                        self.advance()
                        self.tokenize_keyword(char_str, ' ', errors, tokens)
                    else:
                        self.tokenize_id(char_str, id_delim, errors, tokens)
                else:
                    self.tokenize_id(char_str, id_delim, errors, tokens)    
            elif self.current_char == '_':
                char_str = ''
                self.tokenize_id(char_str, id_delim, errors, tokens)
            elif self.current_char == '"':
                result, error = self.make_string()

                if error:
                   errors.extend(error)
                   continue

                self.process_token(result.lexeme, result.token, commslit_delim, errors, tokens)
            elif self.current_char == '+':
                self.advance()
                if self.current_char == '=':
                    self.process_token('+=', TT_PLUS_EQ, delim4, errors, tokens)
                else:
                    self.process_token('+', TT_PLUS, delim3, errors, tokens)
            elif self.current_char == '-':
                lhs = self.prev_char
                self.advance()
                if self.current_char == '=':
                    self.process_token('-=', TT_MINUS_EQ, delim4, errors, tokens)
                else:
                    #check lhs if id, number, )
                    if lhs in valid_lhs:
                        self.process_token('-', TT_MINUS, delim10, errors, tokens)
                    else:
                        if self.current_char in NUM or self.current_char == '.':
                            result, error = self.make_number('-')

                            if error:
                                errors.extend(error)
                                continue  

                            self.process_token(result.lexeme, result.token, numlit_delim, errors, tokens)
                        else:
                            self.process_token('-', TT_NEG, delim4, errors, tokens)
                
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
                        self.process_token(char, token_type, delim4, errors, tokens)
                        break
                    elif self.current_char == '=':  
                        self.advance()
                        self.process_token(char + next_char, token_type, delim4, errors, tokens)
                        break
            elif self.current_char in '^:()[]{},':
                token_map = {
                    '^': [(TT_POW, delim4)],
                    ':': [(TT_COLON, delim6)],
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
                        self.process_token(result, TT_XP_FORMATTING, ')', errors, tokens)
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
                    '=': [(TT_EE, delim7)],
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
                        errors.append(f"Invalid character error at line {self.pos.ln+1}, column {self.pos.col}. Cause: ' {char} '")
            elif self.current_char == '!':
                char = self.current_char
                self.advance()
                if self.current_char == '=':
                    self.advance()
                    self.process_token('!=', TT_NE, delim7, errors, tokens)
                else:
                    self.process_token('!', TT_NOT, delim8, errors, tokens)   
            elif self.current_char == '#':
                comments = '#'
                self.advance()
                while self.current_char is not None:
                    if self.current_char == '\n':
                        self.process_token(comments, TT_COMMENTS1, '\n', errors, tokens)
                        break
                    comments += self.current_char
                    self.advance()
                    
                if self.current_char is None:
                    self.process_token(comments, TT_COMMENTS1, '\n', errors, tokens)

            elif self.current_char == '`':
                backtick_count = 0
                while self.current_char == '`' and backtick_count < 3:
                    backtick_count += 1
                    self.advance()

                if backtick_count != 3:  
                    errors.append(f"Incomplete comment delimiter at line {self.pos.ln + 1}, column {self.pos.col - backtick_count}")
                    return

                comment = ""
                while True:
                    if self.current_char is None: 
                        errors.append(f"Unclosed multi-line comment starting at line {self.pos.ln + 1}")
                        break

                    if self.current_char == '`':  
                        close_count = 0
                        while self.current_char == '`' and close_count < 3:
                            close_count += 1
                            self.advance()

                        if close_count == 3:  
                            self.process_token(comment.strip(), TT_COMMENTS2, whitespace, errors, tokens)
                            break
                        else:  
                            comment += '`' * close_count
                    else:
                        comment += self.current_char
                        self.advance()
            else:
                errors.append(f"Unknown character ' {self.current_char} ' at line {self.pos.ln + 1}, column {self.pos.col + 1}")
                self.advance()
        
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
            if num_str == '-':
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
            # if num_str == '~0':
            #     add_error(f"Invalid number '{num_str}'. Zero can't be negative")
            #     return [], errors
            token_type = TT_NXP if dot_count > 0 else TT_NHP

        return Token(num_str, token_type), errors

    def make_identifier(self, id_str): # todo
        id_len = len(id_str)
        errors = []

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
                add_error(f"Maximum number characters reached in '{id_str}'")
                return [], errors
            
        return Token(id_str, self.identifiers(id_str)), errors

    def identifiers(self, id_str):
        if id_str not in self.identifier_map:
            self.identifier_map[id_str] = f'id{self.current_id}'
            self.current_id += 1

        return self.identifier_map[id_str]

    def tokenize_id(self, char_str, id_delim, errors, tokens):
        result, error = self.make_identifier(char_str)

        if error:
            errors.extend(error)
        else:
            self.process_token(result.lexeme, result.token, id_delim, errors, tokens)

    def tokenize_keyword(self, char_str, valid_delim, errors,tokens):
        if self.current_char is None: 
            self.process_token(char_str, char_str, valid_delim, errors, tokens)
        elif self.current_char in ALPHANUM or self.current_char == '_':
            self.tokenize_id(char_str, id_delim, errors, tokens)
        else:
            self.process_token(char_str, char_str, valid_delim, errors, tokens)

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
                if self.current_char in 'nt{}"\\':
                    resolved_char = escape_characters.get(self.current_char, self.current_char)
                    string += resolved_char 
                    escape_character = False    
                else:
                    string += '\\' + self.current_char    
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

### RUN ###

def run(fn, text):
    lexer = Lexer(fn, text)
    tokens, error = lexer.make_tokens()

    return tokens, error

