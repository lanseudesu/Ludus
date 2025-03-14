let editor;
let isModified = false

document.addEventListener("DOMContentLoaded", () => {
    const savedText = localStorage.getItem("editorText");  // Retrieve saved text

    editor = CodeMirror.fromTextArea(document.getElementById("editor"), {
        lineNumbers: false, 
        mode: "ludus",
        theme: "default",
    });

    editor.on("change", () => {
        isModified = true;
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

    if (window.location.href.includes("index.html")) {
        console.log("Running analyzers after navigation...");
        lexicalAnalyzer();
        syntaxAnalyzer();
        semanticAnalyzer();
    }

    if (window.location.href.includes("lexerpage.html")) {
        console.log("Running Lexical Analyzer after navigation...");
        lexicalAnalyzer();
    }

    if (window.location.href.includes("syntax.html")) {
        console.log("Running Syntax analyzer after navigation...");
        syntaxAnalyzer();
        lexicalAnalyzer();
    }

    if (window.location.href.includes("semantic_page.html")) {
        console.log("Running Semantic Analyzer after navigation...");
        lexicalAnalyzer();
        semanticAnalyzer(); 
    }
});

window.onload = () => {
    const modal = document.getElementById('customConfirm');
    if (modal) {
        modal.classList.add('hidden');
        console.log('Modal hidden status on load:', modal.classList.contains('hidden'));
    } else {
        console.log('Modal not found on load');
    }
};

function showCustomConfirm(message, callback = null) {
    return new Promise((resolve) => {
        document.getElementById('confirmMessage').textContent = message;
        document.getElementById('customConfirm').classList.remove('hidden');

        // Cleanup any old event listeners first
        const yesButton = document.getElementById('confirmYes');
        const noButton = document.getElementById('confirmNo');
        yesButton.replaceWith(yesButton.cloneNode(true));
        noButton.replaceWith(noButton.cloneNode(true));

        // Re-fetch buttons after cloning
        const newYesButton = document.getElementById('confirmYes');
        const newNoButton = document.getElementById('confirmNo');

        const handleResponse = (result) => {
            document.getElementById('customConfirm').classList.add('hidden');
            if (callback) callback(result);
            resolve(result);
        };

        newYesButton.addEventListener('click', () => handleResponse(true));
        newNoButton.addEventListener('click', () => handleResponse(false));
    });
}

async function newFile() {
    if (isModified) {
        showCustomConfirm("You have unsaved changes. Do you want to continue?", async (result) => {
            if (result) {
                await newFileAction();
            }
        });
        return;
    }
    await newFileAction();
}

async function newFileAction() {
    try {
        const content = await eel.create_new_file()();
        editor.setValue(content);
        isModified = false;
    } catch (error) {
        console.error("Error creating new file:", error);
        alert("An error occurred while creating a new file.");
    }
}

async function openFile() {
    if (isModified) {
        const confirmResult = await showCustomConfirm("You have unsaved changes. Do you want to proceed and discard them?");
        if (!confirmResult) {
            return;
        }
    }

    try {
        const content = await eel.open_file()();
        if (content !== null) {
            editor.setValue(content);
            isModified = false;
        }
    } catch (error) {
        console.error("Error opening file:", error);
        alert("An error occurred while opening the file.");
    }
}

function showCustomAlert(message) {
    document.getElementById('alertMessage').textContent = message;
    document.getElementById('customAlert').classList.remove('hidden');

    // Close on any click or key press
    document.addEventListener('click', closeCustomAlert);
    document.addEventListener('keydown', closeCustomAlert);
}

function closeCustomAlert() {
    const alertBox = document.getElementById('customAlert');
    alertBox.classList.add('hidden');

    // Clean up event listeners after closing
    document.removeEventListener('click', closeCustomAlert);
    document.removeEventListener('keydown', closeCustomAlert);
}

async function saveFile() {
    try {
        const content = editor.getValue();
        const success = await eel.save_file(content)();
        if (success) {
            isModified = false;
            showCustomAlert("File saved successfully!");
        } else {
            saveAs();
        }
    } catch (error) {
        console.error("Error saving file:", error);
        showCustomAlert("An error occurred while saving the file.");
    }
}

async function saveAs() {
    try {
        const content = editor.getValue();
        const success = await eel.save_file_as(content)();
        if (success) {
            isModified = false;
            showCustomAlert("File saved successfully!");
        }
    } catch (error) {
        console.error("Error saving file as:", error);
        showCustomAlert("An error occurred while saving the file.");
    }
}

function exitApp() {
        window.close();
        eel.exit_app();
}

document.addEventListener("keydown", (event) => {
    if (event.ctrlKey && event.key.toLowerCase() === "n") {
        event.preventDefault();
        newFile();  // Ctrl + N → New File
    }
    else if (event.ctrlKey && event.key.toLowerCase() === "o") {
        event.preventDefault();
        openFile();  // Ctrl + O → Open File
    }
    else if (event.ctrlKey && event.key.toLowerCase() === "s") {
        event.preventDefault();
        if (event.shiftKey) {
            saveAs();  // Ctrl + Shift + S → Save As
        } else {
            saveFile();  // Ctrl + S → Save
        }
    }
    else if (event.ctrlKey && event.key.toLowerCase() === "q") {
        event.preventDefault();
        exitApp();  // Ctrl + W → Exit App
    }
});

function preserveText() {
    if (editor) {
        localStorage.setItem("editorText", editor.getValue());
    }
}

function toggleFileButton() {
    document.getElementById("dropdown-content").classList.toggle("show");
}

window.onclick = function(event) {
    if (!event.target.matches('.file-button')) {
        var dropdowns = document.getElementsByClassName("file-options");
        var i;
        for (i = 0; i < dropdowns.length; i++) {
            var openDropdown = dropdowns[i];
            if (openDropdown.classList.contains('show')) {
                openDropdown.classList.remove('show');
            }
        }
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

function semanticAnalyzer() {
    const inputText = editor.getValue(); 
    eel.semantic_analyzer(inputText); 
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

eel.expose(updateTerminal);
function updateTerminal(result) {
    const errorArea = document.getElementById("error2");
    if (errorArea) errorArea.value = result; 
}

eel.expose(clearError);
function clearError() {
    const errorArea = document.getElementById("error");
    if (errorArea) errorArea.value = ""; 
}
