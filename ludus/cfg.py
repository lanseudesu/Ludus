cfg = {
    "<program>": [["<global_dec>", "<func_dec>", "play", "(", ")", "{", "<body>", "}", "<fs_body>", "gameOver"]],
    "<global_dec>": [["immo", "id", "<global_dec_tail1>", "<global_dec>"],
                     ["id", "<global_dec_tail2>", "<global_dec>"],
                     ["<datatype>", "id", "<global_dec_tail3>", "<global_dec>"],
                     ["λ"]], 
    "<global_dec_tail1>": [["[", "hp_ltr", "]", "<arr_tail1>"],
                           ["<const_tail>"]],
    "<global_dec_tail2>": [["<const_tail>"],
                           ["[", "<arr_size>", "]", "<arr_tail2>"]],
    "<global_dec_tail3>": [["<id_recur>", "<dead_dec>"],
                           ["[", "<arr_size>", "]", "<arr_tail3>"]],
    "<arr_tail1>": [[":", "[", "<value>", ",", "<value>", "<elems_recur>", "]"],
                    ["[", "hp_ltr", "]", ":", "[", "<value>", ",", "<value>", "<elems_recur>", "]", ",", "[", "<value>", ",", "<value>", "<elems_recur>", "]", "<row_recur2>"]],
    "<arr_tail2>": [[":", "[", "<value>", "<elems_recur>", "]"],
                    ["[", "<arr_size>", "]", ":", "[", "<value>", "<elems_recur>", "]", "<row_recur>"]],
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
                      ["xp_ltr"]],
    "<elems_recur>": [[",", "<value>", "<elems_recur>"],
                      ["λ"]],
    "<row_recur>": [[",", "[", "<value>", "<elems_recur>", "]", "<row_recur>"],
                    ["λ"]], 
    "<row_recur2>": [[",", "[", "<value>", ",", "<value>", "<elems_recur>", "]", "<row_recur2>"],
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
                       ["<local_dec_or_ass>"],
                       ["<builtin_no_ret>"],
                       ["<local_struct>"],
                       ["<struct_inst>"]],

    # sam 63-122
    "<main_stmts>": [["<conditional>"], 
                     ["<looping>"], 
                     ["<common_stmts>"]],
    "<body>": [["<main_stmts>", "<body_recur>"]],
    "<body_recur>": [["<body>"], 
                     ["λ"]],
    "<local_dec>": [["immo", "<local_immo_tail>"], 
                    ["<datatype>", "id", "<global_dec_tail3>"]],
    "<local_dec_or_ass>": [["id", "<dec_tail>"]],
    "<local_immo_tail>": [["id", "<global_dec_tail1>"], 
                          ["access", "id", "id", ":", "<value>", "<elems_recur>"]],
    "<dec_tail>": [["<col_or_ass>"], 
                   ["(", "<args>", ")"], 
                   [".", "<dot_tail>"], 
                   ["[", "<index>", "]", "<bracket_tail>"]],
    "<dot_tail>": [["id", "<dot_tail_rhs>"], 
                   ["drop", "(", "<index>", ")"], 
                   ["join", "(", "<arr_rhs_tail>", ")"]], 
    "<dot_tail_rhs>": [[":", "<expr>"], 
                   ["<assign_op>", "<expr>"]],               
    "<bracket_tail>": [[":", "<arr_rhs_tail>"], 
                       ["<assign_op>", "<expr>"],
                       ["[", "<index>", "]", "<arr2d_rhs>"], 
                       [".", "<inner_bracket_tail>"]], 
    "<arr_rhs_tail>": [["[", "<value>", "<elems_recur>", "]"],
                       ["<expr>"]], 
    "<inner_bracket_tail>": [["drop", "(", "<index>", ")"], 
                             ["join", "(", "<expr>", ")"]],
    "<index>": [["<expr>"], 
                ["λ"]], 
    "<arr2d_rhs>": [[":", "<arr2d_rhs_tail>"], 
                    ["<assign_op>", "<expr>"]],
    "<arr2d_rhs_tail>": [["[", "<value>", "<elems_recur>", "]", "<row_recur>"], 
                         ["<expr>"]], 
    "<col_or_ass>": [[":", "<col_tail>"], 
                     [",", "id", "<id_recur>", ":", "<expr>"], 
                     ["<assign_op>", "<expr>"]],
    "<col_tail>": [["<expr>", "<expr_recur>"],
                  ["[", "<value>", "<elems_recur>", "]", "<row_recur>"]],
    "<id_tail>": [[".", "id"], 
                  ["[", "<expr>", "]", "<id_tail_arr>"], 
                  ["λ"]], 
    "<id_tail_arr>": [["[", "<expr>", "]"], 
                      ["λ"]],
    "<expr_recur>": [[",", "id", ":", "<expr>", "<expr_recur>"], 
                     ["λ"]], 
    "<expr>": [["<relat_expr>", "<expr_tail>"]],
    "<expr_tail>": [["<logic_op>", "<expr>"], 
                    ["λ"]],
    "<relat_expr>": [["<arith_expr>", "<relat_tail>"]],                
    "<relat_tail>": [["<relat_op>", "<relat_expr>"], ["λ"]], 
    "<arith_expr>": [["<factor>", "<arith_tail>"]],
    "<arith_tail>": [["<arith_op>", "<arith_expr>"], 
                      ["λ"]],

    
    # khar 123-179
    "<factor>": [["id", "<id_rhs_tail>"], ["<value>"], ["-", "<negative>"],
                 ["<builtin_w_ret>"], ["!", "<negative>"], ["(", "<expr>", ")", "<xp_format>"]],
    "<id_rhs_tail>": [["(", "<args>", ")"], [".", "<rhs_dot_tail>"], 
                     ["[", "<expr>", "]", "<rhs_bracket_tail>"], ["xp_formatting"], ["λ"]],
    "<xp_format>": [["xp_formatting"], ["λ"]],               
    "<args>": [["<expr>", "<args_recur>"], ["λ"]],
    "<args_recur>": [[",", "<expr>", "<args_recur>"], ["λ"]],
    "<rhs_dot_tail>": [["id"], ["seek", "(", "<arr_rhs_tail>", ")"], ["drop", "(", "<index>", ")"]],
    "<rhs_bracket_tail>": [["[", "<expr>", "]"], [".", "<rhs_inner_bracket_tail>"], ["λ"]],
    "<rhs_inner_bracket_tail>": [["drop", "(", "<index>", ")"], ["seek", "(", "<expr>", ")"]],
    "<assign_op>": [["+="], ["-="], ["*="], ["/="], ["%="]],
    "<negative>": [["(", "<expr>", ")"], ["id", "<id_tail>"]],
    "<arith_op>": [["+"], ["-"], ["/"], ["%"], ["*"], ["^"]],
    "<relat_op>": [["<"], [">"], ["<="], [">="], ["=="], ["!="]],
    "<logic_op>": [["&&"], ["||"], ["AND"], ["OR"]],
    "<builtin_no_ret>": [["shoot", "(", "<shoot_args>", ")"], 
                         ["shootNxt", "(", "<shoot_args>", ")"],
                         ["wipe", "(", ")"]],
    
    #jae 180-242
    "<builtin_w_ret>": [["load", "(", "<load_args>", ")"], 
                        ["loadNum", "(", "<load_args>", ")"], 
                        ["rounds", "(", "<rounds_args>", ")"], 
                        ["levelUp", "(", "id", "<id_args_tail>", ")"], 
                        ["levelDown", "(", "id", "<id_args_tail>", ")"], 
                        ["toHp", "(", "<expr>", ")"], 
                        ["toXp", "(", "<expr>", ")"], 
                        ["toComms", "(", "<expr>", ")"]], 
    "<shoot_args>": [["<expr>"], 
                     ["λ"]],
    "<load_args>": [["comms_ltr"], 
                    ["λ"]],
    "<rounds_args>": [["comms_ltr"], 
                     ["id", "<id_args_tail>"],
                     ["toComms", "(", "id", "<id_tail>", ")"]],
    "<id_args_tail>": [["<id_tail>" ], ["(", "<args>", ")"]],
    "<recall_stmt>": [["recall", "<rec_elems>"]],
    "<rec_elems>": [["<expr>", "<rec_elems_recur>"], 
                    ["[", "]"], ["void"]],
    "<rec_elems_recur>": [[",", "<expr>", "<rec_elems_recur>"], 
                          ["λ"]],               
    "<loop_control>": [["resume"], 
                       ["checkpoint"]],
    "<local_struct>": [["build", "id", "{", "<struct_fields>", "<struct_fields_recur>", "}"]],
    "<struct_fields>": [["<datatype>", "id", "<field_dec>"]],
    "<field_dec>": [[",", "<struct_fields>"], 
                    ["λ"]],
    "<def_recur>": [[",", "<datatype>", "id", ":", "<value>", "<def_recur>"], 
                    ["λ"]],
    "<struct_fields_recur>": [[":", "<value>", "<def_recur>"], 
                              ["λ"]],
    "<struct_inst>": [["access", "id", "id", "<inst_dec>"]],
    "<inst_dec>": [[":", "<value>", "<instval_recur>"], 
                   ["λ"]],
    "<instval_recur>": [[",", "<value>", "<instval_recur>"], 
                        ["λ"]],
    "<conditional>": [["<if_stmt>"],["<flank_stmt>"]],
    "<if_stmt>": [["if", "<expr>", "{", "<body>", "}", "<else_elif>"]],
    "<else_elif>": [["<else_stmt>"], ["<elif_stmt>"], 
                    ["λ"]],
    "<else_stmt>": [["else", "{", "<body>", "}"]],
    "<elif_stmt>": [["elif", "<expr>", "{", "<body>", "}", "<else_elif>"]],
    "<flank_stmt>": [["flank", "<expr>", "{", "choice", "<valdead>", "<valdead_recur>", ":", "<flank_body>", "}"]],
    "<flank_body>": [["<main_stmts>", "<flank_body_recur>"],
                     ["resume", "<choice_recur>"]],
    "<flank_body_recur>": [["<flank_body>"],
                           ["<choice_recur>"]],                
    "<valdead>": [["<value>"], ["dead"]],
    "<valdead_recur>": [[",", "<valdead>", "<valdead_recur>"], 
                        ["λ"]],
    "<choice_recur>": [["choice", "<valdead>", "<valdead_recur>", ":", "<flank_body>"], 
                       ["backup", ":", "<body>"]],
    "<looping>":[["<for_loop>"], ["<while_loop>"], ["<do_while_loop>"]],
    "<for_loop>": [["for", "id", ":", "<arith_expr>", ",", "<expr>", ",", "id", "<update>", "{", "<loop_body>", "}"]],
    "<update>": [["<assign_op>", "<arith_expr>"], [":", "<arith_expr>"]],
    "<while_loop>": [["while", "<expr>", "{", "<loop_body>", "}"]],
    "<do_while_loop>": [["grind", "{", "<loop_body>", "}", "while", "<expr>"]],
    "<loop_body>": [["<loop_stmts>", "<loop_body_recur>"]],
    "<loop_body_recur>": [["<loop_body>"], 
                          ["λ"]],
   #jm 243-305
    "<loop_stmts>": [["<common_stmts>"], ["<if_stmt_loop>"], ["<flank_stmt_loop>"], 
                     ["<looping>"]],
    "<if_stmt_loop>": [["if", "<expr>", "{", "<main_stmts_loop>", "}",  "<else_elif_loop>"]],
    "<else_elif_loop>": [["<else_stmt_loop>"], ["<elif_stmt_loop>"], ["λ"],],
    "<else_stmt_loop>": [["else", "{", "<main_stmts_loop>", "}"]],
    "<elif_stmt_loop>": [["elif", "<expr>", "{", "<main_stmts_loop>", "}", "<else_elif_loop>"]],
    "<flank_stmt_loop>": [["flank", "<expr>", "{", "choice", "<valdead>", "<valdead_recur>", ":", "<flank_body_loop>", "}"]],
    "<flank_body_loop>": [["<main_stmts>", "<flank_loop_recur>"],
                         ["<loop_control>", "<loop_choice_recur>"]],
    "<flank_loop_recur>": [["<flank_body_loop>"],
                           ["<loop_choice_recur>"]],    
    "<loop_choice_recur>": [["choice", "<valdead>", "<valdead_recur>", ":", "<flank_body_loop>"], 
                            ["backup", ":", "<backup_loop_body>"]],
    "<backup_loop_body>": [["<body>"],["checkpoint"]],                    
    "<main_stmts_loop>": [["<loop_stmts>", "<cond_recur_loop>"], 
                          ["<loop_control>"]],
    "<cond_recur_loop>": [["<main_stmts_loop>"], ["λ"]],
    "<fs_body>": [["<func_body>"]],
    "<func_body>": [["generate", "id", "(", "<params>", ")", "{", "<func_stmts_recur>", "}", "<func_body>"],
                    ["<struct_body>"]],
    "<struct_body>": [["<local_struct>", "<struct_body>"],
                      ["λ"]],
    "<func_stmts>": [["<common_stmts>"], ["<recall_stmt>"],
                     ["<if_stmt_func>"], ["<flank_func>"],
                     ["<looping_func>"]],
    "<func_stmts_recur>": [["<func_stmts>", "<func_stmts_recur>"], ["λ"]],               
    "<flank_func>": [["flank", "<expr>", "{", "choice", "<valdead>", "<valdead_recur>",
                     ":", "<flank_func_body>", "}"]],
    "<flank_func_body>": [["<main_stmts>", "<flank_func_recur>"], 
                          ["<recall_stmt>", "<choice_func_recur>"], 
                          ["resume", "<choice_func_recur>"]],
    "<flank_func_recur>": [["<flank_func_body>"], ["<choice_func_recur>"]],
    "<choice_func_recur>": [["choice", "<valdead>", "<valdead_recur>", ":", "<flank_func_body>"], 
                            ["backup", ":", "<backup_func_body>"]],
    "<backup_func_body>": [["<main_stmts>", "<backup_func_body>"], ["<recall_stmt>"]],
    "<if_stmt_func>": [["if", "<expr>", "{", "<func_stmts>", "<func_stmts_recur>", "}", "<else_elif_func>"]],
    "<else_elif_func>": [["<else_stmt_func>"], ["<elif_stmt_func>"], ["λ"]],
    "<else_stmt_func>": [["else", "{", "<func_stmts>", "<func_stmts_recur>", "}"]],
    "<elif_stmt_func>": [["elif", "<expr>", "{", "<func_stmts>", "<func_stmts_recur>", "}", "<else_elif_func>"]],
    "<looping_func>": [["<for_func>"], ["<while_func>"], ["<do_while_func>"]],
    "<for_func>": [["for", "id", ":", "<arith_expr>", ",", "<expr>", ",", "id",
                   "<update>", "{", "<loop_body_func>", "}"]],
    "<while_func>": [["while", "<expr>", "{", "<loop_body_func>", "}"]],
    "<do_while_func>": [["grind", "{", "<loop_body_func>", "}", "while", "<expr>"]],
    "<loop_body_func>": [["<func_stmts_loop>", "<loop_body_recur>"]],
    "<func_stmts_loop>": [["<if_func_loop>"], ["<common_stmts>"], ["<flank_loop_func>"], 
                     ["<recall_stmt>"], ["<looping_func>"]],
    "<if_func_loop>": [["if", "<expr>", "{", "<func_loop_cond>", "}", "<else_elif_func_loop>"]],
    "<else_elif_func_loop>": [["<else_func_loop>"], ["λ"], ["<elif_func_loop>"]],
    "<else_func_loop>": [["else", "{", "<func_loop_cond>", "}"]],
    "<elif_func_loop>": [["elif", "<expr>", "{", "<func_loop_cond>", "}", "<else_elif_func>"]],
    "<func_loop_cond>": [["<func_stmts_loop>", "<func_loop_recur>"], ["<loop_control>", "<func_loop_recur>"]],
    "<func_loop_recur>": [["<func_loop_cond>"], ["λ"]],
    "<flank_loop_func>": [["flank", "<expr>", "{", "choice", "<valdead>", "<valdead_recur>",
                        ":", "<flank_body_func_loop>", "}"]],
    "<flank_body_func_loop>": [["<main_stmts>", "<flank_func_loop_recur>"], 
                              ["<recall_stmt>", "<loop_func_choice_recur>"], 
                              ["<loop_control>", "<loop_func_choice_recur>"]],
    "<flank_func_loop_recur>": [["<flank_body_func_loop>"], ["<loop_func_choice_recur>"]],
    "<loop_func_choice_recur>": [["choice", "<valdead>", "<valdead_recur>", ":", "<flank_body_func_loop>"], 
                            ["backup", ":", "<backup_func_loop_body>"]],
    "<backup_func_loop_body>": [["<main_stmts>", "<backup_func_loop_body>"], ["<recall_stmt>"],
                                ["checkpoint"]],
}

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

    changed = True  

    while changed:
        changed = False 
    
        for non_terminal, productions in cfg.items():
            for production in productions:
                for i, item in enumerate(production):
                    if item in cfg:  # nt only
                        follow_before = follow_set[item].copy()

                        if i + 1 < len(production):  # A -> <alpha>B<beta>
                            beta = production[i + 1]
                            if beta in cfg:  # if <beta> is a non-terminal
                                follow_set[item].update(first_set[beta] - {"λ"})
                                if "λ" in first_set[beta]:
                                    follow_set[item].update(follow_set[beta])
                            else:  # if <beta> is a terminal
                                follow_set[item].add(beta)
                        else:  # nothing follows B
                            follow_set[item].update(follow_set[non_terminal])

                        if follow_set[item] != follow_before:
                            changed = True  

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

