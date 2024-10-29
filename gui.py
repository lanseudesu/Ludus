import customtkinter as ctk

window = ctk.CTk()
window.title("Ludus")
window.geometry("1000x700") #widthxlength

def checkbox_event():
    print("checkbox toggled, current value:", check_var.get())

check_var = ctk.StringVar(value="0")
checkbox = ctk.CTkCheckBox(window, 
    text="CTkCheckBox", 
    fg_color="green",
    hover_color="gray",
    border_width=3,
    border_color="gray",
    command=checkbox_event,
    variable=check_var, 
    onvalue="1", offvalue="0"
)
checkbox.pack(pady=10)

code_input = ctk.StringVar()
code = ctk.CTkEntry(
    window, 
    textvariable = code_input,
    width=400,
    height=200
)
code.pack(pady=10)

window.mainloop()