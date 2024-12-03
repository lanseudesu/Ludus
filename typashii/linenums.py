import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import lexer

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("ludus.json") # change; make custom theme (ludus.json); tuple["light", "dark"]
#logo colors = maroon(L): orig-#be0108 or mychoice#690104, yellow(D): #fdca01, mustard/gold(S): #f2a61d, white: #ffffff

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Ludus")
        self.iconbitmap('ludus.ico')
        self.geometry("1300x800")

        self.file_path = None
        
        # menu bar
        self.menu_bar = tk.Menu(self)
        self.config(menu=self.menu_bar)

        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)
        self.settings_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Settings", menu=self.settings_menu)

        # file options
        self.file_menu.add_command(label="Open", command=self.open_file, accelerator="Ctrl + O") 
        self.bind_all("<Control-o>", lambda event: self.open_file())
        self.file_menu.add_command(label="Save", command=self.save_file, accelerator="Ctrl + S")
        self.bind_all("<Control-s>", lambda event: self.save_file())
        self.file_menu.add_command(label="Save As", command=self.save_as_file, accelerator="Ctrl + Shift + S")
        self.bind_all("<Control-Shift-s>", lambda event: self.save_as_file())
        self.file_menu.add_command(label="Close File", command=self.close_file, accelerator="Ctrl + Q")
        self.bind_all("<Control-q>", lambda event: self.close_file())
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self.exit_app, accelerator="Ctrl + W")
        self.bind_all("<Control-w>", lambda event: self.exit_app())

        # settings options
        self.theme_menu = tk.Menu(self.menu_bar, tearoff=False)
        self.theme = tk.IntVar(value=2)
        self.theme_menu.add_radiobutton(label="Light Mode", value=1, variable=self.theme, command=self.change_theme)
        self.theme_menu.add_radiobutton(label="Dark Mode", value=2, variable=self.theme, command=self.change_theme)
        self.settings_menu.add_cascade(menu=self.theme_menu, label="Theme")

        # text editor and terminal frame
        self.editor_frame = ctk.CTkFrame(self)
        self.editor_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        # textbox line numbers and scrollbar
        self.line_numbers = tk.Label(self.editor_frame, width=4, padx=4, anchor="nw", background="gray12", foreground="#fdca01", font=("Consolas", 13))
        self.line_numbers.pack(side="left", fill="y")

        self.scrollbar = tk.Scrollbar(self.editor_frame, orient="vertical", command=self.sync_scroll)
        self.scrollbar.pack(side="right", fill="y")

        self.code_editor = tk.Text(self.editor_frame, wrap=tk.NONE, font=("Consolas", 13))
        self.code_editor.pack(side="left", fill="both", expand=True)
        
        self.code_editor.config(yscrollcommand=self.scrollbar.set)

        self.code_editor.bind("<KeyRelease>", self.update_line_numbers)
        self.code_editor.bind("<MouseWheel>", self.update_line_numbers)
        self.code_editor.bind("<Button-1>", self.update_line_numbers)
        self.code_editor.bind("<Configure>", self.update_line_numbers)

        # lexeme, token, and error frame
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

        self.lexeme_label = ctk.CTkLabel(self.lexeme_frame, text="Lexemes", font=("Arial", 14, "bold"))
        self.lexeme_label.pack(side="top", padx=10)
        self.lexeme_listbox = tk.Listbox(self.lexeme_frame, font=("Arial", 10), width=25)
        self.lexeme_listbox.pack(side="top", padx=10, fill="both", expand=True)

        self.token_label = ctk.CTkLabel(self.token_frame, text="Tokens", font=("Arial", 14, "bold"))
        self.token_label.pack(side="top", padx=10)
        self.token_listbox = tk.Listbox(self.token_frame, font=("Arial", 10), width=25)
        self.token_listbox.pack(side="top", padx=10, fill="both", expand=True)

        # tokenize button
        self.tokenize_button = ctk.CTkButton(self.info_frame, text="Tokenize", font=("Arial", 13, "bold"), command=self.process_text)
        self.tokenize_button.pack(side="bottom", pady=10)
        
        self.error_field = tk.Text(self.info_frame, height=15, font=("Arial", 10), bg="lightgray", fg="red", width=50)
        self.error_field.pack(side="bottom",padx=5, pady=5, fill="x")

        self.error_label = ctk.CTkLabel(self.info_frame, text="Errors", font=("Arial", 14, "bold"))
        self.error_label.pack(side="bottom", pady=5)

        self.error_field.config(state=tk.DISABLED)

    # File handling methods
    def open_file(self):
        self.file_path = filedialog.askopenfilename(filetypes=[("Ludus Files", "*.lds")])
        if self.file_path:
            with open(self.file_path, 'r') as file:
                content = file.read()
                self.code_editor.delete(1.0, tk.END)
                self.code_editor.insert(tk.END, content)
                
    def save_file(self):
        if self.file_path:
            content = self.code_editor.get(1.0, tk.END)   
            with open(self.file_path, 'w') as file:
                file.write(content)  
                messagebox.showinfo("File Saved", f"Saved: {self.file_path}")
        else: 
            self.save_as_file()  

    def save_as_file(self):
        self.file_path = filedialog.asksaveasfilename(defaultextension=".lds",
                                                      filetypes=[("Ludus Files", "*.lds"), ("All Files", "*.*")])
        if self.file_path:
            with open(self.file_path, 'w') as file:
                content = self.code_editor.get(1.0, tk.END) 
                file.write(content)  
                messagebox.showinfo("File Saved", f"Saved as: {self.file_path}")

    def close_file(self):
        self.lexeme_listbox.delete(0, tk.END)
        self.token_listbox.delete(0, tk.END)
        self.error_field.config(state=tk.NORMAL) 
        self.error_field.delete(1.0, tk.END)      
        self.error_field.config(state=tk.DISABLED)
        self.code_editor.delete(1.0, tk.END)
        self.file_path = None
        messagebox.showinfo("File Closed", "The file has been closed.")

    def exit_app(self):
        self.quit()

    # Settings functions
    def change_theme(self):
        theme_value = self.theme.get()
        if theme_value == 1:
            ctk.set_appearance_mode("light") 
        elif theme_value == 2:
            ctk.set_appearance_mode("dark")
    
    # Textbox functions
    def update_line_numbers(self, event=None):
        first_visible_line = int(self.code_editor.index("@0,0").split(".")[0])
        last_visible_line = int(self.code_editor.index("@0,%d" % self.code_editor.winfo_height()).split(".")[0])
        line_numbers_string = "\n".join(str(i) for i in range(first_visible_line, last_visible_line + 1))
        self.line_numbers.config(text=line_numbers_string)

    def sync_scroll(self, *args):
        self.code_editor.yview(*args)
        self.update_line_numbers()

    # Tokenize button function
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