function navigateTo(section) {
    eel.navigate_to(section)(); 
}

function updateLineNumbers() {
    const textarea = document.getElementById("codeInput");
    const lineNumbers = document.getElementById("lineNumbers");
    const lines = textarea.value.split("\n").length;

    let lineNumbersHTML = "";
    for (let i = 1; i <= lines; i++) {
        lineNumbersHTML += i + "<br>";
    }

    lineNumbers.innerHTML = lineNumbersHTML;
}

function codeEditorScroll() {
    const textarea = document.getElementById("codeInput");
    const lineNumbers = document.getElementById("lineNumbers");

    lineNumbers.scrollTop = textarea.scrollTop;
}

function lexemeTokenScroll(sourceId) {
    const lexemeArea = document.getElementById("lexeme");
    const tokenArea = document.getElementById("token");

    if (sourceId === "lexeme") {
        tokenArea.scrollTop = lexemeArea.scrollTop; 
    } else if (sourceId === "token") {
        lexemeArea.scrollTop = tokenArea.scrollTop; 
    }
}

function sendTextToPython() {
    const inputText = document.getElementById("codeInput").value; 
    eel.process_text(inputText); 
}

eel.expose(updateLexemeToken);
function updateLexemeToken(lexemes, tokens) {
    document.getElementById("lexeme").value = lexemes; 
    document.getElementById("token").value = tokens; 
}

eel.expose(updateError);
function updateError(errors) {
    document.getElementById("error").value = errors; 
}

eel.expose(clearError);
function clearError() {
    document.getElementById("error").value = ""; 
}