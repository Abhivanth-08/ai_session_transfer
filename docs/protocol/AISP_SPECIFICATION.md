# AI Session Protocol (AISP) Specification v1.0

## 1. Introduction
The **AI Session Protocol (AISP)** is an open, standardized specification designed to facilitate the seamless transfer of AI-assisted software development sessions across different IDEs (VS Code, Cursor, Windsurf, Roo Code) and LLMs (Claude, ChatGPT, Gemini). 

AISP ensures that project context, conversation history, and workspace state are perfectly preserved, eliminating the need for AI models to regenerate existing code or re-establish context when a user switches platforms.

## 2. Core Principles
1. **Local-First & Privacy-Focused**: Data resides locally by default. Cloud sync is optional and E2E encrypted.
2. **Incremental Snapshots**: Only delta changes (diffs) are captured to minimize storage and transmission overhead.
3. **Agnostic Architecture**: Independent of any specific LLM, IDE, or vendor.
4. **Deterministic Resume**: An AI model can perfectly resume a task based on the compressed session state without replaying the entire conversation.

---

## 3. The `.aisession` Format

A project supporting AISP contains an `.ai-session/` directory (or a compressed `.aisession` archive) at its root. 

### 3.1 Directory Structure
```text
.ai-session/
├── metadata.json          # Global session metadata, session ID, timestamps
├── workspace/             # Compressed snapshots of the source code
│   ├── base.tar.gz        # Initial baseline snapshot
│   └── diffs/             # Incremental patch files (git-style deltas)
├── history/               # Immutable event logs and state timelines
│   ├── events.jsonl       # Every meaningful event (keystrokes, commands, file saves)
│   └── chat.json          # Standardized conversation history (Prompts & Responses)
├── state/
│   ├── terminal.log       # Terminal output and command history
│   ├── editor.json        # Open files, cursor positions, active tabs
│   └── environment.json   # Dependencies, OS info, package manager state
├── tasks/                 
│   └── graph.json         # Pending, completed, and current tasks
├── cache/                 # Deterministic AST and dependency graph analysis
└── local.db               # SQLite database for fast local querying and indexing
```

### 3.2 Key File Specifications

#### `metadata.json`
```json
{
  "aisp_version": "1.0",
  "session_id": "uuid-v4",
  "project_name": "MemoryBridge",
  "created_at": "2026-06-27T19:16:20Z",
  "last_updated": "2026-06-27T20:00:00Z",
  "primary_language": "python",
  "sync_mode": "local_only"
}
```

#### `tasks/graph.json`
Represents the current AI objective to prevent context loss.
```json
{
  "current_task": {
    "id": "task-102",
    "description": "Implement authentication middleware",
    "status": "in_progress",
    "relevant_files": ["backend/auth.py", "backend/main.py"]
  },
  "completed_tasks": ["task-101"],
  "pending_tasks": ["task-103", "task-104"]
}
```

#### `state/editor.json`
```json
{
  "active_file": "backend/auth.py",
  "cursor_position": {"line": 42, "column": 12},
  "open_tabs": [
    "backend/auth.py",
    "backend/models.py"
  ]
}
```

---

## 4. Snapshot & Diff Strategy

AISP does not store full copies of the project for every change. It uses **Incremental Snapshots**.

1. **Baseline (`workspace/base.tar.gz`)**: Created when AISP is initialized. Contains the full project state excluding ignored files (`.gitignore`, `node_modules`, etc.).
2. **Event Trigger**: When a meaningful action occurs (AI response generated, user saves a file).
3. **Diff Generation (`workspace/diffs/`)**: An optimized diff patch is created against the current state.
4. **Compression**: Uses Zstandard (zstd) for ultra-fast compression of textual code data.

---

## 5. Sync & Resume Protocols

### 5.1 Sync Protocol
When syncing to the cloud (Mode 2/3), AISP defines a REST-based synchronization protocol.
- `POST /api/v1/sessions/{id}/sync`: Uploads new diffs and events appended to `events.jsonl`.
- `GET /api/v1/sessions/{id}/state`: Retrieves the latest `metadata.json` hash to check for divergence.

### 5.2 Resume Protocol
When opening an `.aisession` in a new IDE or AI tool, the Resume Engine executes:
1. **Validation**: Checks `aisp_version` and metadata.
2. **Reconstruction**: Applies `base.tar.gz` and applies all patches in `workspace/diffs/` sequentially.
3. **Context Hydration**: 
   - Restores editor tabs and cursor positions from `editor.json`.
   - Injects the `current_task` into the LLM's system prompt.
   - Generates a "Resume Summary" (compressed project state) rather than sending the entire chat history.

### 5.3 Optimal Resume Summary (LLM Prompt Injection)
Instead of feeding 100,000 tokens of chat history to the new model, AISP generates a compressed context block:
```markdown
# AISP Resume Context
**Project**: MemoryBridge
**Architecture**: FastAPI Backend, React Frontend
**Current Task**: Implement authentication middleware (in progress)
**Modified Files (Last 10 mins)**: `backend/auth.py`
**Active Errors**: `ImportError: cannot import name 'JWT' from 'jose'`
**Cursor Location**: `backend/auth.py:42`

*Continue resolving the active error to complete the current task.*
```

## 6. Extensibility
The AISP specification allows for custom vendor extensions inside a `.ai-session/vendor/` directory, ensuring IDEs can store proprietary UI states without breaking the core protocol interoperability.
