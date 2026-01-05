import os
import sys
import time
from google import genai
from google.genai import types

# --- SECURE CONFIGURATION ---
# This looks into your Mac's "locker" for the key we just saved
API_KEY = os.environ.get("GEMINI_API_KEY")

if not API_KEY:
    print("[!] ERROR: API Key not found in Environment Variables.")
    print("[*] Did you remember to run 'source ~/.zshrc'?")
    sys.exit()

MODEL_ID = "gemini-2.0-flash-lite"

def run_diagnostic():
    print("--- GEMINI API DIAGNOSTIC (2026) ---")
    client = genai.Client(api_key=API_KEY)
    
    try:
        print(f"[*] Testing connection to {MODEL_ID}...")
        
        # We send a tiny 3-word prompt to minimize token usage
        response = client.models.generate_content(
            model=MODEL_ID,
            contents="Say 'System Ready'"
        )
        
        if "System Ready" in response.text:
            print("[SUCCESS] API Key is active and quota is available.")
            print(f"[SUCCESS] Gemini Response: {response.text.strip()}")
            print("\nRESULT: You are cleared to run translate_epub.py")
        else:
            print("[?] API connected, but returned unexpected text.")
            
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg:
            print("\n[!] FAILURE: Quota still exhausted. Check Google Cloud Console.")
        elif "403" in error_msg:
            print("\n[!] FAILURE: API Key invalid or Generative Language API not enabled.")
        else:
            print(f"\n[!] UNEXPECTED ERROR: {error_msg}")

if __name__ == "__main__":
    run_diagnostic()
    
