import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
from linenums import textlinenum, customtext
import lexer

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("ludus.json")

# USES TERMINAL FRAME 

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Ludus")
        self.iconbitmap('ludus.ico')
        self.center_window()

        self.file_path = None
        self.is_saved = True
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # menu bar
        self.menu_bar = tk.Menu(self)
        self.config(menu=self.menu_bar)

        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)
        # self.settings_menu = tk.Menu(self.menu_bar, tearoff=0)
        # self.menu_bar.add_cascade(label="Settings", menu=self.settings_menu)

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
        # self.theme_menu = tk.Menu(self.menu_bar, tearoff=0)
        # self.theme = tk.IntVar(value=2)
        # self.theme_menu.add_radiobutton(label="Light Mode", value=1, variable=self.theme, command=self.change_theme)
        # self.theme_menu.add_radiobutton(label="Dark Mode", value=2, variable=self.theme, command=self.change_theme)
        # self.settings_menu.add_cascade(label="Theme", menu=self.theme_menu)

        # code editor and terminal frame
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=0)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # code editor
        self.editor_frame = ctk.CTkFrame(self.main_frame)
        self.editor_frame.grid(row=0, column=0, sticky="nsew")

        self.editor_xscrollbar = tk.Scrollbar(self.editor_frame, orient="horizontal", command=self.editor_x_scroll)
        self.editor_xscrollbar.pack(side="bottom", fill="x")

        self.editor_yscrollbar = tk.Scrollbar(self.editor_frame, orient="vertical", command=self.editor_y_scroll)
        self.editor_yscrollbar.pack(side="right", fill="y")

        self.line_numbers = tk.Label(self.editor_frame, width=4, padx=4, anchor="nw", background="gray12", foreground="#fdca01", font=("Consolas", 12))
        self.line_numbers.pack(side="left", fill="y")

        self.code_editor = tk.Text(self.editor_frame, wrap=tk.NONE, font=("Consolas", 12), undo=True)
        self.code_editor.pack(side="left", fill="both", expand=True)
        self.code_editor.config(xscrollcommand=self.editor_xscrollbar.set)
        self.code_editor.config(yscrollcommand=self.editor_yscrollbar.set)

        self.code_editor.bind("<KeyRelease>", self.update_line_numbers)
        self.code_editor.bind("<MouseWheel>", self.update_line_numbers)
        self.code_editor.bind("<Button-1>", self.update_line_numbers)
        self.code_editor.bind("<Configure>", self.update_line_numbers)
        self.code_editor.bind("<<Modified>>", self.mark_as_unsaved)

        # terminal
        self.terminal_frame = ctk.CTkFrame(self.main_frame, height=12)
        self.terminal_frame.grid(row=1, column=0, sticky="ew") 

        self.terminal_frame.grid_columnconfigure(0, weight=1)
        self.terminal_frame.grid_columnconfigure(1, weight=0)

        self.terminal_yscrollbar = tk.Scrollbar(self.terminal_frame, orient="vertical", command=self.terminal_y_scroll)
        self.terminal_yscrollbar.grid(row=1, column=2, sticky="ns")

        self.terminal_label = ctk.CTkLabel(self.terminal_frame, text="Terminal", anchor="w", fg_color="gray12", text_color="white", font=("Arial", 14, "bold"))
        self.terminal_label.grid(row=0, column=0, columnspan=2, sticky="ew")

        self.terminal = tk.Text(self.terminal_frame, wrap="word", bg="gray12", fg="white", font=("Consolas", 12),height=12, yscrollcommand=self.terminal_yscrollbar.set)
        self.terminal.grid(row=1, column=0, sticky="nsew")

        # tokenize button
        self.tokenize_button = ctk.CTkButton(self.terminal_frame, text="Tokenize", font=("Arial", 13, "bold"), command=self.process_text)
        self.tokenize_button.grid(row=1, column=1, padx=5, pady=5, sticky="n")

        # tokenize button
        self.tokenize_button = ctk.CTkButton(self.terminal_frame, text="Tokenize", font=("Arial", 13, "bold"), command=self.process_text)
        self.tokenize_button.grid(row=1, column=1, padx=5, pady=5, sticky="n")

        # lexeme, token, and error frame
        self.info_frame = ctk.CTkFrame(self)
        self.info_frame.pack(side="right", fill="both", padx=10, pady=10, expand=False)

        self.info_label = ctk.CTkLabel(self.info_frame, text="Lexeme Table", font=("Arial", 14, "bold"))
        self.info_label.pack(side="top", fill="both") 

        # frame for lexeme and token list
        self.list_frame = ctk.CTkFrame(self.info_frame)
        self.list_frame.pack(side="top", fill="both", expand=True) 

        # vertical frames for lexeme and token list
        self.lexeme_frame = ctk.CTkFrame(self.list_frame)
        self.lexeme_frame.pack(side="left", padx=5, fill="both", expand=True)

        self.token_frame = ctk.CTkFrame(self.list_frame)
        self.token_frame.pack(side="left", padx=5, fill="both", expand=True)

        self.list_scrollbar = tk.Scrollbar(self.list_frame, orient="vertical")
        self.list_scrollbar.pack(side="right", fill="y")

        self.lexeme_label = ctk.CTkLabel(self.lexeme_frame, text="Lexemes", font=("Arial", 14, "bold"))
        self.lexeme_label.pack(side="top", padx=10)
        self.lexeme_listbox = tk.Listbox(self.lexeme_frame, font=("Arial", 10), width=25, yscrollcommand=self.list_scrollbar.set)
        self.lexeme_listbox.pack(side="top", padx=5, pady=10, fill="both", expand=True)

        self.token_label = ctk.CTkLabel(self.token_frame, text="Tokens", font=("Arial", 14, "bold"))
        self.token_label.pack(side="top", padx=10)
        self.token_listbox = tk.Listbox(self.token_frame, font=("Arial", 10), width=25, yscrollcommand=self.list_scrollbar.set)
        self.token_listbox.pack(side="top", padx=5, pady=10, fill="both", expand=True)
        
        self.lexeme_listbox.bind("<MouseWheel>", self.sync_scroll)
        self.token_listbox.bind("<MouseWheel>", self.sync_scroll)
        self.list_scrollbar.config(command=lambda *args: [self.lexeme_listbox.yview(*args), self.token_listbox.yview(*args)])

    
    # General
    def center_window(self):
        self.update_idletasks()  
        self.screen_width = self.winfo_screenwidth()
        self.screen_height = self.winfo_screenheight()
        self.app_width = 1300
        self.app_height = 700
        self.x_width = (self.screen_width // 2) - (self.app_width // 2)
        self.y_height = (self.screen_height // 2) - (self.app_height // 2)
        self.geometry(f"{self.app_width}x{self.app_height}+{self.x_width}+{self.y_height}")

    # File handling methods
    def open_file(self):
        self.file_path = filedialog.askopenfilename(filetypes=[("Ludus Files", "*.lds")])
        if self.file_path:
            with open(self.file_path, 'r') as file:
                content = file.read()
                self.lexeme_listbox.delete(0, tk.END)
                self.token_listbox.delete(0, tk.END)
                self.terminal.config(state=tk.NORMAL) 
                self.terminal.delete(1.0, tk.END)      
                self.terminal.config(state=tk.DISABLED)
                self.code_editor.delete(1.0, tk.END)
                self.code_editor.delete(1.0, tk.END)
                self.code_editor.insert(tk.END, content)
        elif not self.check_unsaved_changes():
            return
                
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
        if not self.check_unsaved_changes():
            return
        self.lexeme_listbox.delete(0, tk.END)
        self.token_listbox.delete(0, tk.END)
        self.terminal.config(state=tk.NORMAL) 
        self.terminal.delete(1.0, tk.END)      
        self.terminal.config(state=tk.DISABLED)
        self.code_editor.delete(1.0, tk.END)
        self.file_path = None

    def exit_app(self): 
        self.quit()
        if not self.check_unsaved_changes():
            return
    
    def check_unsaved_changes(self):
        # TODO: ayusin pa 
        # (1) gumagana lang kapag KeyRelease, 
        # (2) if walang change/inopen lang, di dapat lalabas, 
        # (3) magulo pa application sa ibang file functions
        if not self.is_saved:
            response = messagebox.askyesnocancel(
                "Unsaved Changes",
                "You have unsaved changes. Do you want to save before proceeding?",
            )
            if response:  
                self.save_file()
                return True  
            elif response is None:  
                return False  
        return True

    def mark_as_unsaved(self, event=None):
        self.is_saved = False

    # Settings function
    # def change_theme(self):
    #     theme_value = self.theme.get()
    #     if theme_value == 1:
    #         ctk.set_appearance_mode("light") 
    #     elif theme_value == 2:
    #         ctk.set_appearance_mode("dark")
    
    # Code editor and terminal functions
    def update_line_numbers(self, event=None):
        first_visible_line = int(self.code_editor.index("@0,0").split(".")[0])
        last_visible_line = int(self.code_editor.index("@0,%d" % self.code_editor.winfo_height()).split(".")[0])
        line_numbers_string = "\n".join(str(i) for i in range(first_visible_line, last_visible_line + 1))
        self.line_numbers.config(text=line_numbers_string)

        cursor_position = self.code_editor.index("insert")
        self.code_editor.see(cursor_position)

    def editor_x_scroll(self, *args):
        self.code_editor.xview(*args)
    
    def editor_y_scroll(self, *args):
        self.code_editor.yview(*args)
        self.update_line_numbers()

    def terminal_y_scroll(self, *args):
        self.terminal.yview(*args)

    # Listboxes function
    def sync_scroll(self, event): 
        delta = int(-1 * (event.delta / 120))  
        self.lexeme_listbox.yview_scroll(delta, "units")
        self.token_listbox.yview_scroll(delta, "units")
        return "break"

    # Tokenize button function
    def process_text(self):
        input_text = self.code_editor.get("0.0", tk.END).strip()  
        tokens, error = lexer.run(self.file_path, input_text)

        self.terminal.config(state=tk.NORMAL) 
        self.terminal.delete(1.0, tk.END)      
        self.terminal.config(state=tk.DISABLED)

        if error:  
            self.terminal.config(state=tk.NORMAL)
            for errors in error:
                self.terminal.insert(tk.END, errors + '\n')  
            self.terminal.config(state=tk.DISABLED)
            
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