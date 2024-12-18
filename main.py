import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import lexer
import re

# TODO: REFACTOR CODE 

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("ludus.json")

keywords = [
    "gameOver", "build", "access", "AND", "OR", "immo", "if", "elif", "else", "flank",
    "choice", "backup", "for", "while", "grind", "checkpoint", "resume", "recall",
    "generate", "play", "shoot", "shootNxt", "load", "loadNum", "rounds", "wipe",
    "join", "drop", "seek", "levelUp", "levelDown", "toHp", "toXp", "toComms", "hp", "xp", "comms",
    "flag"
]

NUM = '0123456789'
values = [
    "true", "false", "dead"
]
symbols = r"[\(\)\[\]\{\}\!\%\^\*\-\+\=\|:,.<>\/]"

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Ludus")
        self.iconbitmap('ludus.ico')
        self.geometry("1300x800")

        self.file_path = None
        self.count_add = 0
        
        # menu bar
        self.menu_bar = tk.Menu(self, background="#333", foreground="black")
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

        # code editor frame
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        self.editor_frame = ctk.CTkFrame(self.main_frame)
        self.editor_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # code editor
        self.code_editor = ctk.CTkTextbox(self.editor_frame, wrap="none", font=("Consolas", 15), undo=True, activate_scrollbars=False)
        self.code_editor.grid(row=0, column=1, sticky="nsew",pady=5, padx=(2,5))
        
        # line numbers
        self.line_numbers = ctk.CTkTextbox(self.editor_frame, font=("Consolas", 15), width=40, wrap="none", text_color="#fdca01",activate_scrollbars=False)
        self.line_numbers.grid(row=0, column=0, sticky="ns",pady=5, padx=(5,0))
        self.line_numbers.configure(state="disabled") 

        # horizontal scrollbar
        self.editor_xscrollbar = ctk.CTkScrollbar(self.editor_frame, orientation="horizontal")
        self.editor_xscrollbar.grid(row=1, column=1, sticky="ew")

        # vertical scrollbar
        self.editor_yscrollbar = ctk.CTkScrollbar(self.editor_frame,  orientation="vertical")
        self.editor_yscrollbar.grid(row=0, column=2, sticky="ns")

        #scrollbar commands
        self.editor_xscrollbar.configure(command=self.editor_x_scroll)
        self.editor_yscrollbar.configure(command=self.editor_y_scroll)

        # link scrollbar to code_editor
        self.code_editor.configure(xscrollcommand=self.update_horizontal_scrollbar)
        self.code_editor.configure(yscrollcommand=self.update_vertical_scrollbar)

        # code editor bindings
        self.code_editor.bind("<KeyRelease>", self.handle_return)
        self.code_editor.bind("<Return>", self.handle_newline)
        self.code_editor.bind("<MouseWheel>", self.editor_y_scrollwheel)
        self.code_editor.bind("<Button-1>", self.sync_editor_linenumbers)
        self.code_editor.bind("<Key-{>", self.handle_braces)
        self.code_editor.bind("<Key-(>", self.handle_parentheses)
        self.code_editor.bind("<Key-[>", self.handle_brackets)
        self.code_editor.bind('<Key-">', self.handle_quotation)

        #############################################################

        # lexeme, token, and error frame
        self.info_frame = ctk.CTkFrame(self)
        self.info_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        # frame for lexeme and token textbox
        self.list_frame = ctk.CTkFrame(self.info_frame)
        self.list_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=5)

        # vertical frames for lexeme and token textbox
        self.lexeme_frame = ctk.CTkFrame(self.list_frame)
        self.lexeme_frame.grid(row=0, column=0, padx=10, sticky="nsew")

        self.token_frame = ctk.CTkFrame(self.list_frame)
        self.token_frame.grid(row=0, column=1, padx=10, sticky="nsew")

        # lexeme and token list scrollbar
        self.list_scrollbar = ctk.CTkScrollbar(self.list_frame, orientation="vertical")
        self.list_scrollbar.grid(row=0, column=2, sticky="ns")

        # lexeme and token label and textbox
        self.lexeme_label = ctk.CTkLabel(self.lexeme_frame, text="Lexemes", font=("Consolas", 15, "bold"))
        self.lexeme_label.grid(row=0, column=0, padx=10, pady=(0,5), sticky="n")
        self.lexeme_textbox = ctk.CTkTextbox(self.lexeme_frame, wrap="none", font=("Consolas", 15), width=200, height=300, )
        self.lexeme_textbox.grid(row=1, column=0, padx=0, pady=0, sticky="nsew")

        self.token_label = ctk.CTkLabel(self.token_frame, text="Tokens", font=("Consolas", 15, "bold"))
        self.token_label.grid(row=0, column=0, padx=10, pady=(0,5), sticky="n")
        self.token_textbox = ctk.CTkTextbox(self.token_frame, font=("Consolas", 15), width=200, height=300)
        self.token_textbox.grid(row=1, column=0, padx=0, pady=0, sticky="nsew")

        self.lexeme_textbox.configure(state="disabled")
        self.token_textbox.configure(state="disabled")
        
        # lexeme & token list configuration
        self.list_scrollbar.configure(command=self.sync_scroll)
        self.lexeme_textbox.configure(yscrollcommand=self.update_scrollbar)
        self.token_textbox.configure(yscrollcommand=self.update_scrollbar)
        
        # error field label and text box
        self.error_label = ctk.CTkLabel(self.info_frame, text="Errors", font=("Consolas", 15, "bold"))
        self.error_label.grid(row=1, column=0, padx=10, pady=0, sticky="n")

        self.error_field = ctk.CTkTextbox(self.info_frame, height=250, font=("Consolas", 15), width=350, text_color="#e69f35")
        self.error_field.grid(row=2, column=0, padx=15, pady=5, sticky="sew")
        self.error_field.configure(state="disabled")

        # tokenize button
        self.tokenize_button = ctk.CTkButton(self.info_frame, text="Tokenize", font=("Consolas", 15, "bold"), command=self.process_text)
        self.tokenize_button.grid(row=3, column=0, padx=50, pady=5, sticky="n")

        #############################################################

        # root window grid weights
        self.grid_rowconfigure(0, weight=1)  
        self.grid_columnconfigure(0, weight=3)  #code editor
        self.grid_columnconfigure(1, weight=0)  #info frame

        # main frame
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # code editor frame
        self.editor_frame.grid_rowconfigure(0, weight=1)  
        self.editor_frame.grid_columnconfigure(1, weight=1)  
        self.editor_frame.grid_columnconfigure(0, weight=0)

        # info frame
        self.info_frame.grid_rowconfigure(0, weight=3)
        self.info_frame.grid_columnconfigure(0, weight=0)

        self.info_frame.grid_rowconfigure(1, weight=0)  # button
        self.info_frame.grid_rowconfigure(2, weight=0)  # error label
        self.info_frame.grid_rowconfigure(3, weight=1)  # error field 

        # lexeme and token list
        self.list_frame.grid_rowconfigure(0, weight=1)  # Allow the lexeme and token list frames to expand
        self.list_frame.grid_columnconfigure(0, weight=0)

        self.lexeme_frame.grid_rowconfigure(1, weight=1)
        self.token_frame.grid_rowconfigure(1, weight=1)

        # line numbers styling
        self.line_numbers.insert("1.0", "1")
        self.line_numbers.tag_config("right", justify="right")
        self.line_numbers.tag_add("right", "1.0", "end")

    ####################### file handling functions ################################
    
    def open_file(self): # TODO: warningan yung user na i-save muna ang file bago mag-open ng bago kung hindi pa nasasave
        self.file_path = filedialog.askopenfilename(filetypes=[("Ludus Files", "*.lds")])
        if self.file_path:
            with open(self.file_path, 'r') as file:
                content = file.read()
                self.lexeme_textbox.configure(state="normal")
                self.token_textbox.configure(state="normal")

                self.lexeme_textbox.delete("0.0", "end")
                self.token_textbox.delete("0.0", "end")

                self.error_field.configure(state="normal") 
                self.error_field.delete("0.0", "end")      
                self.error_field.configure(state="disabled")

                self.code_editor.delete("0.0", "end")
                self.code_editor.insert("end", content)
                self.update_line_numbers()
                self.highlight_syntax()
                
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

    
    def change_theme(self):
        theme_value = self.theme.get()
        if theme_value == 1:
            ctk.set_appearance_mode("light") 
        elif theme_value == 2:
            ctk.set_appearance_mode("dark")

    # code editor scrollbar functions

    def update_line_numbers(self, event=None):
        content = self.code_editor.get("1.0", "end-1c")  
        num_lines = content.count('\n') + self.count_add  

        line_numbers_string = "\n".join(str(i) for i in range(1, num_lines + 1))

        self.line_numbers.configure(state="normal") 
        self.line_numbers.delete("1.0", "end")  
        self.line_numbers.insert("1.0", line_numbers_string)  
        self.line_numbers.configure(state="disabled") 

        self.line_numbers.tag_config("right", justify="right")
        self.line_numbers.tag_add("right", "1.0", "end")
        self.line_numbers.yview_moveto(self.code_editor.yview()[1])

    def editor_x_scroll(self, *args):
        self.code_editor.xview(*args)
    
    def editor_y_scroll(self, *args):
        self.code_editor.yview(*args)
        self.line_numbers.yview(*args)

    def update_horizontal_scrollbar(self, *args):
        editor_scroll_needed = self.code_editor.xview()[0] > 0.0 or self.code_editor.xview()[1] < 1.0
        linenumbers_scroll_needed = self.line_numbers.xview()[0] > 0.0 or self.line_numbers.xview()[1] < 1.0
        
        if editor_scroll_needed or linenumbers_scroll_needed:
            self.editor_xscrollbar.grid()
        else:
            self.editor_xscrollbar.grid_remove()
        
        self.editor_xscrollbar.set(*args)

    def update_vertical_scrollbar(self, *args):
        editor_scroll_needed = self.code_editor.yview()[0] > 0.0 or self.code_editor.yview()[1] < 1.0
        linenumbers_scroll_needed = self.line_numbers.yview()[0] > 0.0 or self.line_numbers.yview()[1] < 1.0
        
        if editor_scroll_needed or linenumbers_scroll_needed:
            self.editor_yscrollbar.grid()
        else:
            self.editor_yscrollbar.grid_remove()
        
        self.editor_yscrollbar.set(*args)

    # code editor functions
    
    def editor_y_scrollwheel(self, event):
        if event.num == 4 or event.delta > 0:  
            self.code_editor.yview_scroll(-1, "units")
            self.line_numbers.yview_scroll(-1, "units")
        elif event.num == 5 or event.delta < 0:  #
            self.code_editor.yview_scroll(1, "units")
            self.line_numbers.yview_scroll(1, "units")
        return "break"

    def handle_parentheses(self, event):
        cursor_index = self.code_editor.index("insert")
        self.code_editor.insert(cursor_index, "()")
        self.code_editor.mark_set("insert", f"{cursor_index} + 1c")
        return "break"

    def handle_brackets(self, event):
        cursor_index = self.code_editor.index("insert")
        self.code_editor.insert(cursor_index, "[]")
        self.code_editor.mark_set("insert", f"{cursor_index} + 1c")
        return "break"
    
    def handle_quotation(self, event):
        cursor_index = self.code_editor.index("insert")
        self.code_editor.insert(cursor_index, '""')
        self.code_editor.mark_set("insert", f"{cursor_index} + 1c")
        return "break"
    
    def is_inside_string(self, cursor_index):
        text_before_cursor = self.code_editor.get("1.0", cursor_index)
        quotes_count = len(re.findall(r'(?<!\\)"', text_before_cursor))
        return quotes_count % 2 != 0

    def handle_braces(self, event):
        indentation = "         "  # tab simulation
        
        cursor_index = self.code_editor.index("insert")

        if self.is_inside_string(cursor_index):
            return  

        line_start = f"{cursor_index.split('.')[0]}.0"
        current_line = self.code_editor.get(line_start, cursor_index)
        leading_spaces = len(current_line) - len(current_line.lstrip())
        current_indent = " " * leading_spaces

        self.code_editor.insert(cursor_index, "{\n" + current_indent + indentation + "\n" + current_indent + "}")
        
        new_cursor_index = f"{int(cursor_index.split('.')[0]) + 1}.0 + {leading_spaces + len(indentation)}c"
        self.code_editor.mark_set("insert", new_cursor_index)

        return "break"

    def sync_editor_linenumbers(self, event=None):
        self.line_numbers.yview_moveto(self.code_editor.yview()[1])

    def handle_newline(self,event=None):
        if event.keysym == "Return":
            self.count_add = 2
        
        self.update_line_numbers()

    def handle_return(self, event=None):
        if event.keysym == "Return":
            return
        
        self.highlight_syntax()
    
    def highlight_syntax(self, event=None):
        self.count_add = 1
        self.update_line_numbers()
        
        text = self.code_editor.get("1.0", "end").strip()  
        if not text:
            return

        self.code_editor.tag_remove("purple", "1.0", "end")
        self.code_editor.tag_remove("comment", "1.0", "end")
        self.code_editor.tag_remove("yellow", "1.0", "end")
        self.code_editor.tag_remove("symbols", "1.0", "end")
        
        for keyword in keywords:
            start_index = "1.0"
            while True:
                start_index = self.code_editor.search(keyword, start_index, stopindex="end")
                if not start_index:
                    break
                end_index = f"{start_index}+{len(keyword)}c"
                self.code_editor.tag_add("purple", start_index, end_index)
                start_index = end_index  

        start_index = "1.0"
        while True:
            start_index = self.code_editor.search(r'\d+\.\d+|\d+', start_index, stopindex="end", regexp=True)
            
            if not start_index:
                break  

            matched_text = self.code_editor.get(start_index, f"{start_index}+{len(self.code_editor.get(start_index, start_index+'+1c'))}c")
            
            end_index = f"{start_index}+{len(matched_text)}c"
            
            self.code_editor.tag_add("yellow", start_index, end_index)
            start_index = end_index 
        
        for value in values:
            start_index = "1.0"
            while True:
                start_index = self.code_editor.search(value, start_index, stopindex="end")
                if not start_index:
                    break
                end_index = f"{start_index}+{len(value)}c"
                self.code_editor.tag_add("yellow", start_index, end_index)
                start_index = end_index  

        matches = re.finditer(r'"(?:[^"\\\n]|\\.)*"', text)  
        for match in matches:
            start_index = f"1.0 + {match.start()} chars"
            end_index = f"1.0 + {match.end()} chars"
            self.code_editor.tag_add("yellow", start_index, end_index)

        start_index = "1.0"
        while True:
            match_start = self.code_editor.search(symbols, start_index, stopindex="end", regexp=True)
            if not match_start: 
                break
            
            match_end = f"{match_start}+1c"
            self.code_editor.tag_add("symbols", match_start, match_end)
            start_index = match_end

        start_index = "1.0"
        while True:
            start_index = self.code_editor.search("#", start_index, stopindex="end")
            if not start_index:
                break
            line_end = self.code_editor.index(f"{start_index} lineend")  
            self.code_editor.tag_add("comment", start_index, line_end)
            start_index = line_end

        pattern = r"```(.*?)```"  
        matches = re.finditer(pattern, text, re.DOTALL) 

        for match in matches:
            start_idx = match.start()
            end_idx = match.end()

            start_index = f"1.0 + {start_idx} chars"
            end_index = f"1.0 + {end_idx} chars"

            self.code_editor.tag_add("comment", start_index, end_index)
            
        self.code_editor.tag_config("purple", foreground="#f396d3")
        self.code_editor.tag_config("comment", foreground="#999999")
        self.code_editor.tag_config("yellow", foreground="#FFFF00")
        self.code_editor.tag_config("symbols", foreground="orange")
    
    # lexeme and token scrollbar

    def sync_scroll(self, *args):
        self.lexeme_textbox.yview(*args)
        self.token_textbox.yview(*args)

    def update_scrollbar(self, *args):
        lexeme_scroll_needed = self.lexeme_textbox.yview()[0] > 0.0 or self.lexeme_textbox.yview()[1] < 1.0
        token_scroll_needed = self.token_textbox.yview()[0] > 0.0 or self.token_textbox.yview()[1] < 1.0

        if lexeme_scroll_needed or token_scroll_needed:
            self.list_scrollbar.grid()
        else:
            self.list_scrollbar.grid_remove()

        self.list_scrollbar.set(*args)
      
    # tokenize button function
    def process_text(self):
        input_text = self.code_editor.get("0.0", "end").strip()  
        tokens, error = lexer.run(self.file_path, input_text)

        self.error_field.configure(state="normal") 
        self.error_field.delete("0.0", "end")      
        self.error_field.configure(state="disabled")

        if error:  
            self.error_field.configure(state="normal")
            for errors in error:
                self.error_field.insert("end", errors + '\n')  
            self.error_field.configure(state="disabled")
                
        self.lexeme_textbox.configure(state="normal")
        self.token_textbox.configure(state="normal")
        
        self.lexeme_textbox.delete("0.0", "end")
        self.token_textbox.delete("0.0", "end")

        for index, token in enumerate(tokens):
            lexeme = token.lexeme
            newlines_count = lexeme.count('\n')

            self.token_textbox.insert("end", f"{token.token}\n")
            self.lexeme_textbox.insert("end", f"{lexeme}\n")

            if newlines_count > 0:
                for _ in range(newlines_count):  
                    self.token_textbox.insert("end", "\n") 

        lexeme_text = self.lexeme_textbox.get("1.0", "end-1c")  
        token_text = self.token_textbox.get("1.0", "end-1c")  

        lexeme_matches = re.finditer(r'^[^:]*:', lexeme_text, re.MULTILINE)
        for match in lexeme_matches:
            start_index = self.index_to_tk(match.start(), lexeme_text)
            end_index = self.index_to_tk(match.end(), lexeme_text)
            self.lexeme_textbox.tag_add("highlight", start_index, end_index)

        token_matches = re.finditer(r'^[^:]*:', token_text, re.MULTILINE)
        for match in token_matches:
            start_index = self.index_to_tk(match.start(), token_text)
            end_index = self.index_to_tk(match.end(), token_text)
            self.token_textbox.tag_add("highlight", start_index, end_index)
                
        self.lexeme_textbox.tag_config("highlight", foreground="#fdca01")
        self.token_textbox.tag_config("highlight", foreground="#fdca01")

        self.lexeme_textbox.configure(state="disabled")
        self.token_textbox.configure(state="disabled")

    def index_to_tk(self, abs_index, text):
        line = text.count('\n', 0, abs_index) + 1
        column = abs_index - text.rfind('\n', 0, abs_index) - 1
        return f"{line}.{column}"
app = App()
app.mainloop()