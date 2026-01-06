import sys, os, time, ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
from google import genai

# --- CONFIGURATION ---
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
    
    # --- STEP 1: PRESERVE ORIGINAL PARAGRAPHS ---
    chapters = []
    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        soup = BeautifulSoup(item.get_content(), 'html.parser')
        # We extract the actual <p> tags so we don't lose the author's structure
        paras = soup.find_all('p')
        if paras:
            text_block = "\n".join([str(p) for p in paras])
            if len(text_block) > 30:
                chapters.append(text_block)

    output_file = os.path.splitext(epub_path)[0] + "_Bilingual.txt"
    end_section = min(start_section + limit, len(chapters)) if limit else len(chapters)

    print(f"[*] Resuming from Section {start_section + 1}...")

    for i in range(start_section, end_section):
        original_html_chunk = chapters[i]
        
        # Strip tags for the AI prompt only
        text_for_ai = BeautifulSoup(original_html_chunk, 'html.parser').get_text()
        
        time.sleep(20) 
        print(f"[*] Section {i+1}: Translating...", end=" ", flush=True)
        
        try:
            response = client.models.generate_content(
                model=MODEL_ID,
                config={'system_instruction': "Translate this literary prose into clear, contemporary English. Use modern paragraph structures."},
                contents=text_for_ai[:12000]
            )
            
            # Format translation paragraphs
            trans_lines = response.text.strip().split('\n')
            formatted_translation = "".join([f"<p>{l.strip()}</p>" for l in trans_lines if l.strip()])
            
            with open(output_file, "a", encoding="utf-8") as f:
                # Write with preserved tags
                f.write(f"\n<div class='original-text justify-text'>\n")
                f.write(f"### SECTION {i+1} ORIGINAL\n")
                f.write(original_html_chunk + "\n")
                f.write(f"</div>\n")
                   
                f.write(f"\n<details class='modern-translation'>\n")
                f.write(f"  <summary>Click to show contemporary translation</summary>\n")
                f.write(f"  <div class='translation-content'>\n")
                f.write(f"    <i>{formatted_translation}</i>\n") 
                f.write(f"  </div>\n")
                f.write(f"</details>\n")
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
        run_interleaved_translation(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else None)
