# get parse_table from cfg.py
# push the start_symbol into a stack
# read the ip buffer
# check parse table, pop start, push production from parse table (reverse order)
# whenever ip buffer is matched to the top of the stack, pop the symbol
# ty neso academy

from cfg import parse_table

def parser(parse_table, start_symbol, input_buffer):
    stack = [start_symbol]  
    input_buffer.append("$")  
    pointer = 0  

    while stack:
        top = stack.pop()
        current_input = input_buffer[pointer]

        print(top)
        print(current_input)

        if top == current_input:
            print(f"Matched: {top}")
            pointer += 1
        elif top in parse_table:
            if current_input in parse_table[top]:
                production = parse_table[top][current_input]
                print(f"Expand: {top} → {' '.join(production)}")
                if "λ" not in production:
                    stack.extend(reversed(production))
                print(stack)
            else:
                raise SyntaxError(f"Unexpected token '{current_input}' at {pointer}")
        else:
            raise SyntaxError(f"Unexpected token '{current_input}' at {pointer}")

    if pointer == len(input_buffer) - 1:
        print("slmt neso academy!")
    else:
        raise SyntaxError("Input not fully consumed.")
    
input_buffer = ["a", "d", "b"]
parser(parse_table, "<S>", input_buffer)


