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
    """Deletes common AI conversational artifacts."""
    artifacts = [
        "Here's my attempt", "Here is the translation", "Translation:", 
        "Contemporary English:", "Certainly!", "Okay", "Enough thinking"
    ]
    cleaned = text.strip()
    for artifact in artifacts:
        # Case-insensitive removal of common introductory phrases
        cleaned = re.sub(f"(?i)^{artifact}.*?[:\\n]", "", cleaned)
    return cleaned.strip()

def split_into_sentences(text):
    """Splits text into sentences based on punctuation."""
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s for s in sentences if s.strip()]

def is_narrative_start(el):
    """Triggers translation at the first 15-word paragraph (e.g., 'Longtemps')."""
    text = el.get_text().strip()
    return el.name == 'p' and len(text.split()) >= 15

def run_interleaved_translation(epub_path, section_limit=None, min_sect_length=500, num_sentences=None, break_at_p_tags=False):
    start_section = 0
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r") as f:
            line = f.read().strip()
            start_section = int(line) if line.isdigit() else 0

    book = epub.read_epub(epub_path)
    output_file = os.path.splitext(epub_path)[0] + "_Bilingual.txt"
    
    # 1. METADATA HANDSHAKE
    if not os.path.exists(output_file):
        title = book.get_metadata('DC', 'title')[0][0] if book.get_metadata('DC', 'title') else "Unknown"
        author = book.get_metadata('DC', 'creator')[0][0] if book.get_metadata('DC', 'creator') else "Unknown"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(f"TITLE: {title}\nAUTHOR: {author}\n========================================\n")

    all_elements = []
    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        soup = BeautifulSoup(item.get_content(), 'html.parser')
        for el in soup.find_all(['p', 'h1', 'h2', 'h3']):
            if el.get_text(strip=True):
                all_elements.append(el)

    # 2. SEGMENTATION ENGINE
    sections, narrative_found, sentence_buffer, chunk_buffer, words_in_chunk = [], False, [], [], 0

    for el in all_elements:
        if not narrative_found and is_narrative_start(el):
            narrative_found = True

        if not narrative_found:
            sections.append((False, str(el)))
        else:
            text = el.get_text().strip()
            # NEW: Immediate break if parameter is active
            if break_at_p_tags and el.name == 'p':
                sections.append((True, str(el)))
            elif num_sentences:
                sentences = split_into_sentences(text)
                for s in sentences:
                    sentence_buffer.append(s)
                    if len(sentence_buffer) >= num_sentences:
                        sections.append((True, " ".join(sentence_buffer)))
                        sentence_buffer = []
            else:
                chunk_buffer.append(el)
                words_in_chunk += len(text.split())
                if words_in_chunk >= min_sect_length:
                    sections.append((True, "\n".join([str(x) for x in chunk_buffer])))
                    chunk_buffer, words_in_chunk = [], 0

    if sentence_buffer: sections.append((True, " ".join(sentence_buffer)))
    if chunk_buffer: sections.append((True, "\n".join([str(x) for x in chunk_buffer])))

    # 3. TRANSLATION WITH CONTEXT
    total = len(sections)
    translated_count = 0
    last_translation = "No previous context."
    idx = start_section

    print(f"[*] Resuming at section {idx+1}/{total}. Filter Active.")

    while idx < total:
        do_trans, content = sections[idx]
        with open(output_file, "a", encoding="utf-8") as f:
            display_original = f"<p>{content}</p>" if (do_trans and num_sentences) else content
            f.write(f"\n<div class='original-text'>\n### SECTION {idx+1} ORIGINAL\n{display_original}\n</div>\n")
            
            if do_trans:
                print(f"[*] Translating Segment {translated_count+1}...", end=" ", flush=True)
                time.sleep(15)
                clean_text = content if num_sentences else BeautifulSoup(content, 'html.parser').get_text().strip()
                
                # Including Last Translation for continuity
                prompt = f"PREVIOUS TRANSLATION CONTEXT: {last_translation}\n\nCURRENT TEXT TO TRANSLATE:\n{clean_text}"
                
                try:
                    res = client.models.generate_content(
                        model=MODEL_ID,
                        config={'system_instruction': "ACT AS A LITERARY TRANSLATOR. NO CONVERSATION. NO INTRODUCTIONS. OUTPUT ONLY CONTEMPORARY ENGLISH PROSE."},
                        contents=prompt[:12000]
                    )
                    sanitized = clean_ai_response(res.text)
                    last_translation = sanitized 
                    
                    fmt = "".join([f"<p><i>{line.strip()}</i></p>" for line in sanitized.split('\n') if line.strip()])

                    f.write(f"\n<details><summary>Translation</summary>\n<div class='translation-content'>{fmt}</div>\n</details>\n")
                    translated_count += 1
                    print("Done.")
                except Exception as e:
                    print(f"Error: {e}")

            f.write(f"\n========================================\n")
            f.flush()
        idx += 1
        with open(PROGRESS_FILE, "w") as f: f.write(str(idx))
        if section_limit and translated_count >= section_limit: break

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", required=True)
    parser.add_argument("-l", "--limit", type=int, default=None)
    parser.add_argument("-m", "--min_sect_length", type=int, default=500)
    parser.add_argument("-s", "--num_sentences", type=int, default=None)
    # ADDED PARAMETER
    parser.add_argument("-break_at_p_tags", action="store_true", help="Interleave based on paragraph boundaries")
    args = parser.parse_args()
    run_interleaved_translation(args.input, args.limit, args.min_sect_length, args.num_sentences, args.break_at_p_tags)

