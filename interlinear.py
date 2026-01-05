import sys
import os
import time
from google import genai
from google.genai import types

# --- 1. CONFIGURATION ---
API_KEY = "PASTE_YOUR_API_KEY_HERE"
MODEL_ID = "gemini-2.0-flash-lite"

client = genai.Client(api_key=API_KEY)

def run_translation(epub_path):
    if not epub_path.lower().endswith(".epub"):
        print(f"[!] Error: {os.path.basename(epub_path)} is not an EPUB file.")
        return

    # --- THROTTLING & ERROR CORRECTION SETTINGS ---
    MAX_RETRIES = 5           # How many times to try a failed segment
    BASE_DELAY = 10           # Seconds to wait after a 429 error
    MIN_PACING_DELAY = 5      # Mandatory wait between requests to stay under 15 RPM
    
    try:
        print(f"[*] File: {os.path.basename(epub_path)}")
        
        # Step A: Upload (Files API is very stable)
        print("[*] Uploading to Google Cloud...")
        book_file = client.files.upload(file=epub_path)
        
        # Step B: Translation with Error Correction Loop
        print("[*] Beginning translation. Please wait...")
        
        attempt = 0
        while attempt < MAX_RETRIES:
            try:
                # Mandatory Pacing: Ensures we don't exceed 15 requests per minute
                time.sleep(MIN_PACING_DELAY)
                
                response = client.models.generate_content(
                    model=MODEL_ID,
                    config=types.GenerateContentConfig(
                        system_instruction="You are a professional literary translator. Translate this book into English prose.",
                        temperature=0.3,
                    ),
                    contents=[book_file, "Translate this book to English."]
                )
                
                # If we get here, the request was successful
                output_file = os.path.splitext(epub_path)[0] + "_Translated.txt"
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(response.text)
                
                print(f"[SUCCESS] Translation saved to Desktop.")
                return # Exit the function successfully

            except Exception as e:
                error_str = str(e)
                attempt += 1
                
                if "429" in error_str:
                    # This is the Throttling Logic
                    wait_time = BASE_DELAY * (2 ** (attempt - 1)) # Exponential backoff
                    print(f"\n[!] Rate Limit (429) Hit. Throttling active...")
                    print(f"[*] Waiting {wait_time} seconds before Retry {attempt}/{MAX_RETRIES}...")
                    time.sleep(wait_time)
                else:
                    # This is for non-quota errors (Xfinity hiccups, etc.)
                    print(f"\n[!] Unexpected Error: {e}")
                    print(f"[*] Retrying in 5 seconds...")
                    time.sleep(5)

        print("\n[FAIL] Maximum retries reached. The book might be too large for a single pass.")

    except Exception as e:
        print(f"\n[!] Critical Startup Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_translation(sys.argv[1])
    else:
        print("[!] No file path detected.")

