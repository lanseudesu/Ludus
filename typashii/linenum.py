#LINE NUMBER TEST
#Ctrl A + Backspace = pati line nums nabubura then hindi na nababalik
#If nagbackspace, yung numbers is hangggang mafill yung window though dapat wala na siya
#Gawin Responsive like if niresize window vertically pero nagbackspace ka, matic na magreresize siya

from tkinter import Text, Tk
from tkinter.ttk import Style

from tklinenums import TkLineNumbers

# Create the root window
root = Tk()
root.title("TRIAL")

# Create the Text widget and pack it to the right
text =  Text(root)
text.pack(side="right", fill="both", expand=True)

# Insert 50 lines of text into the Text widget
for i in range(50):
    text.insert("end", f"\n")

# Create the TkLineNumbers widget and pack it to the left
linenums = TkLineNumbers(root, text, justify="center", colors=("#ffffff", "#000000"))
linenums.pack(fill="y", side="left")

# Redraw the line numbers when the text widget contents are modified
text.bind("<<Configure>>", lambda event: root.after_idle(linenums.redraw), add=True)

# Start the mainloop for the root window
root.mainloop()