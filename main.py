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

        # Text editor frame
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        self.editor_frame = ctk.CTkFrame(self.main_frame)
        self.editor_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # code editor
        self.code_editor = ctk.CTkTextbox(self.editor_frame, wrap="none", font=("Consolas", 15), undo=True, activate_scrollbars=False)
        self.code_editor.grid(row=0, column=1, sticky="nsew",pady=5, padx=(2,5))
        
        # Create the label inside the frame
        self.line_numbers = ctk.CTkTextbox(self.editor_frame, font=("Consolas", 15), width=40, wrap="none", text_color="#fdca01",activate_scrollbars=False)
        self.line_numbers.grid(row=0, column=0, sticky="ns",pady=5, padx=(5,0))
        #self.line_numbers.configure(state="disabled") 

        # horizontal scrollbar
        self.editor_xscrollbar = ctk.CTkScrollbar(self.editor_frame, orientation="horizontal")
        self.editor_xscrollbar.grid(row=1, column=1, sticky="ew")

        # vertical scrollbar
        self.editor_yscrollbar = ctk.CTkScrollbar(self.editor_frame,  orientation="vertical")
        self.editor_yscrollbar.grid(row=0, column=2, sticky="ns")

        self.editor_xscrollbar.configure(command=self.editor_x_scroll)
        self.editor_yscrollbar.configure(command=self.editor_y_scroll)

        self.code_editor.configure(xscrollcommand=self.update_horizontal_scrollbar)
        self.code_editor.configure(yscrollcommand=self.update_vertical_scrollbar)

        self.code_editor.bind("<KeyRelease>", self.handle_return)
        self.code_editor.bind("<Return>", self.handle_newline)
        self.code_editor.bind("<BackSpace>", self.handle_newline)
        self.code_editor.bind("<MouseWheel>", self.editor_y_scrollwheel)
        self.code_editor.bind("<Button-1>", self.sync_editor_linenumbers)
        self.code_editor.bind("<Key-{>", self.handle_braces)
        self.code_editor.bind("<Key-(>", self.handle_parentheses)
        self.code_editor.bind("<Key-[>", self.handle_brackets)
        self.code_editor.bind('<Key-">', self.handle_quotation)

        # lexeme, token, and error frame
        self.info_frame = ctk.CTkFrame(self)
        self.info_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        # frame for lexeme and token list
        self.list_frame = ctk.CTkFrame(self.info_frame)
        self.list_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=5)

        # vertical frames for lexeme and token list
        self.lexeme_frame = ctk.CTkFrame(self.list_frame)
        self.lexeme_frame.grid(row=0, column=0, padx=10, sticky="nsew")

        self.token_frame = ctk.CTkFrame(self.list_frame)
        self.token_frame.grid(row=0, column=1, padx=10, sticky="nsew")

        self.list_scrollbar = ctk.CTkScrollbar(self.list_frame, orientation="vertical")
        self.list_scrollbar.grid(row=0, column=2, sticky="ns")

        self.lexeme_label = ctk.CTkLabel(self.lexeme_frame, text="Lexemes", font=("Consolas", 15, "bold"))
        self.lexeme_label.grid(row=0, column=0, padx=10, pady=(0,5), sticky="n")
        self.lexeme_textbox = ctk.CTkTextbox(self.lexeme_frame, wrap="none", font=("Consolas", 15), width=200, height=300)
        self.lexeme_textbox.grid(row=1, column=0, padx=0, pady=0, sticky="nsew")

        self.token_label = ctk.CTkLabel(self.token_frame, text="Tokens", font=("Consolas", 15, "bold"))
        self.token_label.grid(row=0, column=0, padx=10, pady=(0,5), sticky="n")
        self.token_textbox = ctk.CTkTextbox(self.token_frame, font=("Consolas", 15), width=200, height=300, activate_scrollbars=False)
        self.token_textbox.grid(row=1, column=0, padx=0, pady=0, sticky="nsew")

        self.lexeme_textbox.configure(state="disabled")
        self.token_textbox.configure(state="disabled")
        
        self.list_scrollbar.configure(command=self.sync_scroll)
        # Update scrollbar visibility dynamically
        self.lexeme_textbox.configure(yscrollcommand=self.update_scrollbar)
        self.token_textbox.configure(yscrollcommand=self.update_scrollbar)
        
        self.error_label = ctk.CTkLabel(self.info_frame, text="Errors", font=("Consolas", 15, "bold"))
        self.error_label.grid(row=1, column=0, padx=10, pady=0, sticky="n")

        # error field (Text widget)
        self.error_field = ctk.CTkTextbox(self.info_frame, height=250, font=("Consolas", 15), width=350, text_color="#e69f35")
        self.error_field.grid(row=2, column=0, padx=15, pady=5, sticky="sew")
        self.error_field.configure(state="disabled")

        # tokenize button
        self.tokenize_button = ctk.CTkButton(self.info_frame, text="Tokenize", font=("Consolas", 15, "bold"), command=self.process_text)
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

        self.line_numbers.insert("1.0", "1")
        self.line_numbers.tag_config("right", justify="right")
        self.line_numbers.tag_add("right", "1.0", "end")

    def editor_y_scrollwheel(self, event):
        # Calculate scroll direction
        if event.num == 4 or event.delta > 0:  # Scroll up
            self.code_editor.yview_scroll(-1, "units")
            self.line_numbers.yview_scroll(-1, "units")
        elif event.num == 5 or event.delta < 0:  # Scroll down
            self.code_editor.yview_scroll(1, "units")
            self.line_numbers.yview_scroll(1, "units")
        return "break"

    def handle_parentheses(self, event):
        # Get the current cursor position
        cursor_index = self.code_editor.index("insert")
        
        # Insert the opening and closing parentheses
        self.code_editor.insert(cursor_index, "()")
        
        # Move the cursor inside the parentheses
        self.code_editor.mark_set("insert", f"{cursor_index} + 1c")
        
        # Prevent the default `(` character from being inserted
        return "break"

    # Function to handle brackets []
    def handle_brackets(self, event):
        # Get the current cursor position
        cursor_index = self.code_editor.index("insert")
        
        # Insert the opening and closing brackets
        self.code_editor.insert(cursor_index, "[]")
        
        # Move the cursor inside the brackets
        self.code_editor.mark_set("insert", f"{cursor_index} + 1c")
        
        # Prevent the default `[` character from being inserted
        return "break"
    
    def handle_quotation(self, event):
        # Get the current cursor position
        cursor_index = self.code_editor.index("insert")
        
        # Insert the opening and closing brackets
        self.code_editor.insert(cursor_index, '""')
        
        # Move the cursor inside the brackets
        self.code_editor.mark_set("insert", f"{cursor_index} + 1c")
        
        # Prevent the default `[` character from being inserted
        return "break"
    
    def is_inside_string(self, cursor_index):
        text_before_cursor = self.code_editor.get("1.0", cursor_index)
        # Count the number of unescaped double quotes before the cursor
        quotes_count = len(re.findall(r'(?<!\\)"', text_before_cursor))
        return quotes_count % 2 != 0

    def handle_braces(self, event):
        # Number of spaces for indentation (replace with '\t' if needed)
        indentation = "         "  # 4 spaces for a tab
        
        # Get the current cursor position
        cursor_index = self.code_editor.index("insert")

        if self.is_inside_string(cursor_index):
            return  # Exit the method without handling braces

        
        # Calculate the current indentation level
        line_start = f"{cursor_index.split('.')[0]}.0"
        current_line = self.code_editor.get(line_start, cursor_index)
        leading_spaces = len(current_line) - len(current_line.lstrip())
        current_indent = " " * leading_spaces

        # Insert the opening brace, newline, indentation, and closing brace
        self.code_editor.insert(cursor_index, "{\n" + current_indent + indentation + "\n" + current_indent + "}")
        
        # Move the cursor to the indented line
        new_cursor_index = f"{int(cursor_index.split('.')[0]) + 1}.0 + {leading_spaces + len(indentation)}c"
        self.code_editor.mark_set("insert", new_cursor_index)

        # Prevent the default `{` character from being inserted
        return "break"

    def sync_editor_linenumbers(self, event=None):
        self.line_numbers.yview_moveto(self.code_editor.yview()[1])

    def handle_newline(self,event=None):
        if event.keysym == "Return":
            self.count_add = 2
        elif event.keysym == "BackSpace":
            self.count_add = 0
        
        self.update_line_numbers()

    def handle_return(self, event=None):
        if event.keysym == "Return" or event.keysym == "BackSpace":
            return
        
        self.highlight_syntax()
    
    def highlight_syntax(self, event=None):
        self.line_numbers.yview_moveto(self.code_editor.yview()[1])
        
        text = self.code_editor.get("1.0", "end").strip()  # Get input text
        if not text:
            return

        self.code_editor.tag_remove("purple", "1.0", "end")
        self.code_editor.tag_remove("comment", "1.0", "end")
        self.code_editor.tag_remove("yellow", "1.0", "end")
        self.code_editor.tag_remove("symbols", "1.0", "end")
        
        for keyword in keywords:
            start_index = "1.0"
            while True:
                # Find the next occurrence of the keyword
                start_index = self.code_editor.search(keyword, start_index, stopindex="end")
                if not start_index:
                    break
                end_index = f"{start_index}+{len(keyword)}c"
                # Apply the tag to the keyword
                self.code_editor.tag_add("purple", start_index, end_index)
                start_index = end_index  # Move to the next character after the keyword

        start_index = "1.0"
        while True:
            # Search for the next occurrence of a number (using NUM)
            start_index = self.code_editor.search(r'\d+\.\d+|\d+', start_index, stopindex="end", regexp=True)
            
            if not start_index:
                break  # No more numbers to highlight

             # Get the matched number (the number string itself)
            matched_text = self.code_editor.get(start_index, f"{start_index}+{len(self.code_editor.get(start_index, start_index+'+1c'))}c")
            
            # Calculate end_index based on the length of the matched number
            end_index = f"{start_index}+{len(matched_text)}c"
            
            # Apply yellow color to the number
            self.code_editor.tag_add("yellow", start_index, end_index)
            start_index = end_index 
        
        for value in values:
            start_index = "1.0"
            while True:
                # Find the next occurrence of the keyword
                start_index = self.code_editor.search(value, start_index, stopindex="end")
                if not start_index:
                    break
                end_index = f"{start_index}+{len(value)}c"
                # Apply the tag to the keyword
                self.code_editor.tag_add("yellow", start_index, end_index)
                start_index = end_index  # Move to the next character after the keyword

        matches = re.finditer(r'"(?:[^"\\\n]|\\.)*"', text)  # Updated regex to stop at newlines
        for match in matches:
            start_index = f"1.0 + {match.start()} chars"
            end_index = f"1.0 + {match.end()} chars"
            self.code_editor.tag_add("yellow", start_index, end_index)

        start_index = "1.0"
        while True:
            # Search for any of the symbols
            match_start = self.code_editor.search(symbols, start_index, stopindex="end", regexp=True)
            if not match_start:  # No more matches
                break
            # Get the end index of the match
            match_end = f"{match_start}+1c"
            # Apply the 'symbols' tag to the match
            self.code_editor.tag_add("symbols", match_start, match_end)
            # Move the start index forward
            start_index = match_end

        start_index = "1.0"
        while True:
            start_index = self.code_editor.search("#", start_index, stopindex="end")
            if not start_index:
                break
            line_end = self.code_editor.index(f"{start_index} lineend")  # End of the line
            self.code_editor.tag_add("comment", start_index, line_end)
            start_index = line_end

        pattern = r"```(.*?)```"  # Matches text between triple backticks
        matches = re.finditer(pattern, text, re.DOTALL) 

        for match in matches:
            start_idx = match.start()
            end_idx = match.end()

            # Convert the match indices to tkinter text widget indices
            start_index = f"1.0 + {start_idx} chars"
            end_index = f"1.0 + {end_idx} chars"

            # Add the tag to highlight the block
            self.code_editor.tag_add("comment", start_index, end_index)
            
        self.code_editor.tag_config("purple", foreground="#f396d3")
        self.code_editor.tag_config("comment", foreground="#999999")
        self.code_editor.tag_config("yellow", foreground="#FFFF00")
        self.code_editor.tag_config("symbols", foreground="orange")

    def sync_scroll(self, *args):
        self.lexeme_textbox.yview(*args)
        self.token_textbox.yview(*args)

    def update_scrollbar(self, *args):
        # Always check if scrolling is needed based on the yview of both textboxes
        lexeme_scroll_needed = self.lexeme_textbox.yview()[0] > 0.0 or self.lexeme_textbox.yview()[1] < 1.0
        token_scroll_needed = self.token_textbox.yview()[0] > 0.0 or self.token_textbox.yview()[1] < 1.0

        # Show the scrollbar if either textbox needs scrolling
        if lexeme_scroll_needed or token_scroll_needed:
            self.list_scrollbar.grid()
        else:
            self.list_scrollbar.grid_remove()

        # Update the scrollbar position for both textboxes
        self.list_scrollbar.set(*args)

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

    # Settings function
    def change_theme(self):
        theme_value = self.theme.get()
        if theme_value == 1:
            ctk.set_appearance_mode("light") 
        elif theme_value == 2:
            ctk.set_appearance_mode("dark")
    
    # Textbox functions
    def update_line_numbers(self, event=None):
        
        # Count the number of lines in the code editor
        content = self.code_editor.get("1.0", "end-1c")  # Get all text excluding the final newline
        num_lines = content.count('\n') + self.count_add  # Count newlines and add 1 for the last line

        # Create a string of line numbers to display
        line_numbers_string = "\n".join(str(i) for i in range(1, num_lines + 1))

        # Update the line_numbers widget with the new line numbers
        self.line_numbers.delete("1.0", "end")  # Clear existing text
        self.line_numbers.insert("1.0", line_numbers_string)  # Insert the new line numbers

        # Align the text to the right
        self.line_numbers.tag_config("right", justify="right")
        self.line_numbers.tag_add("right", "1.0", "end")
        self.line_numbers.yview_moveto(self.code_editor.yview()[1])


    def editor_x_scroll(self, *args):
        self.code_editor.xview(*args)
    
    def editor_y_scroll(self, *args):
        self.code_editor.yview(*args)
        self.line_numbers.yview(*args)
        #self.update_line_numbers()

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
        
    # Tokenize button function
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
                for _ in range(newlines_count):  # Loop over the count of newlines
                    self.token_textbox.insert("end", "\n") 
              
        self.lexeme_textbox.configure(state="disabled")
        self.token_textbox.configure(state="disabled")

app = App()
app.mainloop()