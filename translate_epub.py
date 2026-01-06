import sys, os, time, ebooklib, argparse
from ebooklib import epub
from bs4 import BeautifulSoup
from google import genai

# --- 1. CONFIGURATION ---
API_KEY = os.environ.get("GEMINI_API_KEY")
MODEL_ID = "gemini-2.0-flash-lite"
PROGRESS_FILE = ".translation_progress"
client = genai.Client(api_key=API_KEY)

def run_interleaved_translation(epub_path, paragraphs_per_section=3, section_limit=None):
    start_section = 0
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r") as f:
            start_section = int(f.read().strip())

    book = epub.read_epub(epub_path)
    
    # --- 2. TAG-PRESERVED EXTRACTION ---
    all_paras = []
    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        soup = BeautifulSoup(item.get_content(), 'html.parser')
        # Preserve the original <p> tags to maintain the 19th-century structure
        all_paras.extend(soup.find_all('p'))

    # --- 3. REGROUP INTO SECTIONS ---
    sections = []
    for i in range(0, len(all_paras), paragraphs_per_section):
        chunk = all_paras[i : i + paragraphs_per_section]
        # Join the actual HTML tags into the block
        section_html = "\n".join([str(p) for p in chunk])
        if section_html.strip():
            sections.append(section_html)

    output_file = os.path.splitext(epub_path)[0] + "_Bilingual.txt"
    
    total_sections = len(sections)
    end_section = total_sections
    if section_limit:
        end_section = min(start_section + section_limit, total_sections)
        print(f"[*] Limit Active: Processing {section_limit} sections.")

    print(f"[*] Resuming from Section {start_section + 1} of {total_sections}...")
    print(f"[*] Settings: {paragraphs_per_section} paras/section.")

    for i in range(start_section, end_section):
        original_html_chunk = sections[i]
        
        # Strip tags for the AI prompt only
        text_for_ai = BeautifulSoup(original_html_chunk, 'html.parser').get_text()
        
        time.sleep(20) # 2026 Free Tier Pacing
        
        print(f"[*] Section {i+1}/{total_sections}: Translating...", end=" ", flush=True)
        try:
            response = client.models.generate_content(
                model=MODEL_ID,
                config={'system_instruction': "Translate this literary prose into contemporary English. Use modern paragraph structures."},
                contents=text_for_ai[:12000]
            )
            
            # Format translation paragraphs using proper tags
            trans_lines = response.text.strip().split('\n')
            formatted_translation = "".join([f"<p>{l.strip()}</p>" for l in trans_lines if l.strip()])
            
            with open(output_file, "a", encoding="utf-8") as f:
                # Write original with preserved <p> tags
                f.write(f"\n<div class='original-text justify-text'>\n")
                f.write(f"### SECTION {i+1} ORIGINAL\n")
                f.write(original_html_chunk + "\n")
                f.write(f"</div>\n")
                   
                # Write translation with its own <p> tags
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
    parser = argparse.ArgumentParser(description="Keyword-driven Bilingual Translator")
    
    # Required keyword argument for the input file
    parser.add_argument("-i", "--input", required=True, help="Path to the source .epub file")
    
    # Optional keyword arguments with defaults
    parser.add_argument("-p", "--paras", type=int, default=3, help="Paragraphs per section (Default: 3)")
    parser.add_argument("-l", "--limit", type=int, default=None, help="Sections to translate (Default: All)")
    
    args = parser.parse_args()
    
    run_interleaved_translation(
        epub_path=args.input, 
        paragraphs_per_section=args.paras, 
        section_limit=args.limit
    )

