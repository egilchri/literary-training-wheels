import argparse
import re
from bs4 import BeautifulSoup

def extract_summaries(canto_data_path):
    """Parses the text file and returns a dict mapping Canto names to summaries."""
    summaries = {}
    current_canto = None
    current_text = []
    
    # Matches "NARRATIVE SUMMARY: Inferno * Canto XXXII"
    canto_pattern = re.compile(r"NARRATIVE SUMMARY:\s*(.*?)\s*\(SECTIONS")
    
    with open(canto_data_path, 'r', encoding='utf-8') as f:
        for line in f:
            match = canto_pattern.search(line)
            if match:
                if current_canto:
                    summaries[current_canto] = " ".join(current_text).strip()
                
                # Standardize '*' to '•' to match your HTML's format
                current_canto = match.group(1).replace('*', '•').strip()
                current_text = []
            elif current_canto and "---" not in line:
                # CLEANER FIX: Removes patterns without the backslash error
                clean_line = re.sub(r"\"", "", line).strip()
                if clean_line:
                    current_text.append(clean_line)
                
        if current_canto:
            summaries[current_canto] = " ".join(current_text).strip()
            
    return summaries

def process_html(html_path, summaries):
    with open(html_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')

    found_any = False
    
    # Search for Canto markers in the source-text divs
    for segment in soup.find_all("div", class_="source-text"):
        text = segment.get_text()
        # Matches "Inferno • Canto XXXII" or "Inferno • Canto XXXIII"
        match = re.search(r"(Inferno|Purgatorio)\s*•\s*Canto\s+[IVXLCDM]+", text)
        
        if match:
            canto_title = match.group(0).strip()
            summary_text = summaries.get(canto_title)
            
            if summary_text:
                found_any = True
                
                # 1. Create the <h1> heading
                new_h1 = soup.new_tag("h1")
                new_h1.string = canto_title
                
                # 2. Create the summary <div>
                summary_div = soup.new_tag("div", attrs={"class": "canto-summary"})
                summary_div.string = summary_text
                summary_div['style'] = "background: #f0f4f8; border-left: 5px solid #2c3e50; padding: 15px; margin-bottom: 25px; font-style: italic;"
                
                # 3. Locate the segment to insert before
                parent_segment = segment.find_parent("div", class_="segment")
                
                # 4. Remove the title from the original text
                segment.string = text.replace(canto_title, "").strip()
                
                # 5. Insert Heading and Summary
                parent_segment.insert_before(new_h1)
                new_h1.insert_after(summary_div)

    if found_any:
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(soup.prettify())
        print(f"Successfully processed: {html_path}")
    else:
        print("No matching Canto data found in the HTML.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Inject Canto headings and summaries.")
    parser.add_argument("-html_file", required=True)
    parser.add_argument("-canto_data", required=True)
    
    args = parser.parse_args()
    
    canto_map = extract_summaries(args.canto_data)
    process_html(args.html_file, canto_map)

