import os, re, argparse, time
from google import genai

# Configuration
MODEL_NAME = 'gemini-2.5-pro'
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

def analyze_text(text):
    """
    Sends aggregated English narrative text to the LLM for literary analysis.
    """
    if not text.strip():
        return "No content available for analysis."
    
    prompt = f"""Provide a concise character study based on this text. 
    Focus only on how characters are presented and any immediate shifts in their situation. 
    Avoid thematic or philosophical discussion.

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
        print(f"[!] LLM Error during analysis: {e}")
        return "Analysis generation failed."

def summarize_text(text):
    """
    Sends aggregated English narrative text to the LLM for action-only summarization.
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
        print(f"[!] LLM Error during summary: {e}")
        return "Summary generation failed."

def extract_chapters(input_txt, output_file, extract_analysis=False):
    if not os.path.exists(input_txt):
        print(f"[!] Input file not found: {input_txt}")
        return

    with open(input_txt, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split into sections based on the divider used in translate_epub.py
    raw_sections = re.split(r'={40}', content)
    
    output_data = []
    
    # Tracking variables
    current_chapter_title = None
    current_chapter_accumulator = []

    # Regex to find the <h2> tag with ONLY a Roman Numeral
    ROMAN_H2_RE = r"<h2[^>]*?>\s*([ivxlcdm]+)\s*</h2>"

    print(f"[*] Analyzing {len(raw_sections)} sections for narrative chapters...")

    for section in raw_sections:
        if not section.strip():
            continue

        # Check if this section is a Chapter Header
        header_match = re.search(ROMAN_H2_RE, section, re.IGNORECASE)
        
        if header_match:
            # If we were already building a chapter, finalize it before starting the next one
            if current_chapter_title and current_chapter_accumulator:
                process_and_append_chapter(
                    current_chapter_title, 
                    current_chapter_accumulator, 
                    output_data, 
                    extract_analysis
                )
            
            # Start new chapter tracking
            current_chapter_title = header_match.group(1).upper().strip()
            current_chapter_accumulator = []
            print(f"[*] Started collecting Chapter {current_chapter_title}")
            continue

        # If we are currently inside a chapter, collect the ORIGINAL English text
        if current_chapter_title:
            # Extract only the content inside the ORIGINAL section
            # This avoids sending the <details> translation blocks to the LLM
            original_match = re.search(r"### SECTION \d+ ORIGINAL\n(.*?)(?=\n<details>|### SECTION|$)", section, re.DOTALL)
            if original_match:
                # Strip HTML tags so the LLM gets clean prose
                clean_prose = re.sub(r'<[^>]+>', '', original_match.group(1)).strip()
                if clean_prose:
                    current_chapter_accumulator.append(clean_prose)

    # Process the final chapter in the file
    if current_chapter_title and current_chapter_accumulator:
        process_and_append_chapter(
            current_chapter_title, 
            current_chapter_accumulator, 
            output_data, 
            extract_analysis
        )

    # Save results
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("\n".join(output_data))
    
    print(f"[*] Finished! Output saved to: {output_file}")

def process_and_append_chapter(title, text_list, output_list, extract_analysis):
    """Aggregates text and calls LLM for summary and optional analysis."""
    full_narrative = "\n\n".join(text_list).strip()
    if not full_narrative:
        return

    print(f"    - Processing Chapter {title}...")
    
    # 1. Generate Summary
    summary = summarize_text(full_narrative)
    
    # 2. Format Header
    output_list.append(f"TITLE: Chapter {title}")
    output_list.append(f"SUMMARY: {summary}")
    
    # 3. Optional Analysis
    if extract_analysis:
        analysis = analyze_text(full_narrative)
        output_list.append(f"ANALYSIS: {analysis}")
    
    # 4. Append the clean text content
    output_list.append(f"CONTENT:\n{full_narrative}\n")
    output_list.append("="*40 + "\n")
    
    # Respect rate limits
    time.sleep(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", required=True)
    parser.add_argument("-o", "--output_file", required=True)
    parser.add_argument("--extract-analysis", action="store_true")
    args = parser.parse_args()

    extract_chapters(args.input, args.output_file, args.extract_analysis)

    
