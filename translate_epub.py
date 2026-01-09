import sys, os, time, ebooklib, argparse
from ebooklib import epub
from bs4 import BeautifulSoup
from google import genai

# --- 1. CONFIGURATION ---
API_KEY = os.environ.get("GEMINI_API_KEY")
MODEL_ID = "gemini-2.0-flash-lite"
PROGRESS_FILE = ".translation_progress"
client = genai.Client(api_key=API_KEY)

def clean_ai_response(text):
    """Ensures AI meta-talk like 'Enough thinking' is stripped at the source."""
    artifacts = ["Enough thinking", "Okay, I'm ready", "Here is the translation"]
    cleaned = text.strip()
    for artifact in artifacts:
        cleaned = cleaned.replace(artifact, "")
    return cleaned.strip()

def run_interleaved_translation(epub_path, paragraphs_per_section=3, section_limit=None, min_sect_length=None):
    start_section = 0
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r") as f:
            start_section = int(f.read().strip())

    book = epub.read_epub(epub_path)
    
    # --- 2. VERBATIM EXTRACTION ---
    all_paras = []
    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        soup = BeautifulSoup(item.get_content(), 'html.parser')
        # Captures p and h tags to ensure the TOC headers are preserved
        for el in soup.find_all(['p', 'h1', 'h2', 'h3']):
            if el.get_text(strip=True):
                all_paras.append(el)

    # --- 3. REGROUPING BY WORD COUNT ---
    sections = []
    if min_sect_length:
        current_chunk, current_words = [], 0
        for p in all_paras:
            current_chunk.append(p)
            current_words += len(p.get_text().split())
            if current_words >= min_sect_length:
                sections.append("\n".join([str(x) for x in current_chunk]))
                current_chunk, current_words = [], 0
        if current_chunk: # Final section cleanup
            sections.append("\n".join([str(x) for x in current_chunk]))
    else:
        for i in range(0, len(all_paras), paragraphs_per_section):
            chunk = all_paras[i : i + paragraphs_per_section]
            sections.append("\n".join([str(p) for p in chunk]))

    output_file = os.path.splitext(epub_path)[0] + "_Bilingual.txt"
    total_sections = len(sections)
    end_section = min(start_section + section_limit, total_sections) if section_limit else total_sections

    print(f"[*] Processing Sections {start_section+1} to {end_section} of {total_sections}...")

    for i in range(start_section, end_section):
        original_html_chunk = sections[i]
        text_for_ai = BeautifulSoup(original_html_chunk, 'html.parser').get_text().strip()
        if not text_for_ai: continue

        time.sleep(20) # Pacing
        print(f"[*] Section {i+1}/{total_sections}: Translating...", end=" ", flush=True)
        try:
            # --- 4. REINFORCED SYSTEM INSTRUCTION ---
            response = client.models.generate_content(
                model=MODEL_ID,
                config={'system_instruction': (
                    "ACT AS AN ENGLISH LITERARY TRANSLATOR. "
                    "Rewrite 1902 Henry James prose into contemporary English. "
                    "OUTPUT ONLY ENGLISH TRANSLATED PROSE. NO GREEK. NO SPANISH. "
                    "NO CONVERSATION. NO META-TALK."
                )},
                contents=text_for_ai[:12000]
            )
            
            sanitized = clean_ai_response(response.text if response.text else "")
            # Properly nested italics for e-reader compatibility
            formatted = "".join([f"<p><i>{l.strip()}</i></p>" for l in sanitized.split('\n') if l.strip()])
            
            with open(output_file, "a", encoding="utf-8") as f:
                f.write(f"\n<div class='original-text justify-text'>\n")
                f.write(f"### SECTION {i+1} ORIGINAL\n")
                f.write(original_html_chunk + "\n") # VERBATIM ORIGINAL
                f.write(f"</div>\n")
                   
                f.write(f"\n<details class='modern-translation'>\n")
                f.write(f"  <summary>Click to show contemporary translation</summary>\n")
                f.write(f"  <div class='translation-content'>\n{formatted}\n</div>\n")
                f.write(f"</details>\n========================================\n")
                f.flush()

            with open(PROGRESS_FILE, "w") as f: f.write(str(i+1))
            print("Done.")
        except Exception as e:
            print(f"Error: {e}")
            return

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", required=True)
    parser.add_argument("-p", "--paras", type=int, default=3)
    parser.add_argument("-l", "--limit", type=int, default=None)
    parser.add_argument("-m", "--min_sect_length", type=int, default=None)
    args = parser.parse_args()
    run_interleaved_translation(args.input, args.paras, args.limit, args.min_sect_length)