# for non_terminal, productions in cfg.items():
#     for i, item in enumerate(productions):
#         print(f"{non_terminal} -> {productions[i]}")

first_set = compute_first_set(cfg)
# print("First Sets:")
# for non_terminal, first in first_set.items():
#     print(f"{first}")

# terminals = set()
# for productions in cfg.values():
#     for production in productions:
#         for symbol in production:
#             if not symbol.startswith("<"):  
#                 terminals.add(symbol)

# unique_terminals = sorted(terminals)
# print(unique_terminals)

follow_set = compute_follow_set(cfg, "<program>", first_set)
# print("\nFollow Sets:")
# for non_terminal, follow in follow_set.items():
#     print(f"{follow}")

predict_set = compute_predict_set(cfg, first_set, follow_set)

def display_predict_sets(predict_set):
    print("\nPredict Sets:")
    for (non_terminal, production), predict in predict_set.items():
        production_str = ", ".join(production)
        print(f"{non_terminal} -> {{ {production_str} }} :  {predict} ")

# display_predict_sets(predict_set)

def gen_parse_table():
    parse_table = {}
    for (non_terminal, production), predict in predict_set.items():
        if non_terminal not in parse_table:
            parse_table[non_terminal] = {}
        for terminal in predict:
            parse_table[non_terminal][terminal] = production

    return parse_table
        
