import os
import json
import getpass
from pathlib import Path
from google import genai
from google.genai import types

def _ensure_api_key():
    """
    Checks if GEMINI_API_KEY is in the environment.
    If not, checks the .env file.
    If still not found, prompts the user and saves it.
    """
    env_path = Path(__file__).parent.parent / ".env"
    
    # Manually load from .env if it exists
    if not os.getenv("GEMINI_API_KEY") and env_path.exists():
        with open(env_path, "r") as f:
            for line in f:
                if line.startswith("GEMINI_API_KEY="):
                    os.environ["GEMINI_API_KEY"] = line.strip().split("=", 1)[1]

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("\n[MemoryBridge] Generative AI features require a Gemini API Key.")
        api_key = getpass.getpass("Please paste your GEMINI_API_KEY (input is hidden): ").strip()
        
        if not api_key:
            raise ValueError("API Key cannot be empty.")
            
        # Set it in the current process environment
        os.environ["GEMINI_API_KEY"] = api_key
        
        # Save it to .env so the user doesn't have to type it again
        env_path = Path(__file__).parent.parent / ".env"
        with open(env_path, "a") as f:
            f.write(f"\nGEMINI_API_KEY={api_key}\n")
        print(f"✅ Saved to {env_path} for future sessions.\n")

class SemanticContextCompressor:
    """
    Transforms raw AISP Session data into intelligent summaries using Generative AI.
    """
    def __init__(self, workspace_path: str):
        _ensure_api_key()
        self.workspace_path = Path(workspace_path)
        self.aisp_dir = self.workspace_path / ".ai-session"
        self.client = genai.Client() 
        self.model = 'gemini-2.5-flash'

    def compress_session_history(self) -> str:
        events_path = self.aisp_dir / "history/events.jsonl"
        tasks_path = self.aisp_dir / "tasks/graph.json"
        
        raw_events = []
        if events_path.exists():
            with open(events_path, "r") as f:
                lines = f.readlines()[-20:] 
                raw_events = [json.loads(line) for line in lines]
                
        tasks = {}
        if tasks_path.exists():
            with open(tasks_path, "r") as f:
                tasks = json.load(f)

        system_instruction = """
        You are an elite Staff Software Engineer. Your job is to analyze the raw telemetry 
        and event logs of another developer's AI-assisted coding session. 
        You must compress this raw data into a dense, highly actionable summary.
        Focus on:
        1. What bug or feature they were just working on.
        2. What the very next logical step is.
        3. Any errors they were actively fighting.
        """
        prompt_data = f"Task State: {json.dumps(tasks)}\nRecent Events: {json.dumps(raw_events)}"

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt_data,
            config=types.GenerateContentConfig(system_instruction=system_instruction, temperature=0.2)
        )
        summary = response.text
        
        summary_path = self.aisp_dir / "state/ai_summary.md"
        summary_path.parent.mkdir(exist_ok=True, parents=True)
        with open(summary_path, "w") as f:
            f.write(summary)
            
        return summary


class ProactivePredictor:
    """
    Monitors recent errors and file saves to proactively predict the next step 
    and write the code for it before the user asks.
    """
    def __init__(self, workspace_path: str):
        _ensure_api_key()
        self.client = genai.Client()
        self.model = 'gemini-2.5-flash'

    def predict_and_fix(self, recent_error: str, broken_code_snippet: str) -> str:
        system_instruction = """
        You are an autonomous AI pair programmer. The user just encountered an error.
        Do not explain the error. Only provide the exact code block required to fix it 
        so we can instantly load it into the user's IDE.
        """
        prompt_data = f"Error: {recent_error}\nCode:\n```\n{broken_code_snippet}\n```"
        
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt_data,
            config=types.GenerateContentConfig(system_instruction=system_instruction, temperature=0.1)
        )
        return response.text


class LLMWikiEngine:
    """
    Instead of using RAG (Vector Embeddings/Cosine Similarity), this engine maintains 
    a living 'Wiki' document. Every time the project state changes significantly, 
    the LLM updates the Markdown Wiki. When the user asks a question, the LLM reads 
    the Wiki as its sole source of truth.
    """
    def __init__(self, workspace_path: str):
        _ensure_api_key()
        self.workspace_path = Path(workspace_path)
        self.wiki_path = self.workspace_path / ".ai-session/state/llm_wiki.md"
        self.client = genai.Client()
        self.model = 'gemini-2.5-flash' # Switched to flash to avoid free-tier rate limits

    def update_wiki(self, diff_content: str, commit_message: str):
        """Updates the living documentation with recent changes."""
        current_wiki = ""
        if self.wiki_path.exists():
            with open(self.wiki_path, "r") as f:
                current_wiki = f.read()

        system_instruction = """
        You are maintaining a living architecture wiki for a software project.
        You will be given the CURRENT WIKI, and a NEW DIFF representing a code change.
        Your job is to rewrite the CURRENT WIKI to incorporate the new knowledge.
        Keep it structured, highly detailed, and omit nothing important.
        """
        
        prompt_data = f"CURRENT WIKI:\n{current_wiki}\n\nNEW DIFF ({commit_message}):\n{diff_content}"
        
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt_data,
            config=types.GenerateContentConfig(system_instruction=system_instruction, temperature=0.2)
        )
        
        self.wiki_path.parent.mkdir(exist_ok=True, parents=True)
        with open(self.wiki_path, "w") as f:
            f.write(response.text)

    def chat_with_wiki(self, user_question: str) -> str:
        """Answers questions deterministically based ONLY on the living wiki."""
        if not self.wiki_path.exists():
            return "The LLM Wiki has not been initialized yet."
            
        with open(self.wiki_path, "r") as f:
            wiki_content = f.read()
            
        system_instruction = """
        You are a project historian. Answer the user's question using ONLY the provided 
        Project Wiki context. If the wiki does not contain the answer, say you don't know.
        """
        
        prompt_data = f"PROJECT WIKI:\n{wiki_content}\n\nUSER QUESTION: {user_question}"
        
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt_data,
            config=types.GenerateContentConfig(system_instruction=system_instruction, temperature=0.1)
        )
        return response.text
