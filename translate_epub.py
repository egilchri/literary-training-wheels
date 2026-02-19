import sys, os, time, ebooklib, argparse, re
from ebooklib import epub
from bs4 import BeautifulSoup
from google import genai

# --- CONFIGURATION ---
API_KEY = os.environ.get("GEMINI_API_KEY")
MODEL_ID = "gemini-2.0-flash-lite"
PROGRESS_FILE = ".translation_progress"
client = genai.Client(api_key=API_KEY)

def clean_ai_response(text):
    artifacts = ["Here's my attempt", "Here is the translation", "Translation:", "Contemporary English:"]
    cleaned = text.strip()
    for artifact in artifacts:
        cleaned = re.sub(f"(?i)^{artifact}.*?[:\\n]", "", cleaned)
    return cleaned.strip()

def is_strict_chapter(text):
    """
    Matches 'Chapter IV' OR just 'IV' (Roman numerals).
    Allows for leading/trailing whitespace.
    """
    # Pattern 1: 'Chapter' + Roman Numeral
    pattern_with_word = r"^\s*chapter\s+[ivxlcdm]+\s*$"
    # Pattern 2: Standalone Roman Numeral (must be the only thing in the tag)
    pattern_standalone = r"^\s*[ivxlcdm]+\s*$"
    
    val = text.lower().strip()
    return bool(re.match(pattern_with_word, val) or re.match(pattern_standalone, val))

def run_interleaved_translation(epub_path, section_limit=None, chapter_limit=None, min_sect_length=500, break_at_p_tags=False, chapter_tags="h1,h2,h3"):
    book = epub.read_epub(epub_path)
    out_file = epub_path.replace(".epub", "_Bilingual.txt")
    tags_to_watch = [t.strip().lower() for t in chapter_tags.split(",")]
    
    idx = 0
    translated_count = 0
    chapters_processed = 0
    
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r") as f: 
            idx = int(f.read().strip())
            print(f"Resuming from index {idx}...")

    items = [item for item in book.get_items() if item.get_type() == ebooklib.ITEM_DOCUMENT]

    with open(out_file, "a" if idx > 0 else "w", encoding="utf-8") as f:
        for i, item in enumerate(items[idx:]):
            current_index = idx + i
            soup = BeautifulSoup(item.get_content(), "html.parser")
            elements = soup.find_all(['p'] + tags_to_watch)
            
            for el in elements:
                text_content = el.get_text().strip()
                if not text_content: continue

                is_header_tag = el.name in tags_to_watch
                
                if is_header_tag:
                    f.write(f"\n<div class='original-text'>\n### SECTION {translated_count + 1} ORIGINAL\n{str(el)}\n</div>\n")
                    f.write(f"\n### EXTRACTED HEADER: {text_content}\n")
                    f.write(f"\n========================================\n")
                    
                    if is_strict_chapter(text_content):
                        chapters_processed += 1
                        print(f"Validated Chapter ({chapters_processed}/{chapter_limit}): {text_content}")
                    else:
                        print(f"Skipping (Non-Chapter Header): {text_content}")
                else:
                    if break_at_p_tags or len(text_content) >= min_sect_length:
                        f.write(f"\n<div class='original-text'>\n### SECTION {translated_count + 1} ORIGINAL\n{str(el)}\n</div>\n")
                        try:
                            print(f"Translating section {translated_count + 1}...", end=" ", flush=True)
                            prompt = f"Translate this into contemporary English. Only provide the translation:\n\n{text_content}"
                            response = client.models.generate_content(model=MODEL_ID, contents=prompt)
                            sanitized = clean_ai_response(response.text)
                            
                            fmt = "".join([f"<p><i>{line.strip()}</i></p>" for line in sanitized.split('\n') if line.strip()])
                            f.write(f"\n<details><summary>Translation</summary>\n<div class='translation-content'>{fmt}</div>\n</details>\n")
                            print("Done.")
                        except Exception as e:
                            print(f"Error: {e}")
                        f.write(f"\n========================================\n")
                    
                translated_count += 1
                f.flush()

                if chapter_limit and chapters_processed >= chapter_limit: break
            if (chapter_limit and chapters_processed >= chapter_limit):
                print("Chapter limit reached.")
                break
            with open(PROGRESS_FILE, "w") as pf: pf.write(str(current_index + 1))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", required=True)
    parser.add_argument("-c", "--chapter_limit", type=int, default=None)
    parser.add_argument("-m", "--min_sect_length", type=int, default=500)
    parser.add_argument("--break_at_p_tags", action="store_true")
    parser.add_argument("--chapter_tags", type=str, default="h1,h2,h3")
    
    args = parser.parse_args()
    run_interleaved_translation(args.input, None, args.chapter_limit, args.min_sect_length, args.break_at_p_tags, args.chapter_tags)

