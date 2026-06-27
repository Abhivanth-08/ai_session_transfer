import os
import tarfile
import hashlib
import time
import shutil
from pathlib import Path
import json

class WorkspaceSnapshotEngine:
    """
    Handles creating incremental snapshots and base tarballs for the AISP protocol.
    For production, this would use Zstandard (zstd) and binary delta compression.
    Here we implement a prototype baseline + full file copy for diffs.
    """
    
    def __init__(self, workspace_path: str):
        self.workspace_path = Path(workspace_path)
        self.aisp_dir = self.workspace_path / ".ai-session"
        self.workspace_snapshot_dir = self.aisp_dir / "workspace"
        
        # Ignored paths
        self.ignore_dirs = {".ai-session", ".git", "node_modules", "__pycache__", "venv"}

    def _should_ignore(self, path: Path) -> bool:
        for parent in path.parents:
            if parent.name in self.ignore_dirs:
                return True
        return path.name in self.ignore_dirs

    def create_baseline(self):
        """Creates the initial base.tar.gz"""
        base_tar_path = self.workspace_snapshot_dir / "base.tar.gz"
        
        with tarfile.open(base_tar_path, "w:gz") as tar:
            for root, dirs, files in os.walk(self.workspace_path):
                # Filter dirs in-place
                dirs[:] = [d for d in dirs if not self._should_ignore(Path(root) / d)]
                
                for file in files:
                    file_path = Path(root) / file
                    if not self._should_ignore(file_path):
                        arcname = file_path.relative_to(self.workspace_path)
                        tar.add(file_path, arcname=arcname)
        
        return base_tar_path

    def snapshot_file_change(self, file_path: str):
        """
        Called when a file is modified. Saves the diff snapshot.
        Prototype: saves a full copy of the modified file into the diffs folder.
        """
        abs_path = self.workspace_path / file_path
        if not abs_path.exists():
            return
            
        timestamp = int(time.time())
        diff_name = f"{timestamp}_{abs_path.name}"
        diff_dest = self.workspace_snapshot_dir / "diffs" / diff_name
        
        shutil.copy2(abs_path, diff_dest)
        
        # Record this diff in metadata
        patch_info = {
            "timestamp": timestamp,
            "original_path": file_path,
            "patch_file": diff_name
        }
        
        
        # Log to events
        from .session import AISessionManager
        manager = AISessionManager(str(self.workspace_path))
        manager.log_event("file_snapshot", patch_info)
        
        return patch_info

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 3 and sys.argv[1] == "save":
        workspace_dir = sys.argv[2]
        file_path = sys.argv[3]
        engine = WorkspaceSnapshotEngine(workspace_dir)
        engine.snapshot_file_change(file_path)
        print(f"Snapshot created for {file_path}")
