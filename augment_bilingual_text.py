import os, ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup

def extract_canto_literals(epub_path):
    """
    Extracts the Canto header and the literal HTML string of the 
    first paragraph following it to use for an exact match.
    """
    book = epub.read_epub(epub_path)
    canto_data = []
    
    # Target Location • Canto Roman
    import re
    canto_pattern = re.compile(r'(Inferno|Purgatorio|Paradiso)\s*•\s*Canto\s*[IVXLCDM]+', re.IGNORECASE)

    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        soup = BeautifulSoup(item.get_content(), 'html.parser')
        for tag in soup.find_all(['h1', 'h2', 'h3', 'p']):
            if canto_pattern.search(tag.get_text()):
                header = tag.get_text(strip=True)
                # Find the next paragraph and get its literal inner HTML
                next_p = tag.find_next('p')
                if next_p:
                    # We store the literal inner content (including <br/> tags)
                    literal_content = "".join([str(c) for c in next_p.contents]).strip()
                    canto_data.append((header, literal_content))
    return canto_data

def augment_with_literals(input_txt, output_txt, canto_data):
    """
    Performs a literal string replacement.
    """
    with open(input_txt, 'r', encoding='utf-8') as f:
        content = f.read()

    found_count = 0
    for header, literal_text in canto_data:
        # We look for the exact literal text preceded by a <p> tag
        # This matches the raw structure: <p>\n  Nel mezzo...
        search_string = f"<p>\n  {literal_text}"
        
        if search_string in content:
            # We insert the header immediately before the <p> tag
            insertion = f"<h3 class='canto-header'>{header}</h3>\n{search_string}"
            content = content.replace(search_string, insertion)
            found_count += 1
        else:
            # Fallback check: try without the specific indentation
            search_alt = f"<p>{literal_text}"
            if search_alt in content:
                insertion = f"<h3 class='canto-header'>{header}</h3>\n{search_alt}"
                content = content.replace(search_alt, insertion)
                found_count += 1
            else:
                print(f"[!] Literal match failed for: {header}")

    with open(output_txt, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"[*] Success: {found_count} headers inserted into {output_txt}.")

if __name__ == "__main__":
    # Ensure files are in the Books folder as previously specified
    EPUB = "Books/divine_comedy.epub"
    IN_TXT = "Books/divine_comedy_Bilingual.txt"
    OUT_TXT = "Books/divine_comedy_Bilingual_aug.txt"

    if os.path.exists(EPUB) and os.path.exists(IN_TXT):
        data = extract_canto_literals(EPUB)
        augment_with_literals(IN_TXT, OUT_TXT, data)
    else:
        print("[!] Error: Check your Books/ folder for the required files.")

