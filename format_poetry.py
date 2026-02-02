import os
import re
from bs4 import BeautifulSoup

def format_html_poetry(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')

    # 1. Ensure the H1 (Canto Title) is prominent and centered
    h1 = soup.find('h1')
    if h1:
        h1['style'] = "text-align: center; border-bottom: 2px solid #333; padding-bottom: 10px;"

    # 2. Process each bilingual row
    for row in soup.find_all(class_='bilingual-row'):
        # Change row to column layout to stack Italian over English
        row['style'] = "display: block; margin-bottom: 30px; padding-bottom: 15px; border-bottom: 1px solid #ddd;"
        
        orig = row.find(class_='original')
        trans = row.find(class_='translation')

        if orig:
            # Replace commas or mid-sentence breaks with actual line breaks 
            # or preserve existing ones if present in the text
            raw_text = orig.get_text().strip()
            # If the text is the 3-line tercet, ensure breaks after punctuation
            formatted_text = raw_text.replace(', ', ',<br/>').replace('. ', '.<br/>')
            orig.clear()
            orig.append(BeautifulSoup(formatted_text, 'html.parser'))
            orig['style'] = "font-style: italic; color: #2c3e50; margin-bottom: 10px; display: block;"

        if trans:
            trans['style'] = "color: #7f8c8d; display: block; padding-left: 20px; border-left: 3px solid #eee;"

    # Save the modified file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(soup.prettify())

def run_filter_on_all():
    # Only target the Canto HTML files
    for filename in os.listdir('.'):
        if filename.endswith('.html') and 'Canto' in filename:
            print(f"[*] Reformatting {filename}...")
            format_html_poetry(filename)

if __name__ == "__main__":
    run_filter_on_all()

