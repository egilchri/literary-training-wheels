import sys, os, time, ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
from google import genai

# --- 1. CONFIGURATION ---
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
    
    # --- 2. UPDATED EXTRACTION LOGIC ---
    # We no longer flatten the text. We preserve paragraph boundaries.
    chapters = []
    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        soup = BeautifulSoup(item.get_content(), 'html.parser')
        
        # Standardize paragraph extraction to keep structure
        paras = soup.find_all(['p', 'div'])
        if paras:
            # Join paragraphs with a temporary single newline
            text_block = "\n".join([p.get_text().strip() for p in paras if p.get_text().strip()])
        else:
            text_block = soup.get_text().strip()
            
        if len(text_block) > 30:
            chapters.append(text_block)

    output_file = os.path.splitext(epub_path)[0] + "_Bilingual.txt"
    
    end_section = min(start_section + limit, len(chapters)) if limit else len(chapters)
    print(f"[*] Resuming from Section {start_section + 1}...")

    for i in range(start_section, end_section):
        # --- 3. ORIGINAL TEXT FORMATTING ---
        # Apply the 'Strip and Join' filter to the original text
        orig_lines = chapters[i].split('\n')
        formatted_original = "\n\n".join([line.strip() for line in orig_lines if line.strip()])
        
        time.sleep(20) # Pacing for API limits
        
        print(f"[*] Section {i+1}/{len(chapters)}: Translating...", end=" ", flush=True)
        try:
            response = client.models.generate_content(
                model=MODEL_ID,
                config={'system_instruction': "Translate this 19th-century prose into clear, contemporary English. Maintain emotional weight but use modern sentence structures."},
                contents=formatted_original[:12000]
            )
            
            # --- 4. TRANSLATED TEXT FORMATTING ---
            # Apply the same filter to the Gemini translation
            trans_lines = response.text.strip().split('\n')
            formatted_translation = "\n\n".join([line.strip() for line in trans_lines if line.strip()])
            
            with open(output_file, "a", encoding="utf-8") as f:
                # WRITE ORIGINAL with fixed spacing
                f.write(f"\n<div class='original-text justify-text'>\n")
                f.write(f"### SECTION {i+1} ORIGINAL\n")
                f.write(formatted_original + "\n")
                f.write(f"</div>\n")
                   
                # WRITE TRANSLATION with fixed spacing
                f.write(f"\n<details class='modern-translation'>\n")
                f.write(f"  <summary>Click to show contemporary translation</summary>\n")
                f.write(f"  <div class='translation-content'>\n")
                f.write(f"    <i>{formatted_translation}</i>\n") 
                f.write(f"  </div>\n")
                f.write(f"</details>\n")
                f.write(f"\n{'='*40}\n")
                f.flush()
                os.fsync(f.fileno())

            with open(PROGRESS_FILE, "w") as f:
                f.write(str(i + 1))
            print(f"Done.")
            
        except Exception as e:
            print(f"Error: {e}")
            return

if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_interleaved_translation(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else None)
    else:
        print("[!] Usage: python3 translate_epub.py [BOOK_PATH] [OPTIONAL_LIMIT]")

