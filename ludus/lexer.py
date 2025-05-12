import string

### CONSTANTS ###

DIGITS          = '123456789'
NUM             = '0' + DIGITS
ALPHA           = string.ascii_letters
ALPHANUM        = ALPHA + NUM
ASCII_PRINTABLE = ''.join(chr(i) for i in range(32, 127))
NUM_TO_6        = '0123456' 

arith_op   = '+-*/%^'
relat_op   = '<>=!'
whitespace = '# \n\t'

### DELIMITERS ###

id_delim       = whitespace + arith_op + relat_op + ',.:[]{}()'
numlit_delim   = arith_op + relat_op + whitespace + ',){}:]'
commslit_delim = whitespace + ',:={])+!'
flag_delim     = whitespace + relat_op + arith_op + ',:]){'

lparen_delim   = ALPHANUM + '_ .()"-!['
lbracket_delim = ALPHANUM + '_ .]-("'
lcurly_delim   = ALPHANUM + whitespace + '_{(-!'
comma_delim    = ALPHANUM + whitespace + '_.["-(!'
period_delim   = ALPHA + '_'  
rparen_delim   = whitespace + arith_op + relat_op + '{})],.'
rcurly_delim   = whitespace + '}' 
rbracket_delim = whitespace + arith_op + relat_op + ',.[:){}'

nl_delim       = ALPHA + whitespace + '_{}`\t'
space_delim    = ALPHANUM + whitespace + arith_op + relat_op + '_,.&|!:()[]{}"`\t'

delim1  = whitespace + ',:'
delim2  = ' {'
delim3  = ALPHANUM + '_ ."-!('
delim4  = ALPHANUM + '_ .-!('
delim5  = ALPHANUM + whitespace + '_."-(!['
delim6  = ALPHA + '_('
delim7  = '})' + whitespace + arith_op + relat_op 

valid_lhs = ALPHANUM + '_)]'

### TOKENS ###

# literals:
TT_HP	      = 'hp_ltr'
TT_XP         = 'xp_ltr'
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
TT_NOT        = '!'

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
TT_XP_FORMATTING = 'xp_formatting'

TT_EOF = 'EOF'

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

        if current_char == '\t':
            self.col += 4 - (self.col % 4)
        else:
            self.col += 1
        
        if current_char == '\n':
            self.ln += 1
            self.col = 0

        return self
    
    def retreat(self, current_char):
        self.idx -= 1
        self.col -= 1

        if current_char == '\n':
            self.ln -= 1
            self.col = 0

        return self

    def copy(self):
        return Position(self.idx, self.ln, self.col, self.fn, self.ftxt)


class Token:
    def __init__(self, lexeme, token, line, column, state_nums=[]):
        self.lexeme = lexeme # 'as'
        self.token = token   # 'id'
        self.line = line    
        self.column = column
        self.state_nums = state_nums # [0, 207, 209, 210]
    
    def __repr__(self):
        return f'{self.lexeme}:{self.token}'

