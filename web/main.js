let editor;

document.addEventListener("DOMContentLoaded", () => {
    editor = CodeMirror.fromTextArea(document.getElementById("editor"), {
        lineNumbers: false, 
        mode: "ludus",
        theme: "default",
    });

    function updateLineNumbers() {
        const lineNumbersElement = document.getElementById("lineNumbers");
        const totalLines = editor.lineCount();
        let lineNumbersHTML = '';

        for (let i = 1; i <= totalLines; i++) {
            lineNumbersHTML += i + '<br>';
        }

        if (lineNumbersElement) lineNumbersElement.innerHTML = lineNumbersHTML;
    }

    function syncLineNumbersScroll() {
        const lineNumbersElement = document.getElementById("lineNumbers");
        const scrollInfo = editor.getScrollInfo();
        lineNumbersElement.scrollTop = scrollInfo.top;
    }

    editor.on("scroll", () => {
        updateLineNumbers();
        syncLineNumbersScroll();
    });
    editor.on("change", updateLineNumbers);

    updateLineNumbers();
});

function navigateTo(section) {
    eel.navigate_to(section)(); 
}

function lexemeTokenScroll(sourceId) {
    const lexemeArea = document.getElementById("lexeme");
    const tokenArea = document.getElementById("token");

    if (!lexemeArea || !tokenArea) return; 

    if (sourceId === "lexeme") {
        tokenArea.scrollTop = lexemeArea.scrollTop; 
    } else if (sourceId === "token") {
        lexemeArea.scrollTop = tokenArea.scrollTop; 
    }
}

function sendTextToPython() {
    const inputText = editor.getValue(); 
    eel.process_text(inputText); 
}

eel.expose(updateLexemeToken);
function updateLexemeToken(lexemes, tokens) {
    const lexemeArea = document.getElementById("lexeme");
    const tokenArea = document.getElementById("token");

    const lexemeWithColors = lexemes.replace(/(\d+(\.\d+)?)(?=:)/g, function(match) {
        return `<span class="number">${match}</span>`;  
    });

    const tokenWithColors = tokens.replace(/(\d+(\.\d+)?)(?=:)/g, function(match) {
        return `<span class="number">${match}</span>`;  
    });

    if (lexemeArea) lexemeArea.innerHTML = lexemeWithColors;  
    if (tokenArea) tokenArea.innerHTML = tokenWithColors;  
}

eel.expose(updateError);
function updateError(errors) {
    const errorArea = document.getElementById("error");
    if (errorArea) errorArea.value = errors; 
}

eel.expose(clearError);
function clearError() {
    const errorArea = document.getElementById("error");
    if (errorArea) errorArea.value = ""; 
}
