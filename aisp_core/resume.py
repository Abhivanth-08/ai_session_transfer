import json
from pathlib import Path

class ResumeEngine:
    """
    Parses the .aisession folder and generates a compressed, optimal
    context prompt for a new LLM to pick up the session.
    """
    
    def __init__(self, workspace_path: str):
        self.workspace_path = Path(workspace_path)
        self.aisp_dir = self.workspace_path / ".ai-session"
        
    def _read_json(self, rel_path: str):
        file_path = self.aisp_dir / rel_path
        if not file_path.exists():
            return {}
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def generate_resume_prompt(self) -> str:
        """
        Generates the Context Hydration Prompt for the AI.
        """
        metadata = self._read_json("metadata.json")
        graph = self._read_json("tasks/graph.json")
        state = self._read_json("state/editor.json")
        
        project_name = metadata.get("project_name", "Unknown Project")
        lang = metadata.get("primary_language", "unknown")
        
        current_task = graph.get("current_task")
        task_desc = current_task.get("description", "No active task.") if current_task else "No active task."
        relevant_files = current_task.get("relevant_files", []) if current_task else []
        
        active_file = state.get("active_file", "None")
        cursor = state.get("cursor_position", {})
        cursor_line = cursor.get("line", "Unknown")
        
        prompt = f"""# AISP Resume Context (MemoryBridge)

**Project Name**: {project_name}
**Primary Language**: {lang}

## Current Objective
{task_desc}

## Relevant Files for Task
{', '.join(relevant_files) if relevant_files else 'None defined'}

## Editor State
**Active File**: `{active_file}`
**Cursor Position**: Line {cursor_line}

---
*INSTRUCTION FOR AI: You have been restored into this session. Please analyze the 'Current Objective' and the 'Active File', and continue the implementation seamlessly. Do not regenerate existing codebase scaffolding.*
"""
        return prompt

    def generate_full_code_prompt(self) -> str:
        """Generates the basic prompt but appends the actual source code of recently modified files."""
        prompt = self.generate_resume_prompt()
        prompt += "\n## Recent Code Context\n"
        
        diffs_dir = self.aisp_dir / "workspace" / "diffs"
        if diffs_dir.exists():
            # Get the last 5 modified files
            recent_files = sorted(list(diffs_dir.iterdir()), key=lambda x: x.stat().st_mtime, reverse=True)[:5]
            for f in recent_files:
                if f.is_file():
                    try:
                        content = f.read_text(encoding='utf-8')
                        prompt += f"\n### Modified File: {f.name}\n```\n{content}\n```\n"
                    except Exception:
                        pass
        return prompt

    def export_zip(self) -> str:
        """Packages the entire .ai-session database and code diffs into a ZIP for Claude/GPT uploads."""
        import zipfile
        import os
        zip_path = self.workspace_path / "aisp_session_export.zip"
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(self.aisp_dir):
                for file in files:
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(self.workspace_path)
                    zipf.write(file_path, arcname=str(arcname))
        return str(zip_path)

if __name__ == "__main__":
    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else "basic"
    workspace = sys.argv[2] if len(sys.argv) > 2 else "."
    
    engine = ResumeEngine(workspace)
    
    if mode == "basic":
        print(engine.generate_resume_prompt())
    elif mode == "full":
        print(engine.generate_full_code_prompt())
    elif mode == "zip":
        print(engine.export_zip())
