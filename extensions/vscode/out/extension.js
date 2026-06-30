"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.activate = activate;
exports.deactivate = deactivate;
const vscode = require("vscode");
const fs = require("fs");
const path = require("path");
const child_process_1 = require("child_process");
// Hardcoded for the prototype to point to your main repository's core python scripts
const PYTHON_CORE_DIR = "d:\\github_proj\\ai_session_transfer\\aisp_core";
function activate(context) {
    console.log('MemoryBridge AISP Extension is now active!');
    let initDisposable = vscode.commands.registerCommand('aisp.initSession', () => {
        const workspaceFolders = vscode.workspace.workspaceFolders;
        if (!workspaceFolders) {
            vscode.window.showErrorMessage('No workspace open to initialize AISP.');
            return;
        }
        const workspacePath = workspaceFolders[0].uri.fsPath;
        const aispDir = path.join(workspacePath, '.ai-session');
        if (fs.existsSync(aispDir)) {
            vscode.window.showInformationMessage('AISP Session already exists in this workspace.');
            return;
        }
        vscode.window.showInformationMessage('Initializing MemoryBridge .ai-session...');
        const pythonScript = path.join(PYTHON_CORE_DIR, "session.py");
        (0, child_process_1.exec)(`python "${pythonScript}" init "${workspacePath}"`, (error, stdout, stderr) => {
            if (error) {
                vscode.window.showErrorMessage('Failed to init: ' + stderr);
            }
            else {
                vscode.window.showInformationMessage('✅ MemoryBridge: Initialized .ai-session perfectly via Python Engine!');
            }
        });
    });
    let generateDisposable = vscode.commands.registerCommand('aisp.generateResume', async () => {
        const workspaceFolders = vscode.workspace.workspaceFolders;
        if (!workspaceFolders)
            return;
        const workspacePath = workspaceFolders[0].uri.fsPath;
        const options = [
            { label: '🧠 Zero-Token Bloat (AST Struct)', description: 'Deterministic AST extraction. 90% fewer tokens.' },
            { label: '📝 Basic Context', description: 'Lightweight prompt (Tasks, Cursors)' },
            { label: '💻 Full Code Context', description: 'Includes recent file source code in the prompt' },
            { label: '📦 Export ZIP Package', description: 'Creates a .zip of the entire session to upload' }
        ];
        const selection = await vscode.window.showQuickPick(options, { placeHolder: 'Select AISP Resume Strategy' });
        if (!selection)
            return;
        let mode = "basic";
        if (selection.label.includes('Zero-Token'))
            mode = "ast";
        if (selection.label.includes('Full Code'))
            mode = "full";
        if (selection.label.includes('Export ZIP'))
            mode = "zip";
        vscode.window.showInformationMessage(`Executing ${selection.label}...`);
        const pythonScript = path.join(PYTHON_CORE_DIR, "resume.py");
        (0, child_process_1.exec)(`python "${pythonScript}" ${mode} "${workspacePath}"`, (error, stdout, stderr) => {
            if (error) {
                vscode.window.showErrorMessage('Failed to generate prompt: ' + stderr);
                return;
            }
            if (mode === "zip") {
                vscode.window.showInformationMessage(`✅ ZIP Exported successfully to: ${stdout.trim()}`);
            }
            else {
                vscode.env.clipboard.writeText(stdout).then(() => {
                    vscode.window.showInformationMessage('✅ AISP Resume Prompt copied to clipboard!');
                });
            }
        });
    });
    // --- NEW: Set Active Task ---
    let setTaskDisposable = vscode.commands.registerCommand('aisp.setActiveTask', async () => {
        const workspaceFolders = vscode.workspace.workspaceFolders;
        if (!workspaceFolders)
            return;
        const workspacePath = workspaceFolders[0].uri.fsPath;
        const taskDesc = await vscode.window.showInputBox({
            prompt: "What are you currently working on?",
            placeHolder: "e.g., Implementing WebSockets for the chat panel"
        });
        if (!taskDesc)
            return; // User cancelled
        const pythonScript = path.join(PYTHON_CORE_DIR, "session.py");
        (0, child_process_1.exec)(`python "${pythonScript}" task "${workspacePath}" "${taskDesc}"`, (error, stdout, stderr) => {
            if (error) {
                vscode.window.showErrorMessage('Failed to set task: ' + stderr);
            }
            else {
                vscode.window.showInformationMessage(`✅ AISP Task Updated: ${taskDesc}`);
            }
        });
    });
    // Listen to file saves to trigger the Snapshot Engine
    vscode.workspace.onDidSaveTextDocument((document) => {
        const workspaceFolders = vscode.workspace.workspaceFolders;
        if (!workspaceFolders)
            return;
        const workspacePath = workspaceFolders[0].uri.fsPath;
        const aispDir = path.join(workspacePath, '.ai-session');
        if (fs.existsSync(aispDir)) {
            const pythonScript = path.join(PYTHON_CORE_DIR, "snapshot.py");
            const relativePath = path.relative(workspacePath, document.uri.fsPath);
            console.log(`[MemoryBridge] Snapshotting file: ${relativePath}`);
            // Execute the Python snapshot engine to perfectly save the diff and log the event
            (0, child_process_1.exec)(`python "${pythonScript}" save "${workspacePath}" "${relativePath}"`, (error, stdout, stderr) => {
                if (error) {
                    console.error('MemoryBridge Snapshot failed: ' + stderr);
                }
                else {
                    console.log('MemoryBridge Snapshot successful: ' + stdout);
                }
            });
        }
    });
    // --- NEW: Track Active Tab and Cursor Position ---
    vscode.window.onDidChangeActiveTextEditor(editor => {
        if (editor)
            updateEditorState(editor);
    });
    vscode.window.onDidChangeTextEditorSelection(event => {
        updateEditorState(event.textEditor);
    });
    function updateEditorState(editor) {
        const workspaceFolders = vscode.workspace.workspaceFolders;
        if (!workspaceFolders)
            return;
        const workspacePath = workspaceFolders[0].uri.fsPath;
        const aispDir = path.join(workspacePath, '.ai-session');
        if (fs.existsSync(aispDir)) {
            const editorJsonPath = path.join(aispDir, 'state', 'editor.json');
            const relativePath = path.relative(workspacePath, editor.document.uri.fsPath);
            const currentLine = editor.selection.active.line + 1; // 1-indexed
            const state = {
                active_file: relativePath,
                cursor_position: { line: currentLine },
                open_tabs: vscode.workspace.textDocuments.map(doc => path.relative(workspacePath, doc.uri.fsPath))
            };
            try {
                if (fs.existsSync(path.dirname(editorJsonPath))) {
                    fs.writeFileSync(editorJsonPath, JSON.stringify(state, null, 2));
                }
            }
            catch (e) {
                // Ignore silent write errors
            }
        }
    }
    context.subscriptions.push(initDisposable, generateDisposable, setTaskDisposable);
}
function deactivate() { }
//# sourceMappingURL=extension.js.map