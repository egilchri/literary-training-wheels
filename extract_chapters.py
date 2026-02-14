import os, re, argparse, time
from google import genai

# Configuration
MODEL_NAME = 'gemini-2.5-pro'
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

def analyze_text(text):
    """
    Sends English original text to the LLM for literary analysis.
    """
    if not text.strip():
        return "No content available for analysis."
    
    prompt = f"""Perform a literary analysis of the following text. 
    Focus on the themes, character developments, and major literary ideas taking shape. 

    Text:
    {text}
    """
    
    try:
        response = client.models.generate_content(
            model=MODEL_NAME, 
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        print(f"[!] LLM Error with {MODEL_NAME} during analysis: {e}")
        return "Analysis generation failed."

def summarize_text(text):
    """
    Sends English original text to the LLM for action-only summarization.
    """
    if not text.strip():
        return "No content available."
    
    prompt = f"""Summarize the action of the following text only. 
    Focus on what happens. Do not include any analysis or interpretation. 

    Text:
    {text}
    """
    
    try:
        response = client.models.generate_content(
            model=MODEL_NAME, 
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        print(f"[!] LLM Error with {MODEL_NAME} during summary: {e}")
        return "Summary generation failed."

def extract_chapters(input_txt, output_file, extract_analysis=False):
    if not os.path.exists(input_txt):
        print(f"[!] Input file not found: {input_txt}")
        return

    with open(input_txt, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split using the Chapter Boundary marker
    raw_blocks = re.split(r'#{40}\n>>> CHAPTER BOUNDARY <<<\n#{40}', content)
    
    output_data = []
    global_chapter_count = 1 

    print(f"[*] Analyzing {len(raw_blocks)} blocks for chapters...")

    for block in raw_blocks:
        # Chapter Detection Logic: Look for the narrative chapter header
        match = re.search(r'##\s+ORIGINAL\s+CHAPTER:\s+Chapter\s+([IVXLCDM]+)', block, re.IGNORECASE)
        
        if match:
            chapter_label = f"Chapter {global_chapter_count}"
            print(f"[*] Processing {chapter_label}...")

            # Clean technical markers so the LLM only sees narrative text
            clean_context = re.sub(r'###\s+SECTION\s+\d+\s+(ORIGINAL|TRANSLATED)', '', block)
            clean_context = re.sub(r"## (ORIGINAL|TRANSLATED) CHAPTER:.*\n", "", clean_context, flags=re.IGNORECASE)
            clean_context = re.sub(r"#{10,}|={10,}", "", clean_context)
            clean_context = clean_context.strip()

            # Generate Summary
            summary = summarize_text(clean_context)
            
            # Format output sequence
            output_data.append(f"TITLE: {chapter_label}")
            output_data.append(f"SUMMARY: {summary}") 
            
            # OPTIONAL: Generate and add Analysis
            if extract_analysis:
                print(f"[*] Generating literary analysis for {chapter_label}...")
                analysis = analyze_text(clean_context)
                output_data.append(f"ANALYSIS: {analysis}")
            
            output_data.append(f"CONTENT:\n{clean_context}\n")
            output_data.append("="*40 + "\n")
            
            global_chapter_count += 1
            time.sleep(1) # Respect rate limits

    # Save results
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("\n".join(output_data))
    
    print(f"[*] Finished! Output saved to: {output_file}")
    print(f"[*] Total Chapters Processed: {global_chapter_count - 1}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", required=True)
    parser.add_argument("-o", "--output_file", required=True)
    # New optional argument for literary analysis
    parser.add_argument("--extract-analysis", action="store_true", help="Generate literary analysis for each chapter")
    args = parser.parse_args()

    extract_chapters(args.input, args.output_file, args.extract_analysis)

