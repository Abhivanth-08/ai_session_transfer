import json
import os
import uuid
import datetime
from pathlib import Path

class AISessionManager:
    """
    Core implementation of the AI Session Protocol (AISP) v1.0.
    Handles the creation, reading, and structural integrity of an .aisession.
    """
    
    def __init__(self, workspace_path: str):
        self.workspace_path = Path(workspace_path)
        self.aisp_dir = self.workspace_path / ".ai-session"
        
    def initialize_session(self, project_name: str, language: str):
        """Creates the .aisession folder structure and baseline metadata."""
        if self.aisp_dir.exists():
            raise FileExistsError("AISP Session already exists in this workspace.")
            
        dirs_to_create = [
            "workspace/diffs",
            "history",
            "state",
            "tasks",
            "cache"
        ]
        
        for d in dirs_to_create:
            (self.aisp_dir / d).mkdir(parents=True, exist_ok=True)
            
        metadata = {
            "aisp_version": "1.0",
            "session_id": str(uuid.uuid4()),
            "project_name": project_name,
            "created_at": datetime.datetime.utcnow().isoformat() + "Z",
            "last_updated": datetime.datetime.utcnow().isoformat() + "Z",
            "primary_language": language,
            "sync_mode": "local_only"
        }
        
        self._write_json("metadata.json", metadata)
        
        # Initialize default state files
        self._write_json("state/editor.json", {"active_file": None, "cursor_position": None, "open_tabs": []})
        self._write_json("tasks/graph.json", {"current_task": None, "completed_tasks": [], "pending_tasks": []})
        
        # Initialize event log
        (self.aisp_dir / "history/events.jsonl").touch()
        
        return metadata

    def log_event(self, event_type: str, payload: dict):
        """Appends an immutable event to the session history."""
        event = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "type": event_type,
            "payload": payload
        }
        
        with open(self.aisp_dir / "history/events.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\n")
            
        self._update_timestamp()

    def update_task(self, task_desc: str, relevant_files: list):
        """Updates the current task graph to provide context for the Resume Engine."""
        graph = self._read_json("tasks/graph.json")
        graph["current_task"] = {
            "id": f"task-{uuid.uuid4().hex[:8]}",
            "description": task_desc,
            "status": "in_progress",
            "relevant_files": relevant_files
        }
        self._write_json("tasks/graph.json", graph)
        self._update_timestamp()

    def _write_json(self, rel_path: str, data: dict):
        with open(self.aisp_dir / rel_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def _read_json(self, rel_path: str) -> dict:
        with open(self.aisp_dir / rel_path, "r", encoding="utf-8") as f:
            return json.load(f)
            
    def _update_timestamp(self):
        metadata = self._read_json("metadata.json")
        metadata["last_updated"] = datetime.datetime.utcnow().isoformat() + "Z"
        self._write_json("metadata.json", metadata)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 2 and sys.argv[1] == "init":
        workspace_dir = sys.argv[2]
        manager = AISessionManager(workspace_dir)
        try:
            manager.initialize_session(Path(workspace_dir).name, "unknown")
            print(f"Session initialized successfully in {workspace_dir}")
        except FileExistsError:
            print("AISP Session already exists.")
    elif len(sys.argv) > 3 and sys.argv[1] == "task":
        workspace_dir = sys.argv[2]
        task_desc = sys.argv[3]
        manager = AISessionManager(workspace_dir)
        manager.update_task(task_desc)
        print(f"Task updated successfully to: {task_desc}")

# Example Usage:
# if __name__ == "__main__":
#     manager = AISessionManager("./sample_project")
#     manager.initialize_session("NextGenApp", "typescript")
#     manager.log_event("prompt", {"text": "Add a login button"})
#     manager.update_task("Implement OAuth2 authentication", ["src/auth.ts"])
