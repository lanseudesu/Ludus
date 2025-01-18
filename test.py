import eel
from ludus import lexer

eel.init('web')  

@eel.expose
def navigate_to(section):
    print(f"Navigating to {section}")
    if section == "code-gen":
        pass
    elif section == "lexer":
        pass
    elif section == "syntax":
        pass
    elif section == "semantic":
        pass

@eel.expose
def process_text(input_text):
    tokens, error = lexer.run("yo", input_text)

    if error:
        eel.updateError("\n".join(error))

    lexemes = [token.lexeme for token in tokens]  
    tokens = [token.token for token in tokens]
    eel.updateLexemeToken("\n".join(lexemes),"\n".join(tokens))

# Start the Eel app
eel.start('index.html', size=(1920,1080))