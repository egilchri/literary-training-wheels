import os, re

def map_canto_sections(bilingual_path):
    """Parses the bilingual file to find the start and end sections for each Canto."""
    canto_map = []
    current_canto = None
    current_start = None
    
    # Matches: ### SECTION 11 ORIGINAL
    section_pattern = re.compile(r'### SECTION (\d+) ORIGINAL')
    # Matches: <h3 class='canto-header'>Inferno • Canto I</h3>
    header_pattern = re.compile(r"<h3 class='canto-header'>(.*?)</h3>")

    with open(bilingual_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    last_section = 0
    for line in lines:
        sect_match = section_pattern.search(line)
        if sect_match:
            last_section = int(sect_match.group(1))

        header_match = header_pattern.search(line)
        if header_match:
            # If we were already tracking a Canto, its end is the section before this one
            if current_canto:
                canto_map.append({
                    'name': current_canto,
                    'start': current_start,
                    'end': last_section - 1
                })
            
            current_canto = header_match.group(1).replace(' • ', ' * ')
            current_start = last_section

    # Add the final Canto
    if current_canto:
        canto_map.append({
            'name': current_canto,
            'start': current_start,
            'end': last_section
        })
        
    return canto_map

def rehabilitate_file(summary_path, canto_map):
    """Writes a new file with the (SECTIONS start-end) added to headers."""
    output_path = summary_path.replace('.txt', '_rehabilitated.txt')
    
    with open(summary_path, 'r', encoding='utf-8') as f:
        content = f.read()

    for canto in canto_map:
        # Search for the header without the section range
        # We use re.escape because of the '*' in your summary file
        search_pattern = re.escape(f"NARRATIVE SUMMARY: {canto['name']}") + " "
        
        # Check if it already has a range to avoid double-processing the first line
        if f"{canto['name']} (SECTIONS" in content:
            continue
            
        replacement = f"NARRATIVE SUMMARY: {canto['name']} (SECTIONS {canto['start']}-{canto['end']})"
        content = re.sub(search_pattern, replacement, content)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"[*] Success! Rehabilitated file created: {output_path}")

if __name__ == "__main__":
    # Pointing to your Books folder structure
    BILINGUAL_FILE = "Books/divine_comedy_Bilingual_aug.txt"
    SUMMARY_FILE = "Books/divine_comedy_all_summaries_new.txt"

    if os.path.exists(BILINGUAL_FILE) and os.path.exists(SUMMARY_FILE):
        mapping = map_canto_sections(BILINGUAL_FILE)
        rehabilitate_file(SUMMARY_FILE, mapping)
    else:
        print("[!] Error: Ensure both files are in the 'Books/' directory.")

