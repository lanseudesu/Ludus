import tkinter as tk
from tkinter import ttk

app = tk.Tk()
app.title("Practice Exercise - ATLAS")
app.geometry("800x600")

def buttonfunc():
    print(string_text.get())
    string_text.set("button pressed")
    print(rad_var.get())

def checkbutton_toggle():
    print("Checkbox toggled, value is now: ", check_var.get())


mainFrame = ttk.Frame(app)
mainFrame.pack()

string_text = tk.StringVar(value="test")

label = tk.Label(mainFrame, font=("Helvetica", 20, "bold"), textvariable=string_text)
label.pack()

entry = ttk.Entry(mainFrame, font=("Times New Roman", 12), textvariable=string_text)
entry.pack()

entry2 = ttk.Entry(mainFrame, font=("Times New Roman", 12), textvariable=string_text)
entry2.pack()

button = ttk.Button(mainFrame, text="Click Me!", command=buttonfunc)
button.pack()

check_var = tk.StringVar(value="Hooray")
checkbox = ttk.Checkbutton(mainFrame, text="Toggle me?", command=lambda:print(check_var.get()), variable= check_var, onvalue="Hooray", offvalue="HepHep")
checkbox.pack()

checkbox2 = ttk.Checkbutton(mainFrame, text="Check 2", command=lambda: check_var.set("Hephep"))
checkbox2.pack()

rad_var = tk.StringVar()
radiobtn1 = ttk.Radiobutton(mainFrame, text="Radio 1", value="Ticked Radio Button 1", variable=rad_var, command=lambda:print(rad_var.get()))
radiobtn1.pack()

radiobtn2 = ttk.Radiobutton(mainFrame, text="Radio 2", value="Ticked Radio Button 2", variable=rad_var)
radiobtn2.pack()

#create 2 radio btns and 1 check btn
# radio btns: values with A and B, ticking either prints the value of checkbtn, and ticking radiobtn unchecks the checkbtn
# check btn: ticking checkbtn prints value of radio btn value, and use Boolean var

def rd_chk_func():
    print(checkvar.get()) #ticking either prints the value of checkbtn
    checkvar.set(False) #ticking radiobtn unchecks the checkbtn

radiovar = tk.StringVar()
radio1 = ttk.Radiobutton(mainFrame, text="Radio 1", value="A", variable=radiovar, command=rd_chk_func)
radio1.pack()

radio2 = ttk.Radiobutton(mainFrame, text="Radio 2", value="B", variable=radiovar, command=rd_chk_func)
radio2.pack()

checkvar = tk.BooleanVar()
check = ttk.Checkbutton(mainFrame, text="Check Me", variable=checkvar, command=lambda:print(radiovar.get())) #ticking checkbtn prints value of radio btn value
check.pack()

import tkinter as tk

# def new_file_clicked(event=None):
#     print("The New File menu was clicked!")

# root = tk.Tk()
# root.title("Menubar in Tk")
# root.geometry("400x300")
# menubar = tk.Menu()
# file_menu = tk.Menu(menubar, tearoff=False)
# file_menu.add_command(
#     label="New",
#     accelerator="Ctrl+N",
#     command=new_file_clicked
# )
# root.bind_all("<Control-n>", new_file_clicked)
# root.bind_all("<Control-N>", new_file_clicked)
# menubar.add_cascade(menu=file_menu, label="File")
# root.config(menu=menubar)
# root.mainloop()

app.mainloop()