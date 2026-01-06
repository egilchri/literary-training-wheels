import sys, os, time, ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
from google import genai

# --- CONFIGURATION ---
API_KEY = os.environ.get("GEMINI_API_KEY")
MODEL_ID = "gemini-2.0-flash-lite"
PROGRESS_FILE = ".translation_progress"
client = genai.Client(api_key=API_KEY)

# This is the phrase the script looks for to know the story has actually begun.
# For Wings of the Dove, the first book starts with "She waited, Kate Croy" 
# or a Chapter heading.
STORY_START_TRIGGER = "She waited, Kate Croy" 

def run_interleaved_translation(epub_path, frequency=1, limit=None):
    start_section = 0
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r") as f:
            try:
                start_section = int(f.read().strip())
            except ValueError:
                start_section = 0

    book = epub.read_epub(epub_path)
    
    # --- STEP 1: EXTRACT ELEMENTS (With Start Trigger) ---
    all_elements = []
    has_story_started = False

    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        soup = BeautifulSoup(item.get_content(), 'html.parser')
        elements = soup.find_all(['h1', 'h2', 'h3', 'p'])
        
        for el in elements:
            text = el.get_text().strip()
            
            # Check if we've hit the start of the actual book
            if not has_story_started:
                if STORY_START_TRIGGER.lower() in text.lower() or "BOOK FIRST" in text.upper():
                    has_story_started = True
                else:
                    continue # Skip this element if the story hasn't started yet
            
            if text:
                all_elements.append(el)

    # --- STEP 2: GROUP ELEMENTS BY FREQUENCY ---
    chunks = []
    for i in range(0, len(all_elements), frequency):
        group = all_elements[i:i + frequency]
        text_block = "\n".join([str(el) for el in group])
        if len(text_block.strip()) > 10:
            chunks.append(text_block)

    output_file = os.path.splitext(epub_path)[0] + "_Bilingual.txt"
    end_section = min(start_section + limit, len(chunks)) if limit else len(chunks)

    print(f"[*] Story trigger found. Total narrative chunks: {len(chunks)}")
    print(f"[*] Resuming from Chunk {start_section + 1}...")

    for i in range(start_section, end_section):
        original_html_chunk = chunks[i]
        text_for_ai = BeautifulSoup(original_html_chunk, 'html.parser').get_text()
        
        time.sleep(20) 
        print(f"[*] Chunk {i+1}/{len(chunks)}: Translating...", end=" ", flush=True)
        
        try:
            response = client.models.generate_content(
                model=MODEL_ID,
                config={'system_instruction': "Translate this literary prose into clear, contemporary English. Maintain paragraph structure."},
                contents=text_for_ai[:12000]
            )
            
            trans_lines = response.text.strip().split('\n')
            formatted_translation = "".join([f"<p>{l.strip()}</p>" for l in trans_lines if l.strip()])
            
            with open(output_file, "a", encoding="utf-8") as f:
                f.write(f"\n<div class='original-text justify-text'>\n")
                f.write(f"### SECTION {i+1} ORIGINAL\n")
                f.write(original_html_chunk + "\n")
                f.write(f"</div>\n")
                   
                f.write(f"\n<div class='translation-block'>\n")
                f.write(f"  <span class='translation-label'>Contemporary Translation</span>\n")
                f.write(f"  <div class='translation-content'>\n")
                f.write(f"    <i>{formatted_translation}</i>\n") 
                f.write(f"  </div>\n")
                f.write(f"</div>\n")
                f.write(f"\n========================================\n")
                f.flush()

            with open(PROGRESS_FILE, "w") as f:
                f.write(str(i + 1))
            print(f"Done.")
        except Exception as e:
            print(f"Error: {e}")
            return

if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_interleaved_translation(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 1, int(sys.argv[3]) if len(sys.argv) > 3 else None)
    else:
        print("[!] Usage: python3 translate_epub.py [EPUB] [FREQUENCY] [LIMIT]")

