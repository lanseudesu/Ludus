import eel
import os, sys
import tkinter as tk
from tkinter import filedialog
from ludus import ast, lexer, parser
import time

eel.init('web')

current_file = None
#Option 1: Clear same window and update editor
@eel.expose
def create_new_file():
    global current_file
    current_file = None
    eel.clearError()
    eel.clearTerminal()
    eel.clearLexemeToken()
    return "" 

#Option 1 Open File - Tkinter
@eel.expose
def open_file():
    global current_file
    root = tk.Tk()
    root.withdraw()  
    root.attributes('-topmost', True)
    file_path = filedialog.askopenfilename(filetypes=[("Ludus Files", "*.lds")])
    if file_path:
        eel.clearError()
        eel.clearTerminal()
        eel.clearLexemeToken()
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
        current_file = file_path
        return content
    return None 

@eel.expose
def save_file(content):
    global current_file
    if current_file:
        with open(current_file, "w", encoding="utf-8") as file:
            file.write(content)
        return True
    return False  

@eel.expose
def save_file_as(content):
    global current_file
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)

    file_path = filedialog.asksaveasfilename(defaultextension=".lds",
                                                filetypes=[("Ludus Files", "*.lds"), ("All Files", "*.*")])
    if file_path:
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(content)
        current_file = file_path
        return True
    return False  

@eel.expose
def lexical_analyzer(input_text):
    tokens, error = lexer.run(current_file, input_text)

    if error:
        eel.updateError("\n\n".join(error))
    else:
        eel.updateError("No lexical errors found!")
    
    if tokens:
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
    result = parser.parse(current_file, input_text)

    eel.updateTerminal(result)

@eel.expose
def semantic_analyzer(input_text):
    #result, table = ast.check(current_file, input_text)
    # output = str(result) + "\n" + str(table) 

    result = ast.check(current_file, input_text)
    output = str(result)  

    eel.updateTerminal(output)

@eel.expose
def runtime_backend(input_text):
    # from ludus.runtime.interpreter import reset_interpreter  # <- we'll define this
    # reset_interpreter()

    print("running runtime again")
    #time.sleep(0.2)
    result = ast.check(current_file, input_text, True)
    
    eel.updateTerminal(result)

# Option 1
@eel.expose
def exit_app(): 
    os._exit(0)

eel.init("web")
eel.start('index.html', size=(1920,1080)) 
