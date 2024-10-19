import customtkinter as ctk
import tkinter as tk
import lexer

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Ludus")
        self.geometry("1300x800")

        # text editor frame
        self.editor_frame = ctk.CTkFrame(self)
        self.editor_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        # textbox
        self.code_editor = tk.Text(self.editor_frame, wrap=tk.NONE, font=("Consolas", 12))
        self.code_editor.pack(fill="both", expand=True)

        # lexeme, token, error frame
        self.info_frame = ctk.CTkFrame(self)
        self.info_frame.pack(side="right", fill="both", padx=10, pady=10, expand=False)

        # frame for lexeme and token list
        self.list_frame = ctk.CTkFrame(self.info_frame)
        self.list_frame.pack(side="top", fill="both", expand=True) 

        # vertical frames for lexeme and token list
        self.lexeme_frame = ctk.CTkFrame(self.list_frame)
        self.lexeme_frame.pack(side="left", padx=10, fill="both", expand=True)

        self.token_frame = ctk.CTkFrame(self.list_frame)
        self.token_frame.pack(side="left", padx=10, fill="both", expand=True)

        self.lexeme_label = ctk.CTkLabel(self.lexeme_frame, text="Lexemes")
        self.lexeme_label.pack(side="top", padx=10)
        self.lexeme_listbox = tk.Listbox(self.lexeme_frame, font=("Arial", 10), width=20)
        self.lexeme_listbox.pack(side="top", padx=10, fill="both", expand=True)

        self.token_label = ctk.CTkLabel(self.token_frame, text="Tokens")
        self.token_label.pack(side="top", padx=10)
        self.token_listbox = tk.Listbox(self.token_frame, font=("Arial", 10), width=20)
        self.token_listbox.pack(side="top", padx=10, fill="both", expand=True)

        # tokenize button
        self.tokenize_button = ctk.CTkButton(self.info_frame, text="Tokenize", command=self.process_text)
        self.tokenize_button.pack(side="bottom", pady=10)
        
        self.error_field = tk.Text(self.info_frame, height=15, font=("Arial", 10), bg="lightgray", fg="red", width=50)
        self.error_field.pack(side="bottom",padx=5, pady=5, fill="x")

        self.error_label = ctk.CTkLabel(self.info_frame, text="Errors")
        self.error_label.pack(side="bottom",pady=5)

        self.error_field.config(state=tk.DISABLED)

    def process_text(self):
        input_text = self.code_editor.get("0.0", tk.END).strip()  
        tokens, error = lexer.run('<stdin>', input_text)

        self.error_field.config(state=tk.NORMAL) 
        self.error_field.delete(1.0, tk.END)      
        self.error_field.config(state=tk.DISABLED)

        if error:  
            self.error_field.config(state=tk.NORMAL)
            for errors in error:
                self.error_field.insert(tk.END, errors + '\n')  
            self.error_field.config(state=tk.DISABLED)
            
        self.lexeme_listbox.delete(0, tk.END)
        self.token_listbox.delete(0, tk.END)

        for token in tokens:
            self.lexeme_listbox.insert(tk.END, token.lexeme)
            self.token_listbox.insert(tk.END, token.token)


app = App()
app.mainloop()

# def execute_run(filename):
#     try:
#         with open(filename, 'r') as file:
#             text = file.read()
#         result, error = lantits.run(filename, text)
        
#         if error:
#             print(error.as_string())
            
#     except FileNotFoundError:
#         print(f"Error: The file '{filename}' was not found.")

# # The main loop where the user can either run files or enter commands interactively
# if __name__ == "__main__":
#     while True:
#         text = input('lantits -> ')

#         # Allow the user to exit the REPL
#         if text.strip().lower() == 'exit':
#             break

#         # Check if the user wants to load and execute a file
#         if text.startswith('run(') and text.endswith(')'):
#             # Extract the filename from the input: execute_run('filename')
#             filename = text[len('run('):-1].strip().strip("'\"")
#             execute_run(filename)
#         else:
#             # Otherwise, process the input interactively
#             result, error = lantits.run('<stdin>', text)

#             if error:
#                 print(error.as_string())
#             else:
#                 print(result)