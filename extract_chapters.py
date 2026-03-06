import os, re, argparse, time
from google import genai

# Configuration
MODEL_NAME = 'gemini-2.5-pro'
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

def int_to_roman(n):
    """Converts an integer to a Roman numeral string."""
    val = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]
    syb = ["M", "CM", "D", "CD", "C", "XC", "L", "XL", "X", "IX", "V", "IV", "I"]
    roman_num = ""
    i = 0
    while n > 0:
        for _ in range(n // val[i]):
            roman_num += syb[i]
            n -= val[i]
        i += 1
    return roman_num

def analyze_text(text):
    if not text.strip(): return "No content available for analysis."
    prompt = f"Provide a concise character study based on this text. Focus only on how characters are presented and any immediate shifts in their situation. Avoid thematic or philosophical discussion.\n\nText:\n{text}"
    try:
        response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
        return response.text.strip()
    except Exception as e:
        print(f"[!] LLM Error: {e}"); return "Analysis generation failed."

def summarize_text(text):
    if not text.strip(): return "No content available."
    prompt = f"Summarize the action of the following text only. Focus on what happens. Do not include any analysis or interpretation. \n\nText:\n{text}"
    try:
        response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
        return response.text.strip()
    except Exception: return "Summary generation failed."

def extract_chapters(input_file, output_file, extract_analysis):
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    sections = re.split(r'={40}', content)
    output_data = []
    current_text_block = []
    chapter_count = 1  # NEW: Tracks the sequence

    for section in sections:
        match = re.search(r'### SECTION \d+ ORIGINAL\s+<h[1-3][^>]*>(.*?)</h[1-3]>', section, re.DOTALL | re.IGNORECASE)
        
        if match:
            if current_text_block:
                # MODIFIED: Use the counter instead of the raw header text
                process_and_append_chapter(int_to_roman(chapter_count), current_text_block, output_data, extract_analysis)
                chapter_count += 1
                current_text_block = []
        
        text_matches = re.findall(r"<div class='original-text'>(.*?)</div>", section, re.DOTALL)
        for t in text_matches:
            clean_t = re.sub(r'<.*?>', '', t).strip()
            if clean_t: current_text_block.append(clean_t)

    if current_text_block:
        process_and_append_chapter(int_to_roman(chapter_count), current_text_block, output_data, extract_analysis)

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("\n".join(output_data))
    print(f"[*] Finished! Output saved to: {output_file}")

def process_and_append_chapter(title, text_list, output_list, extract_analysis):
    full_narrative = "\n\n".join(text_list).strip()
    if not full_narrative: return

    print(f"    - Processing Chapter {title}...")
    summary = summarize_text(full_narrative)
    
    output_list.append(f"TITLE: Chapter {title}")
    output_list.append(f"SUMMARY: {summary}")
    
    if extract_analysis:
        analysis = analyze_text(full_narrative)
        output_list.append(f"ANALYSIS: {analysis}")
    
    output_list.append(f"CONTENT:\n{full_narrative}\n")
    output_list.append("="*40 + "\n")
    time.sleep(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", required=True)
    parser.add_argument("-o", "--output", required=True)
    parser.add_argument("--extract-analysis", action="store_true")
    args = parser.parse_args()
    extract_chapters(args.input, args.output, args.extract_analysis)

