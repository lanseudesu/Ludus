def compute_first_set(cfg):
    first_set = {non_terminal: set() for non_terminal in cfg.keys()}

    def first_of(symbol):
        if symbol not in cfg:
            return {symbol} 

        if symbol in first_set and first_set[symbol]:
            return first_set[symbol]

        result = set()
        
        for production in cfg[symbol]:
            for sub_symbol in production:
                if sub_symbol not in cfg: # terminal
                    result.add(sub_symbol)
                    break  
                else: # non-terminal
                    sub_first = first_of(sub_symbol)
                    result.update(sub_first - {"λ"})  
                    if "λ" not in sub_first:
                        break  
            
            else: # all symbols in the production derive λ
                result.add("λ")

        first_set[symbol] = result
        return result

    for non_terminal in cfg:
        first_of(non_terminal)

    return first_set


def compute_follow_set(cfg, start_symbol, first_set):
    follow_set = {non_terminal: set() for non_terminal in cfg.keys()}
    follow_set[start_symbol].add("$")  

    def follow_of(symbol):
        if follow_set[symbol]:
            return follow_set[symbol]

        result = follow_set[symbol]  
        
        for non_terminal, productions in cfg.items():
            for production in productions:
                for i, item in enumerate(production):
                    if item == symbol:  # find occurrences of the symbol
                        if i + 1 < len(production):  
                            beta = production[i + 1]
                            if beta in first_set:  # beta is non-terminal
                                result.update(first_set[beta] - {"λ"})
                            else:  # beta is terminal
                                result.add(beta)

                        if i + 1 == len(production) or (beta in first_set and "λ" in first_set[beta]):
                            result.update(follow_of(beta)) # add follow set of lhs to symbol's fs
        
        follow_set[symbol] = result  
        return result

    for non_terminal in cfg.keys():
        follow_of(non_terminal)

    return follow_set

def compute_predict_set(cfg, first_set, follow_set):
    predict_set = {}  

    for non_terminal, productions in cfg.items():
        for production in productions:
            production_key = (non_terminal, tuple(production))  # A = (A,(prod))
            predict_set[production_key] = set()

            first_alpha = set()
            for symbol in production:
                if symbol in first_set:  # non-terminal
                    first_alpha.update(first_set[symbol] - {"λ"})
                    if "λ" not in first_set[symbol]:
                        break
                else:  # terminal
                    first_alpha.add(symbol)
                    break
            else:  
                first_alpha.add("λ")

            predict_set[production_key].update(first_alpha - {"λ"})

            # if λ in first_alpha, add follow set of lhs to predict set
            if "λ" in first_alpha:
                predict_set[production_key].update(follow_set[non_terminal])

    return predict_set

