import eel
from ludus import lexer

# Initialize the Eel app
eel.init('web')  # The folder containing web files

# Python function callable from JavaScript
@eel.expose
def navigate_to(section):
    print(f"Navigating to {section}")
    # Logic to update the app state or load specific content
    if section == "home":
        # Handle home navigation
        pass
    elif section == "features":
        # Handle features navigation
        pass
    elif section == "about":
        # Handle about navigation
        pass
    elif section == "contact":
        # Handle contact navigation
        pass

@eel.expose
def process_text(input_text):
    tokens, error = lexer.run("yo", input_text)

    if error:
        eel.updateError("\n".join(error))

    lexemes = [token.lexeme for token in tokens]  # Extract lexemes from tokens
    tokens = [token.token for token in tokens]
    eel.updateLexemeToken("\n".join(lexemes),"\n".join(tokens))

# Start the Eel app
eel.start('index.html', size=(1920,1080))