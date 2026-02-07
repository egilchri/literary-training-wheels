import os, re, argparse, time
from google import genai

# Configuration exactly like extract_cantos.py
MODEL_NAME = 'gemini-2.5-pro'
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

def summarize_text(text):
    """
    Sends English original text to the LLM for action-only summarization
    using the gemini-2.5-pro model.
    """
    if not text.strip():
        return "No content available."
    
    prompt = f"""Summarize the action of the following text only. 
    Focus on what happens. Do not include any analysis or interpretation. 

    Text:
    {text}
    """
    
    try:
        # Using the model name as defined in your other scripts
        response = client.models.generate_content(
            model=MODEL_NAME, 
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        print(f"[!] LLM Error with {MODEL_NAME}: {e}")
        return "Summary generation failed."

def extract_chapters(input_txt, output_file, start_ch, end_ch):
    if not os.path.exists(input_txt):
        print(f"[!] Input file not found: {input_txt}")
        return

    with open(input_txt, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split using the Chapter Boundary marker
    raw_chapters = re.split(r'#{40}\n>>> CHAPTER BOUNDARY <<<\n#{40}', content)
    
    output_data = []
    capture = False

    for i, ch_text in enumerate(raw_chapters):
        if not ch_text.strip():
            continue
            
        # Match the title marker used in the bilingual file
        title_match = re.search(r"## ORIGINAL CHAPTER:\s*(.*)\n", ch_text)
        raw_title = title_match.group(1).strip() if title_match else ""
        
        # Map "CONTENTS" to "Introduction" for consistent start_chapter logic
        norm_title = "Introduction" if raw_title.upper() == "CONTENTS" else raw_title
        
        if norm_title == start_ch:
            capture = True
        
        if capture:
            print(f"[*] Processing: {norm_title}...")
            
            # Remove translations to keep context English-only for the LLM
            english_text = re.sub(r"### SECTION \d+ TRANSLATED.*?(?=### SECTION \d+ ORIGINAL|$)", "", ch_text, flags=re.DOTALL)
            
            # Clean technical markers
            clean_context = re.sub(r"## (ORIGINAL|TRANSLATED) CHAPTER:.*\n", "", english_text)
            clean_context = re.sub(r"#{10,}|={10,}", "", clean_context)
            clean_context = re.sub(r"### SECTION \d+ ORIGINAL", "", clean_context).strip()

            # Active summarization via Gemini 2.5 Pro
            summary = summarize_text(clean_context)
            
            # Format output for build_epub.py
            output_data.append(f"TITLE: {norm_title}")
            output_data.append(f"SUMMARY: {summary}") 
            output_data.append(f"CONTENT:\n{clean_context}\n")
            output_data.append("="*40 + "\n")
            
            time.sleep(1) 

        if norm_title == end_ch:
            capture = False
            break

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("\n".join(output_data))
    
    print(f"[*] Finished! Output saved to: {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", required=True)
    parser.add_argument("-o", "--output_file", required=True)
    parser.add_argument("-start_chapter", required=True)
    parser.add_argument("-end_chapter", required=True)
    args = parser.parse_args()
    
    extract_chapters(args.input, args.output_file, args.start_chapter, args.end_chapter)