cfg = {
    # "<program>": [["<stmt_list>"]],
    # "<stmt_list>": [["<stmt>", "<stmt_list>"], ["<stmt>"]],
    # "<stmt>": [["print", "<expr>"], ["if", "<expr>", "<stmt>", "else", "<stmt>"]],
    # "<expr>": [["<term>", "<expr_prime>"]],
    # "<expr_prime>": [["+", "<term>", "<expr_prime>"], ["λ"]],
    # "<term>": [["<factor>", "<term_prime>"]],
    # "<term_prime>": [["*", "<factor>", "<term_prime>"], ["λ"]],
    # "<factor>": [["(", "<expr>", ")"], ["id"]],

    # tal 1-62
    "<program>": [["<global_dec>", "<fs_dec>", "play", "(", ")", "{", "<body>", "}", "<fs_body>", "gameOver"]],
    "<global_dec>": [["immo", "id", "<global_dec_tail1>", "<global_dec>"],
                     ["id", "<global_dec_tail2>", "<global_dec>"],
                     ["<datatype>", "id", "<global_dec_tail3>", "<global_dec>"],
                     ["λ"]], 
    "<global_dec_tail1>": [["[", "hp_ltr", "]", "<arr_tail1"],
                           ["<const_tail>"]],
    "<global_dec_tail2>": [["<const_tail>"],
                           ["[", "<arr_size>", "]", "<arr_tail2>"]],
    "<global_dec_tail3>": [["<id_recur>", "<dead_dec>"],
                           ["[", "<arr_size>", "]", "<arr_tail3>"]],
    "<arr_tail1>": [[":", "<value>", ",", "<value>", "<elems_recur>"],
                    ["[", "hp_ltr", "]", ":", "[", "<value>", ",", "<value>", ",", "<elems_recur>", "]", ",", "[", "<value>", ",", "<value>", ",", "<elems_recur>", "]", "<row_recur2>"]],
    "<arr_tail2>": [[":", "<value>", "<elems_recur>"],
                    ["[", "<arr_size>", "]", ":", "[", "<value>", ",", "<elems_recur>", "]", "<row_recur>"]],
    "<arr_tail3>": [["<dead_dec>"],
                    ["[", "<arr_size>", "]", "<dead_dec>"]],
    "<const_tail>": [[",", "id", "<id_recur>", ":", "<value>"],
                     [":", "<value>", "<val_recur>"]],
    "<arr_size>": [["hp_ltr"], 
                   ["λ"]], 
    "<id_recur>": [[",", "id", "<id_recur>"],
                   ["λ"]], 
    "<val_recur>": [[",", "id", ":", "<value>", "<val_recur>"],
                    ["λ"]], 
    "<dead_dec>": [[":", "dead"], 
                   ["λ"]],
    "<datatype>": [["hp"],
                    ["xp"],
                    ["comms"],
                    ["flag"]], 
    "<value>": [["<numeric_ltr>"],
                ["comms_ltr"], 
                ["flag_ltr"]], 
    "<numeric_ltr>": [["hp_ltr"],
                      ["xp_ltr"],
                      ["nhp_ltr"],
                      ["nxp_ltr"]],
    "<elems_recur>": [[",", "<value>", "<elems_recur>"],
                      ["λ"]],
    "<row_recur>": [[",", "[", "value", ",", "<elems_recur>"],
                    ["λ"]], 
    "<row_recur2>": [[",", "[", "value", ",", "value", ",", "<elems_recur>", "]", "<row_recur2>"],
                     ["λ"]],
    "<fs_dec>": [["<func_dec>"],
                 ["λ"]],
    "<func_dec>": [["generate", "id", "(", "<params>", ")", "<func_dec>"],
                   ["<struct_dec>"]],
    "<struct_dec>": [["build", "id", "<struct_dec>"],
                     ["λ"]],
    "<params>": [["id", "<def_or_recur>"],
                 ["λ"]],
    "<def_or_recur>": [[",", "id", "<def_or_recur>"],
                       [":", "<value>", "<defparam_recur>"],
                       ["λ"]],
    "<defparam>": [["id", ":", "<value>", "<defparam_recur>"]],
    "<defparam_recur>": [[",", "<defparam>"],
                         ["λ"]],
    "<common_stmts>": [["<local_dec>"],
                       ["<builtin_no_ret>"],
                       ["local_struct>"],
                       ["<struct_inst>"]],
    
    # khar 123-180
    "<factor>": [["id", "<id_rhs_tail>"], ["<value>"], ["-", "<negative>"],
                 ["<builtin_w_ret>"], ["!", "<not_tail>"], ["(", "<expr>", ")"]],
    "<id_rhs_tail>": [["(", "<args>", ")"], [".", "<rhs_dot_tail>"], 
                     ["[", "<index>", "]", "<rhs_bracket_tail>"], ["λ"]],
    "<args>": [["<valid_args>", "<args_recur>"], ["λ"]],
    "<valid_args>": [["id", "<id_rhs_tail>"], ["<value>"]],
    "<args_recur>": [[",", "<valid_args>", "<args_recur>"], ["λ"]],
    "<rhs_dot_tail>": [["id"], ["seek", "(", "<seek_tail>", ")"], ["drop", "(", "<index>", ")"]],
    "<rhs_bracket_tail>": [["[", "<index>", "]"], [".", "<rhs_inner_bracket_tail>"], ["λ"]],
    "<rhs_inner_bracket_tail>": [["drop", "(", "<index>", ")"], ["seek", "(", "<append>", ")"]],
    "<seek_tail>": [["<append>"], ["[", "<append>", "<append_recur>", "]"]],
    "<assign_op>": [["+", "="], ["-", "="], ["*", "="], ["/", "="], ["%", "="]],
    "<negative>": [["(", "<expr>", ")"], ["id", "<id_rhs_tail>"], ["<builtin_w_ret>"]],
    "<arith_op>": [["+"], ["-"], ["/"], ["%"], ["*"], ["^"]],
    "<not_tail>": [["(", "<expr>", ")"], ["id"]],
    "<relat_op>": [["<"], [">"], ["<", "="], [">", "="], ["=", "="], ["!", "="]],
    "<logic_op>": [["&", "&"], ["|", "|"], ["AND"], ["OR"]],
    "<builtin_no_ret>": [["shoot", "(", "<shoot_args>", ")"], ["shootNxt", "(", "<shoot_args>", ")"],
                         ["wipe", "(", ")"]],
   
}

first_set = compute_first_set(cfg)
print("First Sets:")
for non_terminal, first in first_set.items():
    print(f"{non_terminal} -> {first}")

follow_set = compute_follow_set(cfg, "<S>", first_set)
print("\nFollow Sets:")
for non_terminal, follow in follow_set.items():
    print(f"{non_terminal} -> {follow}")

predict_set = compute_predict_set(cfg, first_set, follow_set)

def display_predict_sets(predict_set):
    print("\nPredict Sets:")
    for (non_terminal, production), predict in predict_set.items():
        production_str = ", ".join(production)
        print(f"{non_terminal} → {{ {production_str} }} :  {predict} ")

display_predict_sets(predict_set)

def gen_parse_table():
    parse_table = {}
    for (non_terminal, production), predict in predict_set.items():
        if non_terminal not in parse_table:
            parse_table[non_terminal] = {}
        for terminal in predict:
            parse_table[non_terminal][terminal] = production

    return parse_table
        
parse_table = gen_parse_table()

def display_parse_table(parse_table):
    print()
    for non_terminal, rules in parse_table.items():
        print(f"Non-terminal: {non_terminal}")
        for terminal, production in rules.items():
            print(f"  Terminal: {terminal} -> Production: {production}")
        print()  

display_parse_table(parse_table)