### lexer ###
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

    def retreat(self):
        self.pos.retreat(self.current_char)
        self.current_char = self.text[self.pos.idx] if self.pos.idx < len(self.text) else None
    
    def invalid_delim_error(self, valid_delims, error_msg): 
        valid_delims = ",".join(valid_delims) 
        if valid_delims[0] == 'a' and valid_delims[104] == '0':
            valid_delims = list(valid_delims)
            valid_delims[0:123] = ['ALPHANUM']
            valid_delims = ''.join(valid_delims)
        elif valid_delims[0] == 'a':
            valid_delims = list(valid_delims)
            valid_delims[0:103] = ['ALPHA'] 
            valid_delims = ''.join(valid_delims)
        valid_delims = valid_delims.replace("\n", "\\n") 
        valid_delims = valid_delims.replace("\t", "\\t")  
        valid_delims = valid_delims.replace(' ', 'space')
        return f"{error_msg} at line {self.pos.ln + 1}, column {self.pos.col + 1}.\nExpected delimiters are: {valid_delims}"
    
    def process_token(self, cur_ln, cur_col, lexeme, token, valid_delims, errors, tokens, state_num):
        if (self.current_char == '\n' and '\n' not in valid_delims) or (self.current_char is None and '\n' not in valid_delims):
            error_msg = f"Lexical Error: Invalid delimiter for ' {lexeme} '. Cause: ' \\n '"
            errors.append(self.invalid_delim_error(valid_delims, error_msg))
            
            self.advance()
        elif self.current_char is not None and self.current_char not in valid_delims:
            error_msg = f"Lexical Error: Invalid delimiter for ' {lexeme} '. Cause: ' {self.current_char} '"
            errors.append(self.invalid_delim_error(valid_delims, error_msg))
            self.advance()
        else:
            if token == TT_COMMENTS2 or token == TT_COMMENTS1:
                pass
            else:
                if token == TT_COMMS:
                    newline_count = lexeme.count('\n') 
                    if newline_count > 0:
                        token += '\n' * newline_count
                        tokens.append(Token(lexeme, token, cur_ln, cur_col, state_num)) 
                    else:
                       tokens.append(Token(lexeme, token, cur_ln, cur_col, state_num))  
                elif token == 'true' or token == 'false':
                    tokens.append(Token(lexeme, TT_FLAG, cur_ln, cur_col, state_num))
                else:
                    tokens.append(Token(lexeme, token, cur_ln, cur_col, state_num)) 

                #tokens.append(Token(lexeme, token, pos_start=self.pos))  -- use if not using webbased gui

    def make_tokens(self):
        tokens = [] # list of tokens
        errors = [] # list of errors
        lhs_space = '' # this records the character before a space
        # 'lhs_space' is used in checking the lhs of a '-' character to determine if its a negative token or part of a negative numeric
    
        while self.current_char is not None:
            cur_ln = self.pos.ln + 1   
            cur_col = self.pos.col + 1 

            # tab, lexer ignores this
            if self.current_char == '\t':
                self.advance()
            
            # letters, this tries to tokenize keywords or identifiers
            elif self.current_char in ALPHA: 
                char_str = ''   # variable to store the string of the lexeme
                state_num = [0] # list to store the state numbers
 
                # if-else ladder to tokenize keywords
                if self.current_char == 'A':
                    char_str += 'A' # if a letter in a keyword is found, char_str is concatenated with that letter
                    cur_state = 1   # cur_state is changed into whatever the state number of that character in the TD

                    state_num.append(cur_state) # append the cur_state to the state_num list
                    self.advance()

                    if self.current_char == 'N':
                        char_str += 'N'
                        cur_state += 1 # increment cur_state to follow TD

                        state_num.append(cur_state)
                        self.advance()

                        if self.current_char == 'D':
                            char_str += 'D'
                            cur_state += 1
                            state_num.append(cur_state)
                            self.advance()
                            self.tokenize_keyword(cur_ln, cur_col, char_str, ' ', errors, tokens, state_num) # function to try to tokenize the lexeme as the keyword
                        else:
                            self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens) # function to try to tokenize the lexeme as an id
                    
                    # if the next char or letter diverts from the keyword, it is tokenized as an identifier
                    else:
                        self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)        
                elif self.current_char == 'O':
                    char_str += 'O'
                    cur_state = 5
                    state_num.append(cur_state)
                    self.advance()
                    if self.current_char == 'R':
                        char_str += 'R'
                        cur_state += 1
                        state_num.append(cur_state)
                        self.advance()
                        self.tokenize_keyword(cur_ln, cur_col, char_str, ' ', errors, tokens, state_num)
                    else:
                         self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)      
                elif self.current_char == 'a':
                    char_str += 'a'
                    cur_state = 8
                    state_num.append(cur_state)
                    self.advance()
                    if self.current_char == 'c':
                        char_str += 'c'
                        cur_state += 1
                        state_num.append(cur_state)
                        self.advance()
                        if self.current_char == 'c':
                            char_str += 'c'
                            cur_state += 1
                            state_num.append(cur_state)
                            self.advance()
                            if self.current_char == 'e':
                                char_str += 'e'
                                cur_state += 1
                                state_num.append(cur_state)
                                self.advance()
                                if self.current_char == 's':
                                    char_str += 's'
                                    cur_state += 1
                                    state_num.append(cur_state)
                                    self.advance()
                                    if self.current_char == 's':
                                        char_str += 's'
                                        cur_state += 1
                                        state_num.append(cur_state)
                                        self.advance()
                                        self.tokenize_keyword(cur_ln, cur_col, char_str, ' ', errors, tokens, state_num)
                                    else:
                                        self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                                else:
                                    self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                            else:
                                self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                        else:
                            self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                    else:
                        self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)  
                elif self.current_char == 'b':
                    char_str += 'b'
                    cur_state = 15
                    state_num.append(cur_state)
                    self.advance()
                    if self.current_char == 'a':
                        char_str += 'a'
                        cur_state += 1
                        state_num.append(cur_state)
                        self.advance()
                        if self.current_char == 'c':
                            char_str += 'c'
                            cur_state += 1
                            state_num.append(cur_state)
                            self.advance()
                            if self.current_char == 'k':
                                char_str += 'k'
                                cur_state += 1
                                state_num.append(cur_state)
                                self.advance()
                                if self.current_char == 'u':
                                    char_str += 'u'
                                    cur_state += 1
                                    state_num.append(cur_state)
                                    self.advance()
                                    if self.current_char == 'p':
                                        char_str += 'p'
                                        cur_state += 1
                                        state_num.append(cur_state)
                                        self.advance()
                                        self.tokenize_keyword(cur_ln, cur_col, char_str, ':', errors, tokens, state_num)
                                    else:
                                        self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                                else:
                                    self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                            else:
                                self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                        else:
                            self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                    elif self.current_char == 'u':
                        char_str += 'u'
                        cur_state = 22
                        state_num.append(cur_state)
                        self.advance()
                        if self.current_char == 'i':
                            char_str += 'i'
                            cur_state += 1
                            state_num.append(cur_state)
                            self.advance()
                            if self.current_char == 'l':
                                char_str += 'l'
                                cur_state += 1
                                state_num.append(cur_state)
                                self.advance()
                                if self.current_char == 'd':
                                    char_str += 'd'
                                    cur_state += 1
                                    state_num.append(cur_state)
                                    self.advance()
                                    self.tokenize_keyword(cur_ln, cur_col, char_str, ' ', errors, tokens, state_num)
                                else:
                                    self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                            else:
                                self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                        else:
                            self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                    else:
                        self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                elif self.current_char == 'c':
                    char_str += 'c'
                    cur_state = 27
                    state_num.append(cur_state)
                    self.advance()
                    if self.current_char == 'h':
                        char_str += 'h'
                        cur_state += 1
                        state_num.append(cur_state)
                        self.advance()
                        if self.current_char == 'e':
                            char_str += 'e'
                            cur_state += 1
                            state_num.append(cur_state)
                            self.advance()
                            if self.current_char == 'c':
                                char_str += 'c'
                                cur_state += 1
                                state_num.append(cur_state)
                                self.advance()
                                if self.current_char == 'k':
                                    char_str += 'k'
                                    cur_state += 1
                                    state_num.append(cur_state)
                                    self.advance()
                                    if self.current_char == 'p':
                                        char_str += 'p'
                                        cur_state += 1
                                        state_num.append(cur_state)
                                        self.advance()
                                        if self.current_char == 'o':
                                            char_str += 'o'
                                            cur_state += 1
                                            state_num.append(cur_state)
                                            self.advance()
                                            if self.current_char == 'i':
                                                char_str += 'i'
                                                cur_state += 1
                                                state_num.append(cur_state)
                                                self.advance()
                                                if self.current_char == 'n':
                                                    char_str += 'n'
                                                    cur_state += 1
                                                    state_num.append(cur_state)
                                                    self.advance()
                                                    if self.current_char == 't':
                                                        char_str += 't'
                                                        cur_state += 1
                                                        state_num.append(cur_state)
                                                        self.advance()
                                                        self.tokenize_keyword(cur_ln, cur_col, char_str, whitespace, errors, tokens, state_num)
                                                    else:
                                                        self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                                                else:
                                                    self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                                            else:
                                                self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                                        else:
                                            self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                                    else:
                                        self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                                else:
                                    self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                            else:
                                self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                        elif self.current_char == 'o':
                            char_str += 'o'
                            cur_state = 38
                            state_num.append(cur_state)
                            self.advance()
                            if self.current_char == 'i':
                                char_str += 'i'
                                cur_state += 1
                                state_num.append(cur_state)
                                self.advance()
                                if self.current_char == 'c':
                                    char_str += 'c'
                                    cur_state += 1
                                    state_num.append(cur_state)
                                    self.advance()
                                    if self.current_char == 'e':
                                        char_str += 'e'
                                        cur_state += 1
                                        state_num.append(cur_state)
                                        self.advance()
                                        self.tokenize_keyword(cur_ln, cur_col, char_str, ' ', errors, tokens, state_num)
                                    else:
                                        self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                                else:
                                    self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                            else:
                                self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                        else:
                            self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                    elif self.current_char == 'o':
                        char_str += 'o'
                        cur_state = 43
                        state_num.append(cur_state)
                        self.advance()
                        if self.current_char == 'm':
                            char_str += 'm'
                            cur_state += 1
                            state_num.append(cur_state)
                            self.advance()
                            if self.current_char == 'm':
                                char_str += 'm'
                                cur_state += 1
                                state_num.append(cur_state)
                                self.advance()
                                if self.current_char == 's':
                                    char_str += 's'
                                    cur_state += 1
                                    state_num.append(cur_state)
                                    self.advance()
                                    self.tokenize_keyword(cur_ln, cur_col, char_str, ' ', errors, tokens, state_num)
                                else:
                                    self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                            else:
                                self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                        else:
                            self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                    else:
                        self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)    
                elif self.current_char == 'd':
                    char_str += 'd'
                    cur_state = 48
                    state_num.append(cur_state)
                    self.advance()
                    if self.current_char == 'e':
                        char_str += 'e'
                        cur_state += 1
                        state_num.append(cur_state)
                        self.advance()
                        if self.current_char == 'a':
                            char_str += 'a'
                            cur_state += 1
                            state_num.append(cur_state)
                            self.advance()
                            if self.current_char == 'd':
                                char_str += 'd'
                                cur_state += 1
                                state_num.append(cur_state)
                                self.advance()
                                self.tokenize_keyword(cur_ln, cur_col, char_str, delim1, errors, tokens, state_num)
                            else:
                                self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                        else:
                            self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                    elif self.current_char == 'r':
                        char_str += 'r'
                        cur_state = 53
                        state_num.append(cur_state)
                        self.advance()
                        if self.current_char == 'o':
                            char_str += 'o'
                            cur_state += 1
                            state_num.append(cur_state)
                            self.advance()
                            if self.current_char == 'p':
                                char_str += 'p'
                                cur_state += 1
                                state_num.append(cur_state)
                                self.advance()
                                self.tokenize_keyword(cur_ln, cur_col, char_str, '(', errors, tokens, state_num)
                            else:
                                self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                        else:
                            self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                    else:
                        self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                elif self.current_char == 'e':
                    char_str += 'e'
                    cur_state = 57
                    state_num.append(cur_state)
                    self.advance()
                    if self.current_char == 'l':
                        char_str += 'l'
                        cur_state += 1
                        state_num.append(cur_state)
                        self.advance()
                        if self.current_char == 'i':
                            char_str += 'i'
                            cur_state += 1
                            state_num.append(cur_state)
                            self.advance()
                            if self.current_char == 'f':
                                char_str += 'f'
                                cur_state += 1
                                state_num.append(cur_state)
                                self.advance()
                                self.tokenize_keyword(cur_ln, cur_col, char_str, ' ', errors, tokens, state_num)
                            else:
                                self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                        elif self.current_char == 's':
                            char_str += 's'
                            cur_state = 62
                            state_num.append(cur_state)
                            self.advance()
                            if self.current_char == 'e':
                                char_str += 'e'
                                cur_state += 1
                                state_num.append(cur_state)
                                self.advance()
                                self.tokenize_keyword(cur_ln, cur_col, char_str, delim2, errors, tokens, state_num)
                            else:
                                self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                        else:
                            self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                    else:
                        self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                elif self.current_char == 'f':
                    char_str += 'f'
                    cur_state = 65
                    state_num.append(cur_state)
                    self.advance()
                    if self.current_char == 'a':
                        char_str += 'a'
                        cur_state += 1
                        state_num.append(cur_state)
                        self.advance()
                        if self.current_char == 'l':
                            char_str += 'l'
                            cur_state += 1
                            state_num.append(cur_state)
                            self.advance()
                            if self.current_char == 's':
                                char_str += 's'
                                cur_state += 1
                                state_num.append(cur_state)
                                self.advance()
                                if self.current_char == 'e':
                                    char_str += 'e' 
                                    cur_state += 1
                                    state_num.append(cur_state)
                                    self.advance()
                                    self.tokenize_keyword(cur_ln, cur_col, char_str, flag_delim, errors, tokens, state_num)
                                else: 
                                    self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                            else: 
                                self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                        else:
                            self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                    elif self.current_char == 'l':
                        char_str += 'l'
                        cur_state = 71
                        state_num.append(cur_state)
                        self.advance()
                        if self.current_char == 'a':
                            char_str += 'a'
                            cur_state += 1
                            state_num.append(cur_state)
                            self.advance()
                            if self.current_char == 'g':
                                char_str += 'g'
                                cur_state += 1
                                state_num.append(cur_state)
                                self.advance()
                                self.tokenize_keyword(cur_ln, cur_col, char_str, ' ', errors, tokens, state_num)
                            elif self.current_char == 'n':
                                char_str += 'n'
                                cur_state = 75
                                state_num.append(cur_state)
                                self.advance()
                                if self.current_char == 'k':
                                    char_str += 'k'
                                    cur_state += 1
                                    state_num.append(cur_state)
                                    self.advance()
                                    self.tokenize_keyword(cur_ln, cur_col, char_str, ' ', errors, tokens, state_num)
                                else:
                                    self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                            else:
                                self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                        else:
                            self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                    elif self.current_char == 'o':
                        char_str += 'o'
                        cur_state = 78
                        state_num.append(cur_state)
                        self.advance()
                        if self.current_char == 'r':
                            char_str += 'r'
                            cur_state += 1
                            state_num.append(cur_state)
                            self.advance()
                            self.tokenize_keyword(cur_ln, cur_col, char_str, ' ', errors, tokens, state_num)
                        else:
                            self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                    else:
                        self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)  
                elif self.current_char == 'g':
                    char_str += 'g'
                    cur_state = 81
                    state_num.append(cur_state)
                    self.advance()
                    if self.current_char == 'a':
                        char_str += 'a'
                        cur_state += 1
                        state_num.append(cur_state)
                        self.advance()
                        if self.current_char == 'm':
                            char_str += 'm'
                            cur_state += 1
                            state_num.append(cur_state)
                            self.advance()
                            if self.current_char == 'e':
                                char_str += 'e'
                                cur_state += 1
                                state_num.append(cur_state)
                                self.advance()
                                if self.current_char == 'O':
                                    char_str += 'O'
                                    cur_state += 1
                                    state_num.append(cur_state)
                                    self.advance()
                                    if self.current_char == 'v':
                                        char_str += 'v'
                                        cur_state += 1
                                        state_num.append(cur_state)
                                        self.advance()
                                        if self.current_char == 'e':
                                            char_str += 'e'
                                            cur_state += 1
                                            state_num.append(cur_state)
                                            self.advance()
                                            if self.current_char == 'r':
                                                char_str += 'r'
                                                cur_state += 1
                                                state_num.append(cur_state)
                                                self.advance()
                                                self.tokenize_keyword(cur_ln, cur_col, char_str, whitespace, errors, tokens, state_num)
                                            else:
                                                self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                                        else:
                                            self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                                    else:
                                        self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                                else:
                                    self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                            else:
                                self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                        else:
                            self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                    elif self.current_char == 'e':
                        char_str += 'e'
                        cur_state = 90
                        state_num.append(cur_state)
                        self.advance()
                        if self.current_char == 'n':
                            char_str += 'n'
                            cur_state += 1
                            state_num.append(cur_state)
                            self.advance()
                            if self.current_char == 'e':
                                char_str += 'e'
                                cur_state += 1
                                state_num.append(cur_state)
                                self.advance()
                                if self.current_char == 'r':
                                    char_str += 'r'
                                    cur_state += 1
                                    state_num.append(cur_state)
                                    self.advance()
                                    if self.current_char == 'a':
                                        char_str += 'a'
                                        cur_state += 1
                                        state_num.append(cur_state)
                                        self.advance()
                                        if self.current_char == 't':
                                            char_str += 't'
                                            cur_state += 1
                                            state_num.append(cur_state)
                                            self.advance()
                                            if self.current_char == 'e':
                                                char_str += 'e'
                                                cur_state += 1
                                                state_num.append(cur_state)
                                                self.advance()
                                                self.tokenize_keyword(cur_ln, cur_col, char_str, ' ', errors, tokens, state_num)
                                            else:
                                                self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                                        else:
                                            self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                                    else:
                                        self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                                else:
                                    self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                            else:
                                self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                        else:
                            self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                    elif self.current_char == 'r':
                        char_str += 'r'
                        cur_state = 98
                        state_num.append(cur_state)
                        self.advance()
                        if self.current_char == 'i':
                            char_str += 'i'
                            cur_state += 1
                            state_num.append(cur_state)
                            self.advance()
                            if self.current_char == 'n':
                                char_str += 'n'
                                cur_state += 1
                                state_num.append(cur_state)
                                self.advance()
                                if self.current_char == 'd':
                                    char_str += 'd'
                                    cur_state += 1
                                    state_num.append(cur_state)
                                    self.advance()
                                    self.tokenize_keyword(cur_ln, cur_col, char_str, delim2, errors, tokens, state_num)
                                else:
                                    self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                            else:
                                self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                        else:
                            self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                    else:
                            self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                elif self.current_char == 'h':
                    char_str += 'h' 
                    cur_state = 103
                    state_num.append(cur_state)
                    self.advance()
                    if self.current_char == 'p':
                        char_str += 'p'
                        cur_state += 1
                        state_num.append(cur_state)
                        self.advance()
                        self.tokenize_keyword(cur_ln, cur_col, char_str, ' ', errors, tokens, state_num)
                    else:
                        self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                elif self.current_char == 'i':
                    char_str += 'i' 
                    cur_state = 106
                    state_num.append(cur_state)
                    self.advance()
                    if self.current_char == 'f':
                        char_str += 'f'
                        cur_state += 1
                        state_num.append(cur_state)
                        self.advance()
                        self.tokenize_keyword(cur_ln, cur_col, char_str, ' ', errors, tokens, state_num)
                    elif self.current_char == 'm':
                        char_str += 'm'
                        cur_state = 109
                        state_num.append(cur_state)
                        self.advance()
                        if self.current_char == 'm':
                            char_str += 'm'
                            cur_state += 1
                            state_num.append(cur_state)
                            self.advance()
                            if self.current_char == 'o':
                                char_str += 'o'
                                cur_state += 1
                                state_num.append(cur_state)
                                self.advance()
                                self.tokenize_keyword(cur_ln, cur_col, char_str, ' ', errors, tokens, state_num)
                            else:
                                self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                        else:
                            self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                    else:
                        self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                elif self.current_char == 'j':
                    char_str += 'j' 
                    cur_state = 113
                    state_num.append(cur_state)
                    self.advance()
                    if self.current_char == 'o':
                        char_str += 'o' 
                        cur_state += 1
                        state_num.append(cur_state)
                        self.advance()
                        if self.current_char == 'i':
                            char_str += 'i' 
                            cur_state += 1
                            state_num.append(cur_state)
                            self.advance()
                            if self.current_char == 'n':
                                char_str += 'n' 
                                cur_state += 1
                                state_num.append(cur_state)
                                self.advance()
                                self.tokenize_keyword(cur_ln, cur_col, char_str, '(', errors, tokens, state_num)
                            else:
                                self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                        else:
                            self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                    else:
                        self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                elif self.current_char == 'l':
                    char_str += 'l' 
                    cur_state = 118
                    state_num.append(cur_state)
                    self.advance()
                    if self.current_char == 'e':
                        char_str += 'e' 
                        cur_state += 1
                        state_num.append(cur_state)
                        self.advance()
                        if self.current_char == 'v':
                            char_str += 'v' 
                            cur_state += 1
                            state_num.append(cur_state)
                            self.advance()
                            if self.current_char == 'e':
                                char_str += 'e' 
                                cur_state += 1
                                state_num.append(cur_state)
                                self.advance()
                                if self.current_char == 'l':
                                    char_str += 'l' 
                                    cur_state += 1
                                    state_num.append(cur_state)
                                    self.advance()
                                    if self.current_char == 'D':
                                        char_str += 'D' 
                                        cur_state += 1
                                        state_num.append(cur_state)
                                        self.advance()
                                        if self.current_char == 'o':
                                            char_str += 'o' 
                                            cur_state += 1
                                            state_num.append(cur_state)
                                            self.advance()
                                            if self.current_char == 'w':
                                                char_str += 'w' 
                                                cur_state += 1
                                                state_num.append(cur_state)
                                                self.advance()
                                                if self.current_char == 'n':
                                                    char_str += 'n' 
                                                    cur_state += 1
                                                    state_num.append(cur_state)
                                                    self.advance()
                                                    self.tokenize_keyword(cur_ln, cur_col, char_str, '(', errors, tokens, state_num)
                                                else:
                                                    self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                                            else:
                                                self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                                        else:
                                            self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                                    elif self.current_char == 'U':
                                        char_str += 'U' 
                                        cur_state = 128
                                        state_num.append(cur_state)
                                        self.advance()
                                        if self.current_char == 'p':
                                            char_str += 'p' 
                                            cur_state += 1
                                            state_num.append(cur_state)
                                            self.advance()
                                            self.tokenize_keyword(cur_ln, cur_col, char_str, '(', errors, tokens, state_num)
                                        else:
                                            self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                                    else:
                                        self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                                else:
                                    self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                            else:
                                self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                        else:
                            self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                    elif self.current_char == 'o':
                        char_str += 'o'
                        cur_state = 131
                        state_num.append(cur_state)
                        self.advance()
                        if self.current_char == 'a':
                            char_str += 'a' 
                            cur_state += 1
                            state_num.append(cur_state)
                            self.advance()
                            if self.current_char == 'd':
                                char_str += 'd' 
                                cur_state += 1
                                state_num.append(cur_state)
                                self.advance()
                                if self.current_char == 'N':
                                    char_str += 'N'
                                    cur_state += 1
                                    state_num.append(cur_state)
                                    self.advance()
                                    if self.current_char == 'u':
                                        char_str += 'u'
                                        cur_state += 1
                                        state_num.append(cur_state)
                                        self.advance()
                                        if self.current_char == 'm':
                                            char_str += 'm'
                                            cur_state += 1
                                            state_num.append(cur_state)
                                            self.advance()
                                            self.tokenize_keyword(cur_ln, cur_col, char_str, '(', errors, tokens, state_num)
                                        else:
                                            self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                                    else:
                                        self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                                elif self.current_char is None:
                                    self.tokenize_keyword(cur_ln, cur_col, char_str, '(', errors, tokens, state_num)
                                elif self.current_char in ALPHANUM or self.current_char == '_':
                                    self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                                else:
                                    self.tokenize_keyword(cur_ln, cur_col, char_str, '(', errors, tokens, state_num) 
                            else:
                                self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)    
                        else:
                            self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)   
                    else:
                        self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens) 
      
                elif self.current_char == 'p':
                    char_str += 'p'
                    cur_state = 139
                    state_num.append(cur_state)
                    self.advance() 
                    if self.current_char == 'l':
                        char_str += 'l'
                        cur_state += 1
                        state_num.append(cur_state)
                        self.advance()
                        if self.current_char == 'a':
                            char_str += 'a'
                            cur_state += 1
                            state_num.append(cur_state)
                            self.advance()
                            if self.current_char == 'y':
                                char_str += 'y'
                                cur_state += 1
                                state_num.append(cur_state)
                                self.advance()
                                self.tokenize_keyword(cur_ln, cur_col, char_str, '(', errors, tokens, state_num)
                            else:
                                self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                        else:
                            self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                    else:
                        self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                elif self.current_char == 'r':
                    char_str += 'r' 
                    cur_state = 144
                    state_num.append(cur_state)
                    self.advance()
                    if self.current_char == 'e':
                        char_str += 'e' 
                        cur_state += 1
                        state_num.append(cur_state)
                        self.advance()
                        if self.current_char == 'c':
                            char_str += 'c' 
                            cur_state += 1
                            state_num.append(cur_state)
                            self.advance()
                            if self.current_char == 'a':
                                char_str += 'a' 
                                cur_state += 1
                                state_num.append(cur_state)
                                self.advance()
                                if self.current_char == 'l':
                                    char_str += 'l' 
                                    cur_state += 1
                                    state_num.append(cur_state)
                                    self.advance()
                                    if self.current_char == 'l':
                                        char_str += 'l' 
                                        cur_state += 1
                                        state_num.append(cur_state)
                                        self.advance()
                                        self.tokenize_keyword(cur_ln, cur_col, char_str, ' ', errors, tokens, state_num)
                                    else:
                                        self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                                else:
                                    self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                            else:
                                self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                        elif self.current_char == 's': 
                            char_str += 's' 
                            cur_state = 151
                            state_num.append(cur_state)
                            self.advance()  
                            if self.current_char == 'u': 
                                char_str += 'u' 
                                cur_state += 1
                                state_num.append(cur_state)
                                self.advance()
                                if self.current_char == 'm': 
                                    char_str += 'm' 
                                    cur_state += 1
                                    state_num.append(cur_state)
                                    self.advance()
                                    if self.current_char == 'e': 
                                        char_str += 'e' 
                                        cur_state += 1
                                        state_num.append(cur_state)
                                        self.advance()
                                        self.tokenize_keyword(cur_ln, cur_col, char_str, whitespace, errors, tokens, state_num)
                                    else:
                                        self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                                else:
                                    self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                            else:
                                self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens) 
                        else:
                            self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)  
                    elif self.current_char == 'o':
                        char_str += 'o' 
                        cur_state = 156
                        state_num.append(cur_state)
                        self.advance()
                        if self.current_char == 'u': 
                            char_str += 'u' 
                            cur_state += 1
                            state_num.append(cur_state)
                            self.advance()
                            if self.current_char == 'n': 
                                char_str += 'n' 
                                cur_state += 1
                                state_num.append(cur_state)
                                self.advance()
                                if self.current_char == 'd': 
                                    char_str += 'd' 
                                    cur_state += 1
                                    state_num.append(cur_state)
                                    self.advance()
                                    if self.current_char == 's': 
                                        char_str += 's' 
                                        cur_state += 1
                                        state_num.append(cur_state)
                                        self.advance()
                                        self.tokenize_keyword(cur_ln, cur_col, char_str, '(', errors, tokens, state_num)
                                    else:
                                        self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                                else:
                                    self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                            else:
                                self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                        else:
                            self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                    else:
                        self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                elif self.current_char == 's':
                    char_str += 's'
                    cur_state = 162
                    state_num.append(cur_state)
                    self.advance()
                    if self.current_char == 'e': 
                        char_str += 'e' 
                        cur_state += 1
                        state_num.append(cur_state)
                        self.advance()
                        if self.current_char == 'e': 
                            char_str += 'e' 
                            cur_state += 1
                            state_num.append(cur_state)
                            self.advance()
                            if self.current_char == 'k': 
                                char_str += 'k' 
                                cur_state += 1
                                state_num.append(cur_state)
                                self.advance()
                                self.tokenize_keyword(cur_ln, cur_col, char_str, '(', errors, tokens, state_num)
                            else:
                                self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                        else:
                            self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                    elif self.current_char == 'h':
                        char_str += 'h'
                        cur_state = 167
                        state_num.append(cur_state)
                        self.advance()
                        if self.current_char == 'o': 
                            char_str += 'o' 
                            cur_state += 1
                            state_num.append(cur_state)
                            self.advance()
                            if self.current_char == 'o': 
                                char_str += 'o' 
                                cur_state += 1
                                state_num.append(cur_state)
                                self.advance()
                                if self.current_char == 't': 
                                    char_str += 't' 
                                    cur_state += 1
                                    state_num.append(cur_state)
                                    self.advance()
                                    if self.current_char == 'N': 
                                        char_str += 'N' 
                                        cur_state += 2
                                        state_num.append(cur_state)
                                        self.advance()
                                        if self.current_char == 'x': 
                                            char_str += 'x' 
                                            cur_state += 1
                                            state_num.append(cur_state)
                                            self.advance()
                                            if self.current_char == 't': 
                                                char_str += 't' 
                                                cur_state += 1
                                                state_num.append(cur_state)
                                                self.advance()
                                                self.tokenize_keyword(cur_ln, cur_col, char_str, '(', errors, tokens, state_num)
                                            else:
                                                self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                                        else:
                                            self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                                    elif self.current_char is None:
                                        self.tokenize_keyword(cur_ln, cur_col, char_str, '(', errors, tokens, state_num)
                                    elif self.current_char in ALPHANUM or self.current_char == '_':
                                        self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                                    else:
                                        self.tokenize_keyword(cur_ln, cur_col, char_str, '(', errors, tokens, state_num)
                                else:
                                    self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                            else:
                                self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                        else:
                            self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                    else:
                            self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                elif self.current_char == 't':
                    char_str += 't' 
                    cur_state = 176
                    state_num.append(cur_state)
                    self.advance()
                    if self.current_char == 'o': 
                        char_str += 'o' 
                        cur_state += 1
                        state_num.append(cur_state)
                        self.advance()
                        if self.current_char == 'H': 
                            char_str += 'H' 
                            cur_state += 1
                            state_num.append(cur_state)
                            self.advance()
                            if self.current_char == 'p': 
                                char_str += 'p' 
                                cur_state += 1
                                state_num.append(cur_state)
                                self.advance()
                                self.tokenize_keyword(cur_ln, cur_col, char_str, '(', errors, tokens, state_num)
                            else: 
                                self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                        elif self.current_char == 'X':
                            char_str += 'X' 
                            cur_state = 181
                            state_num.append(cur_state)
                            self.advance()
                            if self.current_char == 'p':
                                char_str += 'p' 
                                cur_state += 1
                                state_num.append(cur_state)
                                self.advance()
                                self.tokenize_keyword(cur_ln, cur_col, char_str, '(', errors, tokens, state_num)
                            else: 
                                self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                        elif self.current_char == 'C':
                            char_str += 'C' 
                            cur_state = 184
                            state_num.append(cur_state)
                            self.advance()
                            if self.current_char == 'o':
                                char_str += 'o' 
                                cur_state += 1
                                state_num.append(cur_state)
                                self.advance()
                                if self.current_char == 'm':
                                    char_str += 'm' 
                                    cur_state += 1
                                    state_num.append(cur_state)
                                    self.advance()
                                    if self.current_char == 'm':
                                        char_str += 'm' 
                                        cur_state += 1
                                        state_num.append(cur_state)
                                        self.advance()
                                        if self.current_char == 's':
                                            char_str += 's' 
                                            cur_state += 1
                                            state_num.append(cur_state)
                                            self.advance()
                                            self.tokenize_keyword(cur_ln, cur_col, char_str, '(', errors, tokens, state_num)
                                        else: 
                                            self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                                    else: 
                                        self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                                else: 
                                    self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                            else: 
                                self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                        else: 
                            self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                    elif self.current_char == 'r':
                        char_str += 'r' 
                        cur_state = 190
                        state_num.append(cur_state)
                        self.advance()
                        if self.current_char == 'u':
                            char_str += 'u' 
                            cur_state += 1
                            state_num.append(cur_state)
                            self.advance()
                            if self.current_char == 'e':
                                char_str += 'e' 
                                cur_state += 1
                                state_num.append(cur_state)
                                self.advance()
                                self.tokenize_keyword(cur_ln, cur_col, char_str, flag_delim, errors, tokens, state_num)
                            else: 
                                self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                        else: 
                            self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                    else: 
                        self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                elif self.current_char == 'v':
                    char_str += 'v' 
                    cur_state = 190
                    state_num.append(cur_state)
                    self.advance()
                    if self.current_char == 'o':
                        char_str += 'o' 
                        cur_state += 1
                        state_num.append(cur_state)
                        self.advance()
                        if self.current_char == 'i':
                            char_str += 'i' 
                            cur_state += 1
                            state_num.append(cur_state)
                            self.advance()
                            if self.current_char == 'd':
                                char_str += 'd' 
                                cur_state += 1
                                state_num.append(cur_state)
                                self.advance()
                                self.tokenize_keyword(cur_ln, cur_col, char_str, whitespace, errors, tokens, state_num)
                            else: 
                                self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                        else: 
                            self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                    else: 
                        self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                elif self.current_char == 'w':
                    char_str += 'w' 
                    cur_state = 194
                    state_num.append(cur_state)
                    self.advance()
                    if self.current_char == 'h':
                        char_str += 'h' 
                        cur_state += 1
                        state_num.append(cur_state)
                        self.advance()
                        if self.current_char == 'i':
                            char_str += 'i' 
                            cur_state += 1
                            state_num.append(cur_state)
                            self.advance()
                            if self.current_char == 'l':
                                char_str += 'l' 
                                cur_state += 1
                                state_num.append(cur_state)
                                self.advance()
                                if self.current_char == 'e':
                                    char_str += 'e' 
                                    cur_state += 1
                                    state_num.append(cur_state)
                                    self.advance()
                                    self.tokenize_keyword(cur_ln, cur_col, char_str, ' ', errors, tokens, state_num)
                                else: 
                                    self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                            else: 
                                self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                        else: 
                            self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                    elif self.current_char == 'i':
                        char_str += 'i'  
                        cur_state = 200
                        state_num.append(cur_state)
                        self.advance()
                        if self.current_char == 'p':
                            char_str += 'p' 
                            cur_state += 1
                            state_num.append(cur_state)
                            self.advance()
                            if self.current_char == 'e':
                                char_str += 'e' 
                                cur_state += 1
                                state_num.append(cur_state)
                                self.advance()
                                self.tokenize_keyword(cur_ln, cur_col, char_str, '(', errors, tokens, state_num)
                            else: 
                                self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                        else: 
                            self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                    else: 
                            self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                elif self.current_char == 'x':
                    char_str += 'x' 
                    cur_state = 204
                    state_num.append(cur_state)
                    self.advance()
                    if self.current_char == 'p':
                        char_str += 'p' 
                        cur_state += 1
                        state_num.append(cur_state)
                        self.advance()
                        self.tokenize_keyword(cur_ln, cur_col, char_str, ' ', errors, tokens, state_num)
                    else:
                        self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
                else:
                    char_str = self.current_char
                    self.advance()
                    self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)    

            # upon encountering an underscore, tries to tokenize it as id  
            elif self.current_char == '_':
                char_str = '_'
                self.advance()
                self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens) 
            
            elif self.current_char == '+':
                state_num = [0, 267] # states for + is 0 -> 267
                self.advance()
                
                # if '=' is encountered next to a '+', it is a  '+=' operator
                if self.current_char == '=':
                    state_num.append(269) # states for += is 0 -> 267 -> 269
                    state_num.append(270) # then 270 if delim is correct
                    self.advance()
                    self.process_token(cur_ln, cur_col, '+=', TT_PLUS_EQ, delim3, errors, tokens, state_num)
                # else it is a '+'
                else:
                    state_num.append(268)
                    self.process_token(cur_ln, cur_col, '+', TT_PLUS, delim3, errors, tokens, state_num)
            
            elif self.current_char == '-':
                state_num = [0, 271]
                lhs = self.prev_char 
                # we must check the left-hand side of the '-' to determine whether it is a negative sign or a subtraction operator
                
                self.advance()

                # if '=' is encountered next to a '-', it's a  '-=' operator
                if self.current_char == '=':
                    state_num.append(273)
                    state_num.append(274)
                    self.advance()
                    self.process_token(cur_ln, cur_col, '-=', TT_MINUS_EQ, delim4, errors, tokens, state_num)
                
                else:
                    # check lhs is id, number, ) or ] -> meaning it is a minus sign
                    if lhs is not None and lhs in valid_lhs:
                        state_num.append(272)
                        self.process_token(cur_ln, cur_col, '-', TT_MINUS, delim4, errors, tokens, state_num)
                   
                    # if lhs is a space, check the value of variable 'lhs_space' which stores the char before the space
                    elif lhs == ' ':
                        # check lhs is id, number, ) or ] ->  meaning it is a minus sign
                        if lhs_space is not None and lhs_space in valid_lhs:
                            state_num.append(272)
                            self.process_token(cur_ln, cur_col, '-', TT_MINUS, delim4, errors, tokens, state_num)
                        
                        else: # else, it either must be a negative sign or part of a negative numeric literal
                            
                            # checks if next char (rhs) is None, meaning it is a negative sign
                            if self.current_char is None:
                                state_num.append(272)
                                self.process_token(cur_ln, cur_col, '-', TT_NEG, delim4, errors, tokens, state_num)
                            
                            # checks if next char (rhs) is a number or a period, meaning it is a negative numeric literal
                            elif self.current_char in NUM or self.current_char == '.':
                                result, error = self.make_number('-', state_num) 
                                # calls make_number function with '-' as the first char of the number (the negative sign)

                                if error:
                                    errors.extend(error)
                                    continue  

                                self.process_token(cur_ln, cur_col, result.lexeme, result.token, numlit_delim, errors, tokens, result.state_nums)

                            # else, just process it as a negative token
                            else:
                                state_num.append(272)
                                self.process_token(cur_ln, cur_col, '-', TT_NEG, delim4, errors, tokens, state_num)

                    # same thing with lhs_space, but checks lhs instead of lhs_space
                    else:
                        if self.current_char is None:
                            state_num.append(272)
                            self.process_token(cur_ln, cur_col, '-', TT_NEG, delim4, errors, tokens, state_num)
                        elif self.current_char in NUM or self.current_char == '.':
                            result, error = self.make_number('-', state_num)

                            if error:
                                errors.extend(error)
                                continue  

                            self.process_token(cur_ln, cur_col, result.lexeme, result.token, numlit_delim, errors, tokens, result.state_nums)
                        else:
                            state_num.append(272)
                            self.process_token(cur_ln, cur_col, '-', TT_NEG, delim4, errors, tokens, state_num)

            elif self.current_char == '*':
                state_num = [0, 275]
                self.advance()
                
                # if '=' is encountered next to a '*', it is a  '*=' operator
                if self.current_char == '=':
                    state_num.append(277)
                    state_num.append(278)
                    self.advance()
                    self.process_token(cur_ln, cur_col, '*=', TT_MUL_EQ, delim4, errors, tokens, state_num)
                # else it is a '*'
                else:
                    state_num.append(276)
                    self.process_token(cur_ln, cur_col, '*', TT_MUL, delim4, errors, tokens, state_num)

            elif self.current_char == '/':
                state_num = [0, 279]
                self.advance()
                
                # if '=' is encountered next to a '/', it is a  '/=' operator
                if self.current_char == '=':
                    state_num.append(281)
                    state_num.append(282)
                    self.advance()
                    self.process_token(cur_ln, cur_col, '/=', TT_DIV_EQ, delim4, errors, tokens, state_num)
                # else it is a '/'
                else:
                    state_num.append(280)
                    self.process_token(cur_ln, cur_col, '/', TT_DIV, delim4, errors, tokens, state_num)

            elif self.current_char == '%':
                state_num = [0, 283]
                self.advance()
                
                # if '=' is encountered next to a '%', it is a  '%=' operator
                if self.current_char == '=':
                    state_num.append(285)
                    state_num.append(286)
                    self.advance()
                    self.process_token(cur_ln, cur_col, '%=', TT_MOD_EQ, delim4, errors, tokens, state_num)
                # else it is a '%'
                else:
                    state_num.append(284)
                    self.process_token(cur_ln, cur_col, '%', TT_MOD, delim4, errors, tokens, state_num)

            elif self.current_char == '^':
                state_num = [0, 287, 288]
                self.advance()
                self.process_token(cur_ln, cur_col, '^', TT_POW, delim4, errors, tokens, state_num)

            elif self.current_char == ':':
                state_num = [0, 289, 290]
                self.advance()
                self.process_token(cur_ln, cur_col, ':', TT_COLON, delim5, errors, tokens, state_num)

            elif self.current_char == '=':
                state_num = [0, 291]
                self.advance()

                # checks for '==' operator
                if self.current_char == '=':    
                    state_num.extend([292,293])
                    self.advance()
                    self.process_token(cur_ln, cur_col, '==', TT_EE, delim3, errors, tokens, state_num)
                # throws an error if character is only '='
                else:
                    errors.append(f"Lexical Error: Invalid character error at line {self.pos.ln+1}, column {self.pos.col}. Cause: ' {'=' + self.current_char} '")

            elif self.current_char == '<':
                state_num = [0, 294]
                self.advance()
                
                # if '=' is encountered next to a '<', it is a  '<=' operator
                if self.current_char == '=':
                    state_num.append(296)
                    state_num.append(297)
                    self.advance()
                    self.process_token(cur_ln, cur_col, '<=', TT_LTE, delim4, errors, tokens, state_num)
                # else it is a '<'
                else:
                    state_num.append(295)
                    self.process_token(cur_ln, cur_col, '<', TT_LT, delim4, errors, tokens, state_num)

            elif self.current_char == '>':
                state_num = [0, 298]
                self.advance()
                
                # if '=' is encountered next to a '>', it is a  '>=' operator
                if self.current_char == '=':
                    state_num.append(300)
                    state_num.append(301)
                    self.advance()
                    self.process_token(cur_ln, cur_col, '>=', TT_GTE, delim4, errors, tokens, state_num)
                # else it is a '>'
                else:
                    state_num.append(299)
                    self.process_token(cur_ln, cur_col, '>', TT_GT, delim4, errors, tokens, state_num)

            elif self.current_char == '!':
                state_num = [0, 302]
                self.advance()

                if self.current_char == '=':
                    state_num.extend([304,305])
                    self.advance()
                    # token is '!=' if '=' is encountered next to '!'
                    self.process_token(cur_ln, cur_col, '!=', TT_NE, delim3, errors, tokens, state_num)   
                else:
                    state_num.append(303)
                    # else, token is '!'
                    self.process_token(cur_ln, cur_col, '!', TT_NOT, delim6, errors, tokens, state_num)
            
            elif self.current_char == '&':
                state_num = [0, 306]
                self.advance()

                # checks for '&&' operator
                if self.current_char == '&':
                    state_num.extend([307,308])
                    self.advance()
                    self.process_token(cur_ln, cur_col, '&&', '&&', ' ', errors, tokens, state_num)
                # throws an error if character is only '&'
                else:
                    errors.append(f"Lexical Error: Invalid character error at line {self.pos.ln+1}, column {self.pos.col}. Cause: ' {'&' + self.current_char} '")
            
            elif self.current_char == '|':
                state_num = [0, 309]
                self.advance()

                # checks for '||' operator
                if self.current_char == '|':
                    state_num.extend([310,311])
                    self.advance()
                    self.process_token(cur_ln, cur_col, '||', '||', ' ', errors, tokens, state_num)
                # throws an error if character is only '|'
                else:
                    errors.append(f"Lexical Error: Invalid character error at line {self.pos.ln+1}, column {self.pos.col}. Cause: ' {'|' + self.current_char} '")

            elif self.current_char == '(':
                state_num = [0, 312, 313]
                self.advance()
                self.process_token(cur_ln, cur_col, '(', TT_LPAREN, lparen_delim, errors, tokens, state_num)

            elif self.current_char == '[':
                state_num = [0, 314, 315]
                self.advance()
                self.process_token(cur_ln, cur_col, '[', TT_LSQUARE, lbracket_delim, errors, tokens, state_num)

            elif self.current_char == '{':
                state_num = [0, 316, 317]
                self.advance()
                self.process_token(cur_ln, cur_col, '{', TT_LCURLY, lcurly_delim, errors, tokens, state_num)

            elif self.current_char == ',':
                state_num = [0, 318, 319]
                self.advance()
                self.process_token(cur_ln, cur_col, ',', TT_COMMA, comma_delim, errors, tokens, state_num)
                
            elif self.current_char == '.':
                state_num = [0, 320]
                self.advance()
    
                # this is for xp_formatting token (if 0-6 digit is found next to '.')
                if self.current_char is not None and self.current_char in NUM_TO_6:
                    result = self.current_char
                    self.advance()

                    # if 'f' is found next to a 0-6 digit, tokenize it as xp_formatting
                    if self.current_char is not None and self.current_char == 'f': 
                        state_num.extend([322, 323, 324])
                        result = '.' + result + 'f'
                        self.advance()
                        self.process_token(cur_ln, cur_col, result, TT_XP_FORMATTING, delim7, errors, tokens, state_num)

                    # else, tokenize it as a xp number
                    else:
                        result, error = self.make_number('.' + result, state_num) # call make_number with '.' as the num_str

                        if error:
                            errors.extend(error)
                            continue  

                        self.process_token(cur_ln, cur_col, result.lexeme, result.token, numlit_delim, errors, tokens, result.state_nums) 
                
                # if 7-9 is found next to '.', try to tokenize it as a number first
                elif self.current_char is not None and self.current_char in NUM:
                    result, error = self.make_number('.', state_num) # call make_number with '.' as the num_str

                    if error:
                        errors.extend(error)
                        continue  

                    self.process_token(cur_ln, cur_col, result.lexeme, result.token, numlit_delim, errors, tokens, result.state_nums)    
                
                # else, tokenize it as a period
                else:
                    state_num.append(321)
                    self.process_token(cur_ln, cur_col, '.', TT_PERIOD, period_delim, errors, tokens, state_num)  

            elif self.current_char == ')':
                state_num = [0, 325, 326]
                self.advance()
                self.process_token(cur_ln, cur_col, ')', TT_RPAREN, rparen_delim, errors, tokens, state_num)

            elif self.current_char == ']':
                state_num = [0, 327, 328]
                self.advance()
                self.process_token(cur_ln, cur_col, ']', TT_RSQUARE, rbracket_delim, errors, tokens, state_num)

            elif self.current_char == '}':
                state_num = [0, 329, 330]
                self.advance()
                self.process_token(cur_ln, cur_col, '}', TT_RCURLY, rcurly_delim, errors, tokens, state_num)

            # numbers (hp and xp)    
            elif self.current_char in NUM:
                state_num = [0, 331]
                result, error = self.make_number('', state_num) # calls the make_number function to tokenize the numeric literal

                # result is the resulting token from the make_number function

                if error:
                   errors.extend(error)
                   continue  

                self.process_token(cur_ln, cur_col, result.lexeme, result.token, numlit_delim, errors, tokens, result.state_nums)

            # string (comms)
            elif self.current_char == '"':
                result, error = self.make_string() # calls the make_string function to tokenize the comms literal

                if error:
                   errors.extend(error)
                   continue

                self.process_token(cur_ln, cur_col, result.lexeme, result.token, commslit_delim, errors, tokens, result.state_nums)

            # single-line comment
            elif self.current_char == '#':
                comments = '#'
                self.advance()
                while self.current_char is not None:
                    # if the next char is a newline, break the loop
                    if self.current_char == '\n':
                        self.process_token(cur_ln, cur_col, comments, TT_COMMENTS1, '\n', errors, tokens, []) 
                        break
                    comments += self.current_char
                    self.advance()
                    
                if self.current_char is None:
                    self.process_token(cur_ln, cur_col, comments, TT_COMMENTS1, '\n', errors, tokens, [])
                    
            # multi-line comment
            elif self.current_char == '`':
                backtick_count = 0
                while self.current_char == '`' and backtick_count < 3: # tries to find the first three backtick opener
                    backtick_count += 1
                    self.advance()

                if backtick_count != 3: # if backtick less than 3, throw an error
                    errors.append(f"Lexical Error: Incomplete comment delimiter at line {self.pos.ln + 1}, column {self.pos.col - backtick_count}")
                else:
                    comment = ""
                    while True:
                        if self.current_char is None: 
                            # throw an error if multi-line comment is not closed with proper 3 backticks
                            errors.append(f"Lexical Error: Unclosed multi-line comment starting at line {self.pos.ln + 1}")
                            break

                        if self.current_char == '`':  
                            close_count = 0
                            while self.current_char == '`' and close_count < 3:
                                close_count += 1
                                self.advance()

                            if close_count == 3:  
                                break
                            else:  
                                comment += '`' * close_count
                        else:
                            comment += self.current_char
                            self.advance()

            # space
            elif self.current_char == ' ':
                # record the previous char as the lhs_space or the char before a space is found
                lhs_space = self.prev_char 

                # tokenize spaces cluster together instead of tokenizing all spaces individually
                while self.current_char == ' ': 
                    self.advance()
                state_num = [0, 417, 418]
                self.process_token(cur_ln, cur_col, ' ', TT_SPACE, space_delim, errors, tokens, state_num)

            # newline
            elif self.current_char == '\n': 
                # tokenize newlines cluster together instead of tokenizing all newline individually
                while self.current_char == '\n':
                    self.advance()
                state_num = [0, 419, 420]
                self.process_token(cur_ln, cur_col, '\\n', TT_NEWLINE, nl_delim, errors, tokens, state_num)
            
            else:
                errors.append(f"Lexical Error: Unknown character ' {self.current_char} ' at line {self.pos.ln + 1}, column {self.pos.col + 1}")
                self.advance()
        
        # append end-of-line in token list
        tokens.append(Token(TT_EOF, TT_EOF, cur_ln, cur_col, []))

        return tokens, errors
    
    ### helper function to create numeric literals ###
    def make_number(self, num_str, state_num):  
        negate = False              # flag to check if num is negative
        dot_count = 0               # counter to determine if num is xp 
        int_len = 0                 # hp whole number length ctr
        dec_len = 0                 # xp decimal length ctr
        errors = []
        zero_int = False            # flag to know when to start counting digits (for leading 0s)
        reserved_dec = ''           # reserved decimal 
        cur_ln = self.pos.ln + 1
        cur_col = self.pos.col + 1
        cur_state = state_num[-1]

        def add_error(message):     # helper func for error message
            errors.append(f"{message} at line {self.pos.ln + 1}, column {self.pos.col - len(num_str) + 1}")
        
        if num_str != '':
            # for negative numeric
            if num_str == '-':      
                if self.current_char is not None and self.current_char == '.':
                    cur_state = 386 # state number for '-.' is 0 -> 271 -> 386
                    state_num.append(cur_state)
                elif self.current_char is not None and self.current_char in NUM:
                    cur_state = 366 # state number for '-{NUM}' is 0 -> 271 -> 366
                    state_num.append(cur_state)
                
                negate = True # flag it as negative numeric
                num_str = ''
            
            # for numeric literals that starts with '.'
            else:                  
                if num_str != '.':
                    cur_state = 352 # state number for '.{NUM}' is 0 -> 320 -> 352
                    state_num.append(cur_state)
                num_str = '0' + num_str
               
                dot_count = 1 # change dot_count to 1, meaning its an xp now
                dec_len = 1    
            
        while self.current_char is not None and self.current_char in NUM + '.':
            if self.current_char == '.':
                
                # throw an error if '.' is found when dot_count is already 1
                if dot_count == 1:  
                    num_str += self.current_char
                    self.advance()
                    while self.current_char is not None and self.current_char not in numlit_delim:
                        num_str += self.current_char
                        self.advance()
                    if negate: num_str = '-' + num_str
                    add_error(f"Lexical Error: Too many decimal points in {num_str}")
                    return [], errors
                
                if self.prev_char == '-': 
                    dot_count += 1
                    num_str += '0.' # '-0.1'
                else:        
                    # for loop to get the correct numbers of state (it counts null as well, check TD)
                    for _ in range((10-len(num_str))+1):  
                        cur_state += 2
                        state_num.append(cur_state)
                    dot_count += 1
                    num_str += '.'
            else:  
                if dot_count == 0:  
                    if int_len < 10:
                        if self.current_char in DIGITS and not zero_int:
                            if num_str == '0':
                                num_str = self.current_char
                                int_len = 1
                                zero_int = True  
                            else:
                                if cur_state == 331 or cur_state == 366:
                                    # since we are already passing [0, 331] or [0, 366] as state_num, we ignore this
                                    pass
                                else:
                                    # cur_state is incremented by 2, check TD
                                    cur_state += 2
                                    state_num.append(cur_state)
                                num_str += self.current_char
                                int_len += 1
                                zero_int = True # no more leading zeroes, so zero_int is changed to True
                        
                        elif self.current_char == '0' and not zero_int:
                            num_str = '0'
                            int_len = 1
                            # leading zeroes
                        elif zero_int:
                            cur_state += 2
                            state_num.append(cur_state)
                            num_str += self.current_char
                            int_len += 1
                    else:  
                        # throw an error if length of whole num exceeds 10
                        while self.current_char is not None and self.current_char not in numlit_delim:
                            num_str += self.current_char
                            self.advance()
                        if negate: num_str = '-' + num_str
                        add_error(f"Lexical Error: Maximum number of whole numbers reached in {num_str}")
                        return [], errors
                else:  
                    if dec_len < 7:
                        if self.current_char == '0' and self.prev_char in NUM:
                            # reserved decimal is used to store the leading zeroes in decimal part
                            reserved_dec += '0'

                        elif self.current_char == '0' and self.prev_char == '.':
                            # if '.0', increment cur_state by 1, check TD
                            cur_state += 1
                            state_num.append(cur_state)
                            num_str += '0'
                            dec_len = 1

                        elif self.current_char in DIGITS and self.prev_char == '0':
                            # no more leading zeroes, concat reserved_dec (if any) + current_char to num_str
                            num_str += reserved_dec + self.current_char
                            dec_len += 1 + len(reserved_dec)
                            if dec_len > 7: 
                                # throw error if decimal length exceeds 7
                                self.advance()
                                while self.current_char is not None and self.current_char not in numlit_delim:
                                    num_str += self.current_char
                                    self.advance()
                                if negate: num_str = '-' + num_str
                                add_error(f"Lexical Error: Maximum number of decimal numbers reached in {num_str}")
                                return [], errors
                            else:
                                # for loop to get correct state_numbers in decimal place
                                for _ in range((10-dec_len)+1):  
                                    cur_state += 2
                                    state_num.append(cur_state)
                                reserved_dec = ''
                        else:
                            if cur_state == 351 or cur_state == 386:
                                # if in cur_state 351 or 386, just add 1, check TD
                                cur_state += 1
                            else:
                                # else, increment by 2
                                cur_state += 2
                            state_num.append(cur_state)
                            num_str += self.current_char
                            dec_len += 1
                    else:  
                        # throw error if decimal length exceeds 7
                        while self.current_char is not None and self.current_char not in numlit_delim:
                            num_str += self.current_char
                            self.advance()
                        if negate: num_str = '-' + num_str
                        add_error(f"Lexical Error: Maximum number of decimal numbers reached in {num_str}")
                        return [], errors
            self.advance()

        state_num.append(cur_state + 1) # add final state
        if dot_count > 0 and num_str.endswith('.'):
            # error for trailing decimal point w/o digits
            if negate: num_str = '-' + num_str
            add_error(f"Lexical Error: Invalid number '{num_str}'. Trailing decimal point without digits")
            return [], errors
        
        if not negate:
            # token_type changes whether dot_count is 1 or 0
            token_type = TT_XP if dot_count >  0 else TT_HP
        else:
            # if negative, add '-' at the beginning of the num_str
            num_str = '-' + num_str
            if num_str == '-0' or num_str == '-0.0':
                return Token('0', TT_HP, cur_ln, cur_col, state_num), errors
            token_type = TT_XP if dot_count > 0 else TT_HP
            
        return Token(num_str, token_type, cur_ln, cur_col, state_num), errors

    ### helper function to create identifiers ###
    def make_identifier(self, id_str, state_num): 
        id_len = len(id_str)
        errors = []
        cur_ln = self.pos.ln + 1
        cur_col = self.pos.col + 1

        def add_error(message):
            errors.append(f"{message} at line {self.pos.ln + 1}, column {self.pos.col - len(id_str) + 1}")

        cur_state = state_num[-1]  # start from the last state
        for _ in range(len(id_str) - 1):  # already have first state, so only add len - 1
            cur_state += 2
            state_num.append(cur_state)

        while self.current_char != None and self.current_char in ALPHANUM + '_':
            if id_len < 30:
                id_str += self.current_char
                id_len += 1
                cur_state += 2
                state_num.append(cur_state)
                self.advance()
            else:
                # throw error if id length exceeds 30
                while self.current_char is not None and self.current_char not in id_delim:
                    id_str += self.current_char
                    self.advance()
                add_error(f"Lexical Error: Maximum number characters reached in '{id_str}'")
                return [], errors
            
        state_num.append(cur_state + 1) # add final state
        return Token(id_str, self.identifiers(id_str), cur_ln, cur_col, state_num), errors

    ### helper function to keep track of existing id, and add number to new ids ###
    def identifiers(self, id_str):
        if id_str not in self.identifier_map:
            self.identifier_map[id_str] = f'id{self.current_id}'
            self.current_id += 1

        return self.identifier_map[id_str]

    ### helper function to tokenize ids ###
    def tokenize_id(self, cur_ln, cur_col, char_str, id_delim, errors, tokens):
        state_num = [0, 207]

        result, error = self.make_identifier(char_str, state_num)

        if error:
            errors.extend(error)
        else:
            self.process_token(cur_ln, cur_col, result.lexeme, result.token, id_delim, errors, tokens, result.state_nums)

    ### helper function to tokenize keywords ###
    def tokenize_keyword(self, cur_ln, cur_col, char_str, valid_delim, errors, tokens, state_num):
        if self.current_char is None: 
            cur_state = state_num[-1]
            state_num.append(cur_state+1)
            self.process_token(cur_ln, cur_col, char_str, char_str, valid_delim, errors, tokens, state_num)
        elif self.current_char in ALPHANUM or self.current_char == '_':
            self.tokenize_id(cur_ln, cur_col, char_str, id_delim, errors, tokens)
        else:
            cur_state = state_num[-1]
            state_num.append(cur_state+1)
            self.process_token(cur_ln, cur_col, char_str, char_str, valid_delim, errors, tokens, state_num)

    ### helper function to create string literals ###
    def make_string(self): 
        cur_ln = self.pos.ln + 1
        cur_col = self.pos.col + 1
        string = ''  
        escape_character = False    # flag if escape_char is found
        errors = []
        self.advance()  
        state_num = [0, 401]
        cur_state = 401

        escape_characters = {
            'n': '\n',   
            't': '\t',   
            '"': '"',    
            '\\': '\\' 
        }

        while self.current_char is not None:
            if escape_character:
                if self.current_char in 'nt"\\':
                    state_num.extend([402, 403])
                    cur_state = 403  
                    resolved_char = escape_characters.get(self.current_char, self.current_char)
                    string += resolved_char 
                    escape_character = False    
                else:
                    string += '\\' + self.current_char    
                    escape_character = False                   
                
            else:
                if self.current_char == '\\':
                    if cur_state == 403:
                        state_num.append(401)
                        cur_state = 401
                    
                    # flag escape_character as True since '\' is found within the string
                    escape_character = True
                elif self.current_char == '"': 
                    if cur_state == 403:
                        state_num.extend([404, 405])
                    else:
                        state_num.extend([406, 407])
                    self.advance() 
                    return Token('"' + string + '"', TT_COMMS, cur_ln, cur_col, state_num), errors  
                elif self.current_char == '\n':
                    errors.append(f'Lexical Error: Unclosed string literal "{string} at line {self.pos.ln + 1}, column {self.pos.col - len(string)}')
                    return [], errors
                else:
                    if cur_state == 403:
                        state_num.append(401)
                        cur_state = 401
                    else:
                        pass
                    string += self.current_char  
            self.advance()

        errors.append(f'Lexical Error: Unclosed string literal "{string} at line {self.pos.ln + 1}, column {self.pos.col - len(string)}')
        return [], errors

### RUN ###
def run(fn, text):
    if text == "":
        return [], ["No code in the module."]
    lexer = Lexer(fn, text)
    tokens, error = lexer.make_tokens()

    # for tok in tokens:
    #     print(f"{tok.token}, {tok.lexeme}: {tok.state_nums}")

    return tokens, error

