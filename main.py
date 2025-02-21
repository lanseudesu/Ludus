import eel
from ludus import ast, lexer, parser

eel.init('web')  

@eel.expose
def lexical_analyzer(input_text):
    tokens, error = lexer.run("yo", input_text)

    if error:
        eel.updateError("\n\n".join(error))
    else:
        eel.clearError()

    tokens.pop()
    linenumbers = [token.line for token in tokens]
    colnumbers = [token.column for token in tokens]
    lexemes = [token.lexeme for token in tokens]  
    tokens = [token.token for token in tokens]
    formatted_lexemes = "\n".join(f'{line}.{col}: {lex}' for line, col, lex in zip(linenumbers, colnumbers, lexemes))
    formatted_tokens = "\n".join(f'{line}.{col}: {tok}' for line, col, tok in zip(linenumbers, colnumbers, tokens))


    eel.updateLexemeToken((formatted_lexemes), (formatted_tokens))

@eel.expose
def syntax_analyzer(input_text):
    result = parser.parse("yo", input_text)

    eel.updateTerminal(result)

@eel.expose
def semantic_analyzer(input_text):
    result, table = ast.check("yo", input_text)
    
    output = str(result) + "\n" + str(table) 
    eel.updateTerminal(output)

eel.start('semantic_page.html', size=(1920,1080)) 