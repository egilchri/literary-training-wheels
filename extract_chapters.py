import os, re, argparse
from google import genai

# --- CONFIGURATION ---
API_KEY = os.environ.get("GEMINI_API_KEY")
MODEL_ID = "gemini-2.0-flash-lite"
client = genai.Client(api_key=API_KEY)

def summarize_text(text, chapter_title):
    """Sends accumulated source text to Gemini for a concise summary."""
    if not text.strip():
        return "No content found for this chapter."
    
    prompt = f"Summarize the following chapter from 'What Maisie Knew' titled '{chapter_title}'. Focus on plot points and character development:\n\n{text[:15000]}"
    
    try:
        res = client.models.generate_content(
            model=MODEL_ID,
            config={'system_instruction': "You are a literary assistant. Provide clear, concise summaries of book chapters."},
            contents=prompt
        )
        return res.text.strip()
    except Exception as e:
        return f"Error during summarization: {e}"

def normalize(val):
    """Strips 'Chapter' and whitespace to allow flexible matching."""
    if not val: return ""
    return re.sub(r'^chapter\s+', '', val.strip().lower())

def process_bilingual_file(filepath, start_ch, end_ch):
    if not os.path.exists(filepath):
        print(f"File {filepath} not found.")
        return

    # Define the .out file path based on the input filename
    output_path = os.path.splitext(filepath)[0] + ".out"
    
    # Initialize/Clear the .out file with a header
    with open(output_path, "w", encoding="utf-8") as f_out:
        f_out.write(f"CHAPTER SUMMARIES FOR: {filepath}\n")
        f_out.write("="*40 + "\n")

    current_chapter_title = ""
    current_chapter_text = []
    is_original_block = False
    in_range = False
    finished = False

    start_target = normalize(start_ch)
    end_target = normalize(end_ch) if end_ch else None

    with open(filepath, "r", encoding="utf-8") as f_in:
        for line in f_in:
            if finished:
                break

            # Boundary Detection
            if "## ORIGINAL CHAPTER:" in line:
                found_title = line.replace("## ORIGINAL CHAPTER:", "").strip()
                norm_found = normalize(found_title)

                # Identify if we have entered the requested range
                if not in_range:
                    if start_target == norm_found or start_target in norm_found:
                        in_range = True
                        print(f"[+] Starting range at: {found_title}")

                # If moving to a new chapter, summarize the one we just finished
                if in_range and current_chapter_text:
                    print(f"[*] Summarizing {current_chapter_title}...")
                    summary = summarize_text(" ".join(current_chapter_text), current_chapter_title)
                    
                    # Write to .out file immediately
                    with open(output_path, "a", encoding="utf-8") as f_out:
                        f_out.write(f"\nTITLE: {current_chapter_title}\n")
                        f_out.write(f"SUMMARY: {summary}\n")
                        f_out.write("-" * 20 + "\n")
                        f_out.flush() # Force write to disk
                    
                    current_chapter_text = []

                    # Stop if we just finished the designated end chapter
                    if end_target and (end_target == normalize(current_chapter_title)):
                        finished = True
                        continue

                current_chapter_title = found_title
                continue

            if not in_range:
                continue

            # Content Extraction Logic
            if "### SECTION" in line and "ORIGINAL" in line:
                is_original_block = True
                continue
            
            if "</div>" in line and is_original_block:
                is_original_block = False
                continue

            if is_original_block:
                # Clean HTML and capture source text
                clean_line = re.sub(r'<[^>]+>', '', line).strip()
                if clean_line and "SECTION" not in clean_line:
                    current_chapter_text.append(clean_line)

    # Summarize the final chapter in the range
    if in_range and current_chapter_text and not finished:
        print(f"[*] Summarizing {current_chapter_title}...")
        summary = summarize_text(" ".join(current_chapter_text), current_chapter_title)
        with open(output_path, "a", encoding="utf-8") as f_out:
            f_out.write(f"\nTITLE: {current_chapter_title}\n")
            f_out.write(f"SUMMARY: {summary}\n")
            f_out.write("="*40 + "\n")

    print(f"\n[!] Done. Summaries written to: {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", default="Books/what_maisie_knew_Bilingual.txt")
    parser.add_argument("-start_chapter", default="I")
    parser.add_argument("-end_chapter", default="VI")
    
    args = parser.parse_args()
    process_bilingual_file(args.input, args.start_chapter, args.end_chapter)

