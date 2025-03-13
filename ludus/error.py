class SemanticError(Exception):
    def __init__(self, message, pos_start=None, pos_end=None, source_code=None):
        self.message = message
        self.pos_start = pos_start
        self.pos_end = pos_end
        self.source_code = source_code  
        super().__init__(self.message)

    def __str__(self):
        if self.pos_start:
            return self.generate_error_message()
        else:
            return f"Semantic Error: {self.message}"

    def generate_error_message(self):
        if not self.source_code:
            return f"Semantic Error: {self.message}"
        line_num = self.pos_start[0]
        start_col = self.pos_start[1]
        end_col = self.pos_end[1]

        try:
            error_line = self.source_code[line_num - 1]
        except IndexError:
            return f"Semantic Error at unknown position: {self.message}"

        expanded_line = error_line.replace('\t', ' ' * 4)

        adjusted_start_col = len(expanded_line[:start_col].replace('\t', ' ' * 4))
        adjusted_end_col = len(expanded_line[:end_col].replace('\t', ' ' * 4))

        underline_length = max(adjusted_end_col - adjusted_start_col, 1)
        if start_col == end_col:
            underline = " " * (adjusted_start_col - 1) + "^" 
        else:
            underline = " " * (adjusted_start_col - 1) + "^" * (underline_length+1)

        return f"Semantic Error found on line {line_num}:\n\n{expanded_line}\n{underline}\n\n{self.message}"