import argparse
import os
import zipfile
import shutil
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import re

# Default CSS path
DEFAULT_CSS_PATH = '/Users/edgargilchrist/tools/BookTranslator/Books/HtmlzOutput/wings/wings_one/new_style.css'

def clean_text_content(text):
    """Removes technical markers and artifacts."""
    text = re.sub(r'###\s+SECTION\s+\d+\s+(ORIGINAL|TRANSLATED)', '', text, flags=re.IGNORECASE)
    text = re.sub(r'^\s*[#=]{3,}\s*$', '', text, flags=re.MULTILINE)
    return text

def epub_to_jekyll_htmlz(epub_path, css_path, output_folder):
    if not os.path.exists(epub_path):
        print(f"Error: EPUB not found: {epub_path}")
        return

    os.makedirs(output_folder, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(epub_path))[0]
    htmlz_path = os.path.join(output_folder, f"{base_name}.htmlz")
    unpack_dir = os.path.join(output_folder, f"{base_name}_unpacked")

    try:
        book = epub.read_epub(epub_path)
    except Exception as e:
        print(f"Error reading EPUB: {e}")
        return

    files_to_zip = {}
    chapter_links = []
    count = 0

    print("[*] Converting EPUB chapters to Jekyll HTML...")

    for item_id, linear in book.spine:
        item = book.get_item_with_id(item_id)
        if not item or item.get_type() != ebooklib.ITEM_DOCUMENT:
            continue
            
        # SKIP THE NAVIGATION/FRONT MATTER
        # This prevents 'nav.xhtml' from becoming 'chap_01.html'
        if 'nav' in item.file_name.lower():
            print(f"[*] Skipping navigation file: {item.file_name}")
            continue

        count += 1
        # Now chap_01.xhtml (narrative) becomes chap_01.html (Jekyll)
        chapter_filename = f"chap_{count:02d}.html"
        chapter_soup = BeautifulSoup(item.get_content(), 'html.parser')
        body_content = chapter_soup.find('body')
        
        if body_content:
            cleaned_html = clean_text_content(body_content.decode_contents())
            chapter_title = f"Chapter {count}"
            chapter_page_content = f"""---
layout: default
title: "{chapter_title}"
css: style.css
---
{cleaned_html}
"""
            files_to_zip[chapter_filename] = chapter_page_content
            chapter_links.append(f'<li><a href="{chapter_filename}">{chapter_title}</a></li>')

    # Create the Main Index (Table of Contents)
    book_title = base_name.replace('_', ' ')
    index_html = f"""---
layout: default
title: "{book_title}"
css: style.css
---
<h1>{book_title}</h1>
<ol>
    {" ".join(chapter_links)}
</ol>
"""
    files_to_zip['index.html'] = index_html

    with zipfile.ZipFile(htmlz_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for filename, content in files_to_zip.items():
            zf.writestr(filename, content)
        with open(css_path, 'r') as f:
            zf.writestr('style.css', f.read())

    if os.path.exists(unpack_dir):
        shutil.rmtree(unpack_dir)
    os.makedirs(unpack_dir)
    with zipfile.ZipFile(htmlz_path, 'r') as zf:
        zf.extractall(unpack_dir)
    
    print(f"[SUCCESS] Processed {count} chapters. Index and individual pages created.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert EPUB to Multi-page Jekyll HTMLZ.")
    parser.add_argument("-i", "--input", required=True)
    parser.add_argument("-c", "--css", default=DEFAULT_CSS_PATH)
    parser.add_argument("--output_folder", required=True)
    args = parser.parse_args()
    epub_to_jekyll_htmlz(args.input, args.css, args.output_folder)

