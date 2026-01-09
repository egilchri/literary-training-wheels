import sys, os, time, ebooklib, argparse
from ebooklib import epub
from bs4 import BeautifulSoup
from google import genai

# --- 1. CONFIGURATION ---
API_KEY = os.environ.get("GEMINI_API_KEY")
MODEL_ID = "gemini-2.0-flash-lite"
PROGRESS_FILE = ".translation_progress"
client = genai.Client(api_key=API_KEY)

def run_interleaved_translation(epub_path, paragraphs_per_section=3, section_limit=None, min_sect_length=None):
    start_section = 0
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r") as f:
            start_section = int(f.read().strip())

    book = epub.read_epub(epub_path)
    
    # --- 2. INCLUSIVE EXTRACTION (Restored) ---
    # Captures paragraphs and headers (I, II, III) to ensure TOC readiness
    all_paras = []
    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        soup = BeautifulSoup(item.get_content(), 'html.parser')
        for el in soup.find_all(['p', 'h1', 'h2', 'h3']):
            if el.get_text(strip=True):
                all_paras.append(el)

    # --- 3. REGROUPING LOGIC (Words vs. Paragraphs) ---
    sections = []
    if min_sect_length:
        # Word-based logic: Exceed threshold, then finish current paragraph
        current_chunk = []
        current_words = 0
        for p in all_paras:
            text = p.get_text()
            words_in_p = len(text.split())
            current_chunk.append(p)
            current_words += words_in_p
            
            if current_words >= min_sect_length:
                sections.append("\n".join([str(x) for x in current_chunk]))
                current_chunk = []
                current_words = 0
        # Final cleanup: handle the remaining "orphan" section at the end of the book
        if current_chunk:
            sections.append("\n".join([str(x) for x in current_chunk]))
    else:
        # Standard Paragraph-based logic
        for i in range(0, len(all_paras), paragraphs_per_section):
            chunk = all_paras[i : i + paragraphs_per_section]
            section_html = "\n".join([str(p) for p in chunk])
            if section_html.strip():
                sections.append(section_html)

    output_file = os.path.splitext(epub_path)[0] + "_Bilingual.txt"
    total_sections = len(sections)
    end_section = min(start_section + section_limit, total_sections) if section_limit else total_sections

    print(f"[*] Resuming from Section {start_section + 1} of {total_sections}...")

    for i in range(start_section, end_section):
        original_html_chunk = sections[i]
        text_for_ai = BeautifulSoup(original_html_chunk, 'html.parser').get_text().strip()
        
        if not text_for_ai:
            continue

        time.sleep(20) # Pacing for Gemini Free Tier
        
        print(f"[*] Section {i+1}/{total_sections}: Translating...", end=" ", flush=True)
        try:
            # Strict translation prompt to minimize meta-talk
            response = client.models.generate_content(
                model=MODEL_ID,
                config={'system_instruction': (
                    "ACT AS A TRANSLATION ENGINE. Translate the text into contemporary English. "
                    "OUTPUT ONLY THE TRANSLATION. NO CONVERSATION. NO META-TALK."
                )},
                contents=text_for_ai[:12000]
            )
            
            # Format translation paragraphs
            trans_lines = response.text.strip().split('\n')
            formatted_translation = "".join([f"<p>{l.strip()}</p>" for l in trans_lines if l.strip()])
            
            with open(output_file, "a", encoding="utf-8") as f:
                f.write(f"\n<div class='original-text justify-text'>\n")
                f.write(f"### SECTION {i+1} ORIGINAL\n")
                f.write(original_html_chunk + "\n")
                f.write(f"</div>\n")
                   
                f.write(f"\n<details class='modern-translation'>\n")
                f.write(f"  <summary>Click to show contemporary translation</summary>\n")
                f.write(f"  <div class='translation-content'>\n")
                # Restored: Translation wrapped in italics
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
    parser = argparse.ArgumentParser(description="Bilingual Translator")
    parser.add_argument("-i", "--input", required=True, help="Path to source .epub")
    parser.add_argument("-p", "--paras", type=int, default=3, help="Paras per section")
    parser.add_argument("-l", "--limit", type=int, default=None, help="Limit sections")
    # Added min_sect_length (measured in words)
    parser.add_argument("-m", "--min_sect_length", type=int, default=None, help="Min words per section (Supersedes -p)")
    
    args = parser.parse_args()
    run_interleaved_translation(args.input, args.paras, args.limit, args.min_sect_length)
    
