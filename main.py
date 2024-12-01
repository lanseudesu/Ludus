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
        self.configure(menu=self.menu_bar)

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

        # text editor frame
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        self.editor_frame = ctk.CTkFrame(self.main_frame)
        self.editor_frame.pack(side="top", fill="both", expand=True)

        # code editor
        self.code_editor = ctk.CTkTextbox(self.editor_frame, wrap="none", font=("Consolas", 12), undo=True, activate_scrollbars=False)
        self.code_editor.grid(row=0, column=1, sticky="nsew")

        # line numbers
        self.line_numbers = ctk.CTkLabel(self.editor_frame, width=4, padx=4, anchor="nw", font=("Consolas", 12))
        self.line_numbers.grid(row=0, column=0, sticky="ns")

        # horizontal scrollbar
        self.editor_xscrollbar = ctk.CTkScrollbar(self.editor_frame, command=self.editor_x_scroll, orientation="horizontal")
        self.editor_xscrollbar.grid(row=1, column=1, sticky="ew")

        # vertical scrollbar
        self.editor_yscrollbar = ctk.CTkScrollbar(self.editor_frame, command=self.editor_y_scroll, orientation="vertical")
        self.editor_yscrollbar.grid(row=0, column=2, sticky="ns")

        # configure grid weights to make widgets resize properly
        self.editor_frame.rowconfigure(0, weight=1)  # allow code editor to expand vertically
        self.editor_frame.columnconfigure(1, weight=1)  # allow code editor to expand horizontally

        self.code_editor.configure(xscrollcommand=self.update_horizontal_scrollbar)
        self.code_editor.configure(yscrollcommand=self.update_vertical_scrollbar)

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

        self.list_scrollbar = ctk.CTkScrollbar(self.list_frame)
        self.list_scrollbar.pack(side="right", fill="y")

        self.lexeme_label = ctk.CTkLabel(self.lexeme_frame, text="Lexemes", font=("Arial", 14, "bold"))
        self.lexeme_label.pack(side="top", padx=10)
        self.lexeme_listbox = tk.Listbox(self.lexeme_frame, font=("Arial", 10), width=25, yscrollcommand=self.list_scrollbar.set)
        self.lexeme_listbox.pack(side="top", padx=10, fill="both", expand=True)

        self.token_label = ctk.CTkLabel(self.token_frame, text="Tokens", font=("Arial", 14, "bold"))
        self.token_label.pack(side="top", padx=10)
        self.token_listbox = tk.Listbox(self.token_frame, font=("Arial", 10), width=25, yscrollcommand=self.list_scrollbar.set)
        self.token_listbox.pack(side="top", padx=10, fill="both", expand=True)
        
        self.list_scrollbar.configure(command=self.sync_scroll)

        # tokenize button
        self.tokenize_button = ctk.CTkButton(self.info_frame, text="Tokenize", font=("Arial", 13, "bold"), command=self.process_text)
        self.tokenize_button.pack(side="bottom", pady=10)
        
        self.error_field = tk.Text(self.info_frame, height=15, font=("Arial", 11), bg="lightgray", fg="red", width=50)
        self.error_field.pack(side="bottom",padx=5, pady=5, fill="x")

        self.error_label = ctk.CTkLabel(self.info_frame, text="Errors", font=("Arial", 14, "bold"))
        self.error_label.pack(side="bottom", pady=5)

        self.error_field.configure(state=tk.DISABLED)
    
    def sync_scroll(self, *args):
        self.lexeme_listbox.yview(*args)
        self.token_listbox.yview(*args)

    def open_file(self): # TODO: warningan yung user na i-save muna ang file bago mag-open ng bago kung hindi pa nasasave
        self.file_path = filedialog.askopenfilename(filetypes=[("Ludus Files", "*.lds")])
        if self.file_path:
            with open(self.file_path, 'r') as file:
                content = file.read()
                self.lexeme_listbox.delete(0, tk.END)
                self.token_listbox.delete(0, tk.END)
                self.error_field.configure(state=tk.NORMAL) 
                self.error_field.delete(1.0, tk.END)      
                self.error_field.configure(state=tk.DISABLED)
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
        self.error_field.configure(state=tk.NORMAL) 
        self.error_field.delete(1.0, tk.END)      
        self.error_field.configure(state=tk.DISABLED)
        self.code_editor.delete(1.0, tk.END)
        self.file_path = None

    def exit_app(self): # TODO: warningan yung user na i-save muna ang file kung hindi pa nasasave
        self.quit()

    # Settings function
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
        self.line_numbers.configure(text=line_numbers_string)

    def editor_x_scroll(self, *args):
        self.code_editor.xview(*args)
    
    def editor_y_scroll(self, *args):
        self.code_editor.yview(*args)
        self.update_line_numbers()

    def update_horizontal_scrollbar(self, *args):
        self.editor_xscrollbar.set(*args)
        self.check_scrollbar_visibility()

    def update_vertical_scrollbar(self, *args):
        self.editor_yscrollbar.set(*args)
        self.check_scrollbar_visibility()

    def check_scrollbar_visibility(self, event=None):
        # tracks if scrollbar alr visible
        if not hasattr(self, "x_scrollbar_visible"):
            self.x_scrollbar_visible = False
        if not hasattr(self, "y_scrollbar_visible"):
            self.y_scrollbar_visible = False

        # check horizontal
        if self.code_editor.xview()[0] > 0 or self.code_editor.xview()[1] < 1:
            if not self.x_scrollbar_visible:
                self.editor_xscrollbar.grid(row=1, column=1, sticky="ew")
                self.x_scrollbar_visible = True
        else:
            if not self.x_scrollbar_visible:  
                self.editor_xscrollbar.grid_remove()
                self.x_scrollbar_visible = False

        # check vertical
        if self.code_editor.yview()[0] > 0 or self.code_editor.yview()[1] < 1:
            if not self.y_scrollbar_visible:
                self.editor_yscrollbar.grid(row=0, column=2, sticky="ns")
                self.y_scrollbar_visible = True
        else:
            if not self.y_scrollbar_visible:  
                self.editor_yscrollbar.grid_remove()
                self.y_scrollbar_visible = False

    # Tokenize button function
    def process_text(self):
        input_text = self.code_editor.get("0.0", tk.END).strip()  
        tokens, error = lexer.run(self.file_path, input_text)

        self.error_field.configure(state=tk.NORMAL) 
        self.error_field.delete(1.0, tk.END)      
        self.error_field.configure(state=tk.DISABLED)

        if error:  
            self.error_field.configure(state=tk.NORMAL)
            for errors in error:
                self.error_field.insert(tk.END, errors + '\n')  
            self.error_field.configure(state=tk.DISABLED)
            
        self.lexeme_listbox.delete(0, tk.END)
        self.token_listbox.delete(0, tk.END)

        for token in tokens:
            self.lexeme_listbox.insert(tk.END, token.lexeme)
            self.token_listbox.insert(tk.END, token.token)
        
        for item in range(self.lexeme_listbox.size()):
            color = "#f0f0f0" if item % 2 == 0 else "#ffffff"
            self.lexeme_listbox.itemconfig(item, {'bg': color})
        
        for item in range(self.token_listbox.size()):
            color = "#f0f0f0" if item % 2 == 0 else "#ffffff"
            self.token_listbox.itemconfig(item, {'bg': color})

app = App()
app.mainloop()