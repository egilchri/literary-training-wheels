import sys, os, time, ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
from google import genai

# --- 1. SECURE CONFIGURATION ---
API_KEY = os.environ.get("GEMINI_API_KEY")
MODEL_ID = "gemini-2.0-flash-lite"

if not API_KEY:
    print("[!] ERROR: GEMINI_API_KEY not found. Run 'source ~/.zshrc' first.")
    sys.exit()

client = genai.Client(api_key=API_KEY)

def run_single_test(epub_path):
    print(f"[*] Starting Single-Section Test: {os.path.basename(epub_path)}")
    
    try:
        # Extract the text
        book = epub.read_epub(epub_path)
        chapters = []
        for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
            soup = BeautifulSoup(item.get_content(), 'html.parser')
            text = soup.get_text().strip()
            if len(text) > 100: # Ensure it's a real chapter, not just a title
                chapters.append(text)

        if not chapters:
            print("[!] Could not find any significant text sections.")
            return

        # Process ONLY the first section
        first_section = chapters[0]
        print(f"[*] Sending Section 1 ({len(first_section)} characters) to Gemini...")
        
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=first_section[:12000] # Safe chunk size
        )
        
        # Display and Save the result
        print("\n" + "="*30)
        print("TRANSLATION PREVIEW:")
        print("="*30)
        print(response.text[:500] + "...") # Show the first 500 characters
        print("="*30)
        
        output_file = "TEST_OUTPUT.txt"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(response.text)
            f.flush()
            os.fsync(f.fileno())
            
        print(f"\n[SUCCESS] Full section saved to {output_file}")
        print("[*] If this look good, you are ready for the full book!")

    except Exception as e:
        print(f"\n[!] Error: {e}")

if __name__ == "__main__":
    # Change this path to your book's location
    BOOK_PATH = "/Users/edgargilchrist/tools/BookTranslator/TurnOfTheScrew.epub"
    run_single_test(BOOK_PATH)

