import re
import argparse
import os
from google import genai

# Securely fetch the API key from your environment
api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    print("Error: GEMINI_API_KEY environment variable not set.")
    exit(1)

client = genai.Client(api_key=api_key)

# Using the Gemini 2.5 Pro model from your verified list
MODEL_NAME = 'gemini-2.5-pro'

def summarize_with_gemini(text, canto_name):
    """Generates a direct narrative summary focusing only on plot events."""
    if not text:
        return "No text found to summarize."
    
    prompt = f"""
    Provide a direct, factual summary of the events that occur in {canto_name} of Dante's 'Divine Comedy'.
    
    Instructions:
    - Narrative Only: Focus strictly on the physical actions, the journey, and the characters encountered.
    - No Symbolism: Do not include analysis of what characters or events symbolize. Avoid theological or allegorical interpretation.
    - Tone: Professional and objective. No 'chatty' openings or conclusions.
    - Style: Use clear, descriptive prose.
    - Length: Approximately 150 words.

    TEXT:
    {text}
    """
    
    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"Gemini Error: {e}"

def process_cantos(file_path, start_canto, end_canto):
    """Extracts text and tracks SECTION numbers for each Canto."""
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' not found.")
        return

    # Regex patterns
    canto_pattern = re.compile(r'(\w+)\s*[•*]\s*(Canto\s+[IVXLCDM]+)', re.IGNORECASE)
    section_pattern = re.compile(r'### SECTION (\d+) ORIGINAL', re.IGNORECASE)
    
    current_canto_name = None
    accumulating = False
    in_translation = False
    
    # Store data as: { canto_name: { 'text': [], 'sections': [] } }
    canto_data = {} 
    current_text = []
    current_sections = []

    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            clean_line = line.strip()
            
            # 1. Track Section Markers
            section_match = section_pattern.search(clean_line)
            if section_match and accumulating:
                current_sections.append(int(section_match.group(1)))

            # 2. Track Canto Headings
            canto_match = canto_pattern.search(clean_line)
            if canto_match:
                found_name = f"{canto_match.group(1)} * {canto_match.group(2)}"
                
                # Save previous Canto data
                if current_canto_name and accumulating:
                    canto_data[current_canto_name] = {
                        'text': "\n".join(current_text),
                        'sections': sorted(current_sections)
                    }
                    current_text = []
                    current_sections = []

                if found_name == start_canto:
                    accumulating = True
                current_canto_name = found_name

            # 3. Accumulate Translation Content
            if accumulating:
                if "class='translation-content'" in clean_line or 'class="translation-content"' in clean_line:
                    in_translation = True
                    continue
                if in_translation:
                    if "</div>" in clean_line:
                        in_translation = False
                    else:
                        text_only = re.sub('<[^<]+?>', '', clean_line)
                        if text_only:
                            current_text.append(text_only)

    # Finalize the last Canto
    if current_canto_name and accumulating:
        canto_data[current_canto_name] = {
            'text': "\n".join(current_text),
            'sections': sorted(current_sections)
        }

    # Output with Section Ranges
    in_range = False
    for name, data in canto_data.items():
        if name == start_canto: in_range = True
        if in_range:
            # Format the section range string
            sec_list = data['sections']
            sec_range = f"(SECTIONS {sec_list[0]}-{sec_list[-1]})" if sec_list else ""
            
            print(f"\n{'-'*70}")
            print(f"NARRATIVE SUMMARY: {name} {sec_range}")
            print(f"{'-'*70}")
            
            print(summarize_with_gemini(data['text'], name))
            
            if name == end_canto: break

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-input", required=True)
    parser.add_argument("-start_canto", required=True)
    parser.add_argument("-end_canto", required=True)
    args = parser.parse_args()
    process_cantos(args.input, args.start_canto, args.end_canto)

