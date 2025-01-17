import eel

# Initialize the Eel app
eel.init('web')  # The folder containing web files

# Python function callable from JavaScript
@eel.expose
def say_hello_py(name):
    print(f"Hello from Python, {name}!")
    return f"Hello, {name}! - From Python"

# Start the Eel app
eel.start('index.html', size=(1300, 800))