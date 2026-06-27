import os
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic") # Hide annoying library warnings

from gen_ai import LLMWikiEngine, ProactivePredictor, _ensure_api_key

def test_wiki():
    print("--- Testing LLM Wiki Engine ---")
    wiki_engine = LLMWikiEngine("./dummy_workspace")
    
    # 1. Simulate a code commit/diff
    diff_content = """
    + def authenticate_user(token: str):
    +     '''Validates JWT token against the Auth0 provider'''
    +     if not token: raise ValueError("No token provided")
    +     return True
    """
    print("Updating Wiki with new diff...")
    wiki_engine.update_wiki(diff_content, "Added JWT authentication via Auth0")
    
    # 2. Chat with the Wiki
    question = "What provider are we using for user authentication?"
    print(f"\nUser Question: {question}")
    answer = wiki_engine.chat_with_wiki(question)
    print(f"AI Answer: {answer}")


def test_predictor():
    print("\n--- Testing Proactive Predictor ---")
    predictor = ProactivePredictor("./dummy_workspace")
    
    error = "ZeroDivisionError: division by zero"
    code = """
def calculate_average(total_score, num_students):
    return total_score / num_students
    """
    
    print(f"Simulating Error: {error}")
    fix = predictor.predict_and_fix(error, code)
    print(f"Proactive Fix Generated:\n{fix}")


if __name__ == "__main__":
    # Ensure the API key is loaded from the .env file before running
    _ensure_api_key()
    
    test_wiki()
    test_predictor()
