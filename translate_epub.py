import sys, os, time, ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
from google import genai

# --- 1. CONFIGURATION ---
# Ensure your GEMINI_API_KEY is set in your Mac's environment variables
API_KEY = os.environ.get("GEMINI_API_KEY")
MODEL_ID = "gemini-2.0-flash-lite"
PROGRESS_FILE = ".translation_progress"

client = genai.Client(api_key=API_KEY)

def run_interleaved_translation(epub_path, limit=None):
    start_section = 0
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r") as f:
            start_section = int(f.read().strip())

    book = epub.read_epub(epub_path)
    
    # --- 2. TAG-PRESERVED EXTRACTION ---
    # Instead of stripping HTML, we keep the <p> tags to maintain the author's structure
    chapters = []
    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        soup = BeautifulSoup(item.get_content(), 'html.parser')
        # Find all actual paragraph elements
        paras = soup.find_all('p')
        if paras:
            # Join the actual HTML strings of the paragraphs
            text_block = "\n".join([str(p) for p in paras])
            if len(text_block) > 30:
                chapters.append(text_block)

    output_file = os.path.splitext(epub_path)[0] + "_Bilingual.txt"
    
    # Determine the end point based on the optional limit
    end_section = len(chapters)
    if limit:
        end_section = min(start_section + limit, len(chapters))
        print(f"[*] LIMIT ACTIVE: Processing {limit} sections.")

    print(f"[*] Resuming from Section {start_section + 1}...")

    for i in range(start_section, end_section):
        original_html_chunk = chapters[i]
        
        # Strip tags ONLY for the AI prompt so the model focuses on words, not code
        text_for_ai = BeautifulSoup(original_html_chunk, 'html.parser').get_text()
        
        time.sleep(20) # Pacing for Gemini Free Tier (3 RPM)
        
        print(f"[*] Section {i+1}/{len(chapters)}: Translating...", end=" ", flush=True)
        try:
            response = client.models.generate_content(
                model=MODEL_ID,
                config={'system_instruction': "You are a professional translator. Translate this 19th-century literary prose into clear, contemporary English. Maintain the emotional weight but use modern sentence structures and paragraphing."},
                contents=text_for_ai[:12000]
            )
            
            # --- 3. FORMAT TRANSLATION WITH PARAGRAPHS ---
            # Turn Gemini's line breaks into proper EPUB paragraph tags
            trans_lines = response.text.strip().split('\n')
            formatted_translation = "".join([f"<p>{l.strip()}</p>" for l in trans_lines if l.strip()])
            
            with open(output_file, "a", encoding="utf-8") as f:
                # WRITE THE ORIGINAL (Keeping its original <p> tags)
                f.write(f"\n<div class='original-text justify-text'>\n")
                f.write(f"### SECTION {i+1} ORIGINAL\n")
                f.write(original_html_chunk + "\n")
                f.write(f"</div>\n")
                   
                # WRITE THE TRANSLATION (Using our new <p> tags)
                f.write(f"\n<details class='modern-translation'>\n")
                f.write(f"  <summary>Click to show contemporary translation</summary>\n")
                f.write(f"  <div class='translation-content'>\n")
                f.write(f"    <i>{formatted_translation}</i>\n") 
                f.write(f"  </div>\n")
                f.write(f"</details>\n")
                f.write(f"\n{'='*40}\n")
                f.flush()
                os.fsync(f.fileno())

            # Update progress
            with open(PROGRESS_FILE, "w") as f:
                f.write(str(i + 1))
            
            print(f"Done.")
            
        except Exception as e:
            if "429" in str(e):
                print("\n[!] QUOTA EXHAUSTED.")
                return
            print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        path = sys.argv[1]
        # Handle optional limit argument
        section_limit = int(sys.argv[2]) if len(sys.argv) > 2 else None
        run_interleaved_translation(path, section_limit)
    else:
        print("[!] Usage: python3 translate_epub.py [BOOK_PATH] [OPTIONAL_LIMIT]")