parse_table = gen_parse_table()

def save_parse_table(parse_table, filename="parse_table.txt"):
    with open(filename, "w", encoding="utf-8") as file:  
        terminals = {}
        for non_terminal, rules in parse_table.items():
            for terminal, production in rules.items():
                if terminal not in terminals:
                    terminals[terminal] = []
                terminals[terminal].append(f"    Non-terminal: {non_terminal} -> Production: {production}")

        for terminal, productions in terminals.items():
            file.write(f"Terminal: {terminal}\n")
            for production in productions:
                file.write(f"{production}\n")
            file.write("\n")


# save_parse_table(parse_table)
# print("Parse table saved to file.")

def check_ambiguity(cfg, predict_set):
    ambiguous_productions = []

    for non_terminal, productions in cfg.items():
        prediction_sets = [predict_set[(non_terminal, tuple(prod))] for prod in productions]
        for i in range(len(prediction_sets)):
            for j in range(i + 1, len(prediction_sets)):
                if prediction_sets[i].intersection(prediction_sets[j]):
                    ambiguous_productions.append((non_terminal, productions[i], productions[j]))

    if ambiguous_productions:
        print("\nAmbiguities found in the CFG:")
        for non_terminal, prod1, prod2 in ambiguous_productions:
            print(f"  {non_terminal} -> {prod1} | {prod2}")
    else:
        print("\nNo ambiguities found in the CFG.")

# check_ambiguity(cfg, predict_set)
