function sayHello() {
    const name = document.getElementById('nameInput').value;
    eel.say_hello_py(name)(response => {
        document.getElementById('response').innerText = response;
    });
}
