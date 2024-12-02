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

        # Text editor frame
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        self.editor_frame = ctk.CTkFrame(self.main_frame)
        self.editor_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # code editor
        self.code_editor = ctk.CTkTextbox(self.editor_frame, wrap="none", font=("Consolas", 15), undo=True, activate_scrollbars=False)
        self.code_editor.grid(row=0, column=1, sticky="nsew",pady=5, padx=(0,5))

        # Create the label inside the frame
        self.line_numbers = ctk.CTkTextbox(self.editor_frame, font=("Consolas", 15), width=35, wrap="none", text_color="#fdca01",activate_scrollbars=False)
        self.line_numbers.grid(row=0, column=0, sticky="ns",pady=5, padx=(5,0))

        # horizontal scrollbar
        self.editor_xscrollbar = ctk.CTkScrollbar(self.editor_frame, command=self.editor_x_scroll, orientation="horizontal")
        self.editor_xscrollbar.grid(row=1, column=1, sticky="ew")

        # vertical scrollbar
        self.editor_yscrollbar = ctk.CTkScrollbar(self.editor_frame, command=self.editor_y_scroll, orientation="vertical")
        self.editor_yscrollbar.grid(row=0, column=2, sticky="ns")

        self.code_editor.configure(xscrollcommand=self.update_horizontal_scrollbar)
        self.code_editor.configure(yscrollcommand=self.update_vertical_scrollbar)

        self.code_editor.bind("<KeyRelease>", self.update_line_numbers)
        self.code_editor.bind("<MouseWheel>", self.update_line_numbers)
        self.code_editor.bind("<Button-1>", self.update_line_numbers)
        self.code_editor.bind("<Configure>", self.update_line_numbers)

        # lexeme, token, and error frame
        self.info_frame = ctk.CTkFrame(self)
        self.info_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        # frame for lexeme and token list
        self.list_frame = ctk.CTkFrame(self.info_frame)
        self.list_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # vertical frames for lexeme and token list
        self.lexeme_frame = ctk.CTkFrame(self.list_frame)
        self.lexeme_frame.grid(row=0, column=0, padx=10, sticky="nsew")

        self.token_frame = ctk.CTkFrame(self.list_frame)
        self.token_frame.grid(row=0, column=1, padx=10, sticky="nsew")

        self.list_scrollbar = ctk.CTkScrollbar(self.list_frame)
        self.list_scrollbar.grid(row=0, column=2, sticky="ns")

        self.lexeme_label = ctk.CTkLabel(self.lexeme_frame, text="Lexemes", font=("Consolas", 15, "bold"))
        self.lexeme_label.grid(row=0, column=0, padx=10, sticky="n")
        self.lexeme_textbox = ctk.CTkTextbox(self.lexeme_frame, font=("Consolas", 15), width=250, height=300, activate_scrollbars=False)
        self.lexeme_textbox.grid(row=1, column=0, padx=0, pady=0, sticky="nsew")

        self.token_label = ctk.CTkLabel(self.token_frame, text="Tokens", font=("Consolas", 14, "bold"))
        self.token_label.grid(row=0, column=0, padx=10, sticky="n")
        self.token_textbox = ctk.CTkTextbox(self.token_frame, font=("Consolas", 15), width=250, height=300, activate_scrollbars=False)
        self.token_textbox.grid(row=1, column=0, padx=0, pady=0, sticky="nsew")
        
        self.list_scrollbar.configure(command=self.sync_scroll)
        
        self.error_label = ctk.CTkLabel(self.info_frame, text="Errors", font=("Arial", 14, "bold"))
        self.error_label.grid(row=1, column=0, padx=10, pady=0, sticky="n")

        # error field (Text widget)
        self.error_field = tk.Text(self.info_frame, height=15, font=("Arial", 11), bg="lightgray", fg="red", width=50)
        self.error_field.grid(row=2, column=0, padx=15, pady=5, sticky="sew")
        self.error_field.configure(state=tk.DISABLED)

        # tokenize button
        self.tokenize_button = ctk.CTkButton(self.info_frame, text="Tokenize", font=("Arial", 13, "bold"), command=self.process_text)
        self.tokenize_button.grid(row=3, column=0, padx=50, pady=5, sticky="n")

        # Configure root window grid weights
        self.grid_rowconfigure(0, weight=1)  # Allow row 0 to expand vertically
        self.grid_columnconfigure(0, weight=3)  # Allow column 0 (editor) to expand horizontally more
        self.grid_columnconfigure(1, weight=0)  # Allow column 1 (info frame) to expand horizontally less

        # Configure main frame
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # Configure info frame
        self.info_frame.grid_rowconfigure(0, weight=3)
        self.info_frame.grid_columnconfigure(0, weight=0)

        # Adjust the row weights to make sure the content expands correctly
        self.info_frame.grid_rowconfigure(1, weight=0)  # Tokenize button doesn't need to expand vertically
        self.info_frame.grid_rowconfigure(2, weight=0)  # Error label doesn't need to expand vertically
        self.info_frame.grid_rowconfigure(3, weight=1)  # Error field should expand vertically

        self.lexeme_frame.grid_rowconfigure(1, weight=1)
        self.token_frame.grid_rowconfigure(1, weight=1)

        # Configure list_frame to expand
        self.list_frame.grid_rowconfigure(0, weight=1)  # Allow the lexeme and token list frames to expand
        self.list_frame.grid_columnconfigure(0, weight=0)

        #self.lexeme_frame.grid_columnconfigure(0, weight=1)

        # Configure editor frame
        self.editor_frame.grid_rowconfigure(0, weight=1)  # Code editor
        self.editor_frame.grid_columnconfigure(1, weight=1)  # Code editor horizontal expansion
        self.editor_frame.grid_columnconfigure(0, weight=0)

    def sync_scroll(self, *args):
        self.lexeme_textbox.yview(*args)
        self.token_textbox.yview(*args)

    def open_file(self): # TODO: warningan yung user na i-save muna ang file bago mag-open ng bago kung hindi pa nasasave
        self.file_path = filedialog.askopenfilename(filetypes=[("Ludus Files", "*.lds")])
        if self.file_path:
            with open(self.file_path, 'r') as file:
                content = file.read()
                self.lexeme_textbox.delete(0, tk.END)
                self.token_textbox.delete(0, tk.END)
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
        self.lexeme_textbox.delete(0, tk.END)
        self.token_textbox.delete(0, tk.END)
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
        # Get the first and last visible lines based on the editor height
        first_visible_line = int(self.code_editor.index("@0,0").split(".")[0])
        last_visible_line = int(self.code_editor.index("@0,%d" % self.code_editor.winfo_height()).split(".")[0])
        
        # Create a string of line numbers to display
        line_numbers_string = "\n".join(str(i) for i in range(first_visible_line, last_visible_line + 1))
        
        # Update the textbox with the line numbers
        self.line_numbers.delete(1.0, "end")  # Clear existing text
        self.line_numbers.insert("end", line_numbers_string)  # Insert the new line numbers

        self.line_numbers.update_idletasks()

    def editor_x_scroll(self, *args):
        self.code_editor.xview(*args)
    
    def editor_y_scroll(self, *args):
        self.code_editor.yview(*args)
        self.line_numbers.yview(*args)
        self.update_line_numbers()

    def update_horizontal_scrollbar(self, *args):
        self.editor_xscrollbar.set(*args)
        self.check_scrollbar_visibility()

    def update_vertical_scrollbar(self, *args):
        self.editor_yscrollbar.set(*args)
        self.check_scrollbar_visibility()

    def check_scrollbar_visibility(self, event=None):
        # Track visibility state
        if not hasattr(self, "x_scrollbar_visible"):
            self.x_scrollbar_visible = False
        if not hasattr(self, "y_scrollbar_visible"):
            self.y_scrollbar_visible = False

        # Check horizontal scrollbar
        if self.code_editor.xview()[0] > 0 or self.code_editor.xview()[1] < 1:
            if not self.x_scrollbar_visible:
                self.editor_xscrollbar.grid(row=1, column=1, sticky="ew")
                self.x_scrollbar_visible = True
        else:
            if not self.x_scrollbar_visible:  # Do not hide if already shown
                self.editor_xscrollbar.grid_remove()
                self.x_scrollbar_visible = False

        # Check vertical scrollbar
        if self.code_editor.yview()[0] > 0 or self.code_editor.yview()[1] < 1:
            if not self.y_scrollbar_visible:
                self.editor_yscrollbar.grid(row=0, column=2, sticky="ns")
                self.y_scrollbar_visible = True
        else:
            if self.y_scrollbar_visible:  # Do not hide if already shown
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
            
        self.lexeme_textbox.delete(1.0, tk.END)
        self.token_textbox.delete(1.0, tk.END)

        for index, token in enumerate(tokens):
            # Insert lexeme
            self.lexeme_textbox.insert("end", f"{token.lexeme}\n")
            # Insert token
            self.token_textbox.insert("end", f"{token.token}\n")
app = App()
app.mainloop()