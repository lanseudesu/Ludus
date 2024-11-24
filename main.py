import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import lexer

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("ludus.json")

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
        self.file_menu.add_command(label="Open", command=self.open_file, accelerator="Control + O") 
        self.bind_all("<Control-o>", lambda event: self.open_file())
        self.file_menu.add_command(label="Save", command=self.save_file, accelerator="Control + S")
        self.bind_all("<Control-s>", lambda event: self.save_file())
        self.file_menu.add_command(label="Save As", command=self.save_as_file, accelerator="Control + Shift + S")
        self.bind_all("<Control-Shift-s>", lambda event: self.save_as_file())
        self.file_menu.add_command(label="Close File", command=self.close_file, accelerator="Control + Q")
        self.bind_all("<Control-q>", lambda event: self.close_file())
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self.exit_app, accelerator="Control + W")
        self.bind_all("<Control-w>", lambda event: self.exit_app())

        # settings options
        self.theme_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.theme = tk.IntVar(value=2)
        self.theme_menu.add_radiobutton(label="Light Mode", value=1, variable=self.theme, command=self.change_theme)
        self.theme_menu.add_radiobutton(label="Dark Mode", value=2, variable=self.theme, command=self.change_theme)
        self.settings_menu.add_cascade(label="Theme", menu=self.theme_menu)

        # text editor and terminal frame
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        # textbox
        self.editor_frame = ctk.CTkFrame(self.main_frame)
        self.editor_frame.pack(side="top", fill="both", expand=True)
        
        self.line_numbers = tk.Label(self.editor_frame, width=4, padx=4, anchor="nw", background="gray12", foreground="#fdca01", font=("Consolas", 12))
        self.line_numbers.pack(side="left", fill="y")

        self.editor_xscrollbar = tk.Scrollbar(self.editor_frame, orient="horizontal", command=self.editor_x_scroll)
        self.editor_xscrollbar.pack(side="bottom", fill="x")

        self.editor_yscrollbar = tk.Scrollbar(self.editor_frame, orient="vertical", command=self.editor_y_scroll)
        self.editor_yscrollbar.pack(side="right", fill="y")

        self.code_editor = tk.Text(self.editor_frame, wrap=tk.NONE, font=("Consolas", 12))
        self.code_editor.pack(side="left", fill="both", expand=True)

        self.code_editor.config(xscrollcommand=self.editor_xscrollbar.set)
        self.code_editor.config(yscrollcommand=self.editor_yscrollbar.set)

        self.code_editor.bind("<KeyRelease>", self.update_line_numbers)
        self.code_editor.bind("<MouseWheel>", self.update_line_numbers)
        self.code_editor.bind("<Button-1>", self.update_line_numbers)
        self.code_editor.bind("<Configure>", self.update_line_numbers)

        # terminal
        self.terminal_frame = ctk.CTkFrame(self.main_frame)
        self.terminal_frame.pack(side="bottom", fill="x", expand=False)

        self.terminal_label = ctk.CTkLabel(self.terminal_frame, text="Terminal", anchor="w", fg_color="gray12", text_color="white", font=("Arial", 14, "bold"))
        self.terminal_label.pack(fill="x")

        # make scrollbar sync with the text after line 10
        self.terminal_xscrollbar = tk.Scrollbar(self.terminal_frame, orient="vertical", command=self.terminal_x_scroll)
        self.terminal_xscrollbar.pack(side="right", fill="y")

        self.terminal = tk.Text(self.terminal_frame, wrap="word", bg="gray12", fg="white", insertbackground="white", height=12, font=("Consolas", 12))
        self.terminal.pack(fill="both", expand=True)

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
    def open_file(self): # TODO: warningan yung user na i-save muna ang file bago mag-open ng bago kung hindi pa nasasave
        self.file_path = filedialog.askopenfilename(filetypes=[("Ludus Files", "*.lds")])
        if self.file_path:
            with open(self.file_path, 'r') as file:
                content = file.read()
                self.lexeme_listbox.delete(0, tk.END)
                self.token_listbox.delete(0, tk.END)
                self.error_field.config(state=tk.NORMAL) 
                self.error_field.delete(1.0, tk.END)      
                self.error_field.config(state=tk.DISABLED)
                self.code_editor.delete(1.0, tk.END)
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

    def close_file(self): # TODO: warningan yung user na i-save muna ang file kung hindi pa nasasave
        self.lexeme_listbox.delete(0, tk.END)
        self.token_listbox.delete(0, tk.END)
        self.error_field.config(state=tk.NORMAL) 
        self.error_field.delete(1.0, tk.END)      
        self.error_field.config(state=tk.DISABLED)
        self.code_editor.delete(1.0, tk.END)
        self.file_path = None

    def exit_app(self): # TODO: warningan yung user na i-save muna ang file kung hindi pa nasasave
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

    def editor_x_scroll(self, *args):
        self.code_editor.xview(*args)
    
    def editor_y_scroll(self, *args):
        self.code_editor.yview(*args)
        self.update_line_numbers()

    def terminal_x_scroll(self, *args):
        self.terminal.yview(*args)

    # Tokenize button function
    def process_text(self):
        input_text = self.code_editor.get("0.0", tk.END).strip()  
        tokens, error = lexer.run(self.file_path, input_text)

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