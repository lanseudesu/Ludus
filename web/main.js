// function sayHello() {
//     const name = document.getElementById('nameInput').value;
//     eel.say_hello_py(name)(response => {
//         document.getElementById('response').innerText = response;
//     });
// }
function navigateTo(section) {
    eel.navigate_to(section)(); // Call a Python function to handle navigation
}

function updateLineNumbers() {
    const textarea = document.getElementById("codeInput");
    const lineNumbers = document.getElementById("lineNumbers");
    const lines = textarea.value.split("\n").length;

    // Generate line numbers dynamically
    let lineNumbersHTML = "";
    for (let i = 1; i <= lines; i++) {
        lineNumbersHTML += i + "<br>";
    }

    lineNumbers.innerHTML = lineNumbersHTML;
}

function codeEditorScroll() {
    const textarea = document.getElementById("codeInput");
    const lineNumbers = document.getElementById("lineNumbers");

    // Sync scrolling
    lineNumbers.scrollTop = textarea.scrollTop;
}

function lexemeTokenScroll(sourceId) {
    const lexemeArea = document.getElementById("lexeme");
    const tokenArea = document.getElementById("token");

    if (sourceId === "lexeme") {
        tokenArea.scrollTop = lexemeArea.scrollTop; // Sync token's scroll to lexeme's scroll
    } else if (sourceId === "token") {
        lexemeArea.scrollTop = tokenArea.scrollTop; // Sync lexeme's scroll to token's scroll
    }
}

function sendTextToPython() {
    const inputText = document.getElementById("codeInput").value; // Get text from the textarea
    eel.process_text(inputText); // Send it to the Python function via eel
}

eel.expose(updateLexemeToken);
function updateLexemeToken(lexemes, tokens) {
    document.getElementById("lexeme").value = lexemes; // Set the value of the lexeme textarea
    document.getElementById("token").value = tokens; // Set the value of the lexeme textarea
}

eel.expose(updateError);
function updateError(errors) {
    document.getElementById("error").value = errors; 
}
