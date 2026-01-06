import sys, os, time, ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
from google import genai

# --- CONFIGURATION ---
API_KEY = os.environ.get("GEMINI_API_KEY")
MODEL_ID = "gemini-2.0-flash-lite"
PROGRESS_FILE = ".translation_progress"
client = genai.Client(api_key=API_KEY)

def run_interleaved_translation(epub_path, frequency=1, limit=None):
    start_section = 0
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r") as f:
            try:
                start_section = int(f.read().strip())
            except ValueError:
                start_section = 0

    book = epub.read_epub(epub_path)
    
    # --- STEP 1: EXTRACT ELEMENTS WITH METADATA FILTERING ---
    all_elements = []
    # Keywords that usually indicate non-narrative metadata to ignore
    metadata_keywords = [
        "Project Gutenberg", "Release Date:", "Credits:", "Author:", 
        "Produced by", "Language:", "Character set encoding:"
    ]

    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        soup = BeautifulSoup(item.get_content(), 'html.parser')
        elements = soup.find_all(['h1', 'h2', 'h3', 'p'])
        
        for el in elements:
            clean_text = el.get_text().strip()
            # Skip empty elements or elements containing metadata keywords
            if not clean_text or any(kw in clean_text for kw in metadata_keywords):
                continue
            all_elements.append(el)

    # --- STEP 2: GROUP ELEMENTS BY FREQUENCY ---
    chunks = []
    for i in range(0, len(all_elements), frequency):
        group = all_elements[i:i + frequency]
        text_block = "\n".join([str(el) for el in group])
        if len(text_block.strip()) > 10: 
            chunks.append(text_block)

    output_file = os.path.splitext(epub_path)[0] + "_Bilingual.txt"
    
    # Calculate exactly where to stop based on the limit
    end_section = min(start_section + limit, len(chunks)) if limit else len(chunks)

    print(f"[*] Resuming from Chunk {start_section + 1}...")
    print(f"[*] Frequency: {frequency} paragraphs/headers per block.")
    if limit:
        print(f"[*] Limit: Processing {limit} chunks this session.")

    for i in range(start_section, end_section):
        original_html_chunk = chunks[i]
        text_for_ai = BeautifulSoup(original_html_chunk, 'html.parser').get_text()
        
        time.sleep(20) # Avoid rate limits
        print(f"[*] Chunk {i+1}/{len(chunks)}: Translating...", end=" ", flush=True)
        
        try:
            # System instruction strictly focuses the AI on the provided text only
            response = client.models.generate_content(
                model=MODEL_ID,
                config={'system_instruction': "Translate this literary prose into clear, contemporary English. Maintain paragraph structure. Only translate the provided text. Do not provide outside content or introductory remarks."},
                contents=text_for_ai[:12000]
            )
            
            trans_lines = response.text.strip().split('\n')
            formatted_translation = "".join([f"<p>{l.strip()}</p>" for l in trans_lines if l.strip()])
            
            with open(output_file, "a", encoding="utf-8") as f:
                f.write(f"\n<div class='original-text justify-text'>\n")
                # Since we filtered metadata upstream, everything here is narrative
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
        target_epub = sys.argv[1]
        # Arg 2: Frequency 
        freq = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        # Arg 3: Limit 
        lim = int(sys.argv[3]) if len(sys.argv) > 3 else None
        
        run_interleaved_translation(target_epub, freq, lim)
    else:
        print("[!] Usage: python3 translate_epub.py [EPUB] [FREQUENCY] [LIMIT]")

