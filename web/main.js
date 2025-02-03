let editor;

document.addEventListener("DOMContentLoaded", () => {
    const savedText = localStorage.getItem("editorText");  // Retrieve saved text

    editor = CodeMirror.fromTextArea(document.getElementById("editor"), {
        lineNumbers: false, 
        mode: "ludus",
        theme: "default",
    });

    // Restore saved text if available
    if (savedText) {
        editor.setValue(savedText);
    }

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

    // Save editor content automatically when the user types
    editor.on("change", () => {
        localStorage.setItem("editorText", editor.getValue());
        updateLineNumbers();
    });

    editor.on("scroll", syncLineNumbersScroll);

    updateLineNumbers();
});

function preserveText() {
    if (editor) {
        localStorage.setItem("editorText", editor.getValue());
    }
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

function lexicalAnalyzer() {
    const inputText = editor.getValue(); 
    eel.lexical_analyzer(inputText); 
}

function syntaxAnalyzer() {
    const inputText = editor.getValue(); 
    eel.syntax_analyzer(inputText); 
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
