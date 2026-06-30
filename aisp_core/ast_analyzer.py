import ast
from pathlib import Path

class TokenOptimizedDistiller:
    """
    Solves the Token Bloat problem.
    Instead of passing full files or relying on LLMs to summarize (which itself costs tokens),
    this deterministically parses the Abstract Syntax Tree (AST) to extract only the 
    architectural skeleton (Classes, Functions, Signatures).
    
    This compresses project context by up to 90% while retaining perfect architectural knowledge 
    so the new LLM knows exactly how the project is structured without reading the implementation details.
    """
    def __init__(self, workspace_path: str):
        self.workspace = Path(workspace_path)

    def distill_file(self, file_path: Path) -> str:
        if not file_path.suffix == '.py':
            return "" # Currently optimized for Python in this prototype

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                code = f.read()
            tree = ast.parse(code)
        except Exception:
            return ""

        skeleton = [f"### File: {file_path.relative_to(self.workspace)}"]
        
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                skeleton.append(f"class {node.name}:")
                for sub_node in node.body:
                    if isinstance(sub_node, ast.FunctionDef):
                        args = [a.arg for a in sub_node.args.args]
                        skeleton.append(f"    def {sub_node.name}({', '.join(args)}): ...")
            elif isinstance(node, ast.FunctionDef):
                args = [a.arg for a in node.args.args]
                skeleton.append(f"def {node.name}({', '.join(args)}): ...")
                
        # Only return if we found classes or functions
        if len(skeleton) > 1:
            return "\n".join(skeleton)
        return ""

    def generate_project_skeleton(self) -> str:
        output = ["# 🧠 AST Architectural Context (Zero-Token Bloat)\n"]
        output.append("The following is the deterministic project skeleton. Implementation details are omitted to save context limits.\n")
        
        # Distill all python files except venv
        for f in self.workspace.rglob("*.py"):
            if "venv" in f.parts or "__pycache__" in f.parts or ".ai-session" in f.parts:
                continue
            skeleton = self.distill_file(f)
            if skeleton:
                output.append(skeleton)
                
        return "\n\n".join(output)
