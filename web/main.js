let editor;
let isModified = false
let keyListener = null;

document.addEventListener("DOMContentLoaded", () => {
    console.log("App started, sessionStorage cleared:", sessionStorage.getItem("preservedTextFirstRun"));

    const savedText = localStorage.getItem("editorText");  // Retrieve saved text
    const savedHistory = sessionStorage.getItem("editorHistory");

    editor = CodeMirror.fromTextArea(document.getElementById("editor"), {
        lineNumbers: false, 
        mode: "ludus",
        theme: "default",
    });

    editor.on("change", () => {
        isModified = true;
    });

    if (savedText) {
        editor.setValue(savedText, -1);
    }

    if (savedHistory) {
        const history = JSON.parse(savedHistory);
        editor.setHistory(history);
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

    editor.on("change", () => {
        localStorage.setItem("editorText", editor.getValue());
        updateLineNumbers();
    });

    editor.on("scroll", syncLineNumbersScroll);

    updateLineNumbers();

    if (!sessionStorage.getItem("hasLoaded")) {
        sessionStorage.setItem("hasLoaded", "true");
        console.log('Skipping analyzers on initial load');
        return;
    }

    if (window.location.href.includes("index.html")) {
        console.log("Running analyzers after navigation...");
        lexicalAnalyzer();
        runtime();
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

        const yesButton = document.getElementById('confirmYes');
        const noButton = document.getElementById('confirmNo');
        yesButton.replaceWith(yesButton.cloneNode(true));
        noButton.replaceWith(noButton.cloneNode(true));

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
        editor.setValue(content, -1);
        isModified = false;
    } catch (error) {
        console.error("Error creating new file:", error);
        alert("An error occurred while creating a new file.");
    }
}

async function openFile() {
    if (isModified && (!sessionStorage.getItem("hasLoaded"))) {
        const confirmResult = await showCustomConfirm("You have unsaved changes. Do you want to proceed and discard them?");
        if (!confirmResult) {
            return;
        }
    }

    try {
        const content = await eel.open_file()();
        if (content !== null) {
            editor.setValue(content, -1);
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

    document.addEventListener('click', closeCustomAlert);
    document.addEventListener('keydown', closeCustomAlert);
}

function closeCustomAlert() {
    const alertBox = document.getElementById('customAlert');
    alertBox.classList.add('hidden');

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
    sessionStorage.setItem("preservedTextFirstRun", "true");
    console.log("First run of preserveText after app start.");
        
    if (editor) {
        localStorage.setItem("editorText", editor.getValue());

        const history = editor.getHistory();
        sessionStorage.setItem("editorHistory", JSON.stringify(history));
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

function runtime() {
    console.log("tatat", keyListener)
    if (keyListener) {
        //eel.pass_input("stop")
        document.removeEventListener("keydown", keyListener);
        keyListener = null;
        console.log("Key listener removed.");
    }
    console.log("after", keyListener)
    document.querySelector("button").disabled = true;

    eel.reset_interpreter()().then(() => {
        setTimeout(() => {
            const inputBox = document.getElementById("error2");
            inputBox.value = "";
            lexicalAnalyzer();
            const inputText = editor.getValue(); 
            eel.runtime_backend(inputText); 
            document.querySelector("button").disabled = false;
        }, 30);
    });
    
    
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
    if (errorArea) {
        if (errorArea.value === "") {
            errorArea.value = result;
        } else {
            errorArea.value += "\n\n" + result;
            console.log("tatat", keyListener)
            if (keyListener) {
                document.removeEventListener("keydown", keyListener);
                keyListener = null;
                console.log("Key listener removed.");
            }
            console.log("after", keyListener)
        }
        
    } 
}

eel.expose(clearError);
function clearError() {
    const errorArea = document.getElementById("error");
    if (errorArea) errorArea.value = ""; 
}

eel.expose(clearTerminal);
function clearTerminal() {
    const errorArea = document.getElementById("error2");
    if (errorArea) errorArea.value = ""; 
}

eel.expose(clearLexemeToken);
function clearLexemeToken() {
    const lexemeArea = document.getElementById("lexeme");
    const tokenArea = document.getElementById("token");

    if (lexemeArea) lexemeArea.innerHTML = "";  
    if (tokenArea) tokenArea.innerHTML = "";  
}



eel.expose(requestInput);
function requestInput(promptText) {
    console.log(`Requesting input from frontend: ${promptText}`);
    
    const inputBox = document.getElementById("error2");
    inputBox.value += promptText;
    const promptLength = inputBox.value.length;
    inputBox.removeAttribute('readonly');
    inputBox.focus();  

    if (keyListener) {
        document.removeEventListener("keydown", keyListener);
    }

    keyListener = function(event) {
        if (event.key === "Enter") {
            event.preventDefault();  

            const userInput = inputBox.value;  
            const newInput = userInput.slice(promptLength).trim();
            console.log("Typed input:", newInput);

            if (newInput !== "") {
                eel.pass_input(newInput)  
                console.log("Input sent to Python.");       
            }
            inputBox.setAttribute('readonly', true);
        }
    };
    document.addEventListener("keydown", keyListener);
}

eel.expose(printShoot);
function printShoot(shootElement) {
    console.log(`Received shoot element: ${shootElement}`);
    
    const inputBox = document.getElementById("error2");
    inputBox.value += shootElement;  
}