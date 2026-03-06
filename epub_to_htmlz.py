import argparse
import os
import shutil
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import re

# Default CSS path based on your setup
DEFAULT_CSS_PATH = '/Users/edgargilchrist/tools/BookTranslator/Books/HtmlzOutput/wings/wings_one/test_style.css'

def clean_text_content(text):
    """Removes technical markers, artifacts, and duplicate chapter headings."""
    text = re.sub(r'###\s+SECTION\s+\d+\s+(ORIGINAL|TRANSLATED)', '', text, flags=re.IGNORECASE)
    text = re.sub(r'^\s*[#=]{3,}\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'<div class="chapter-audio">.*?</div>', '', text, flags=re.DOTALL | re.IGNORECASE)
    
    # NEW: Remove existing chapter titles from the original text (e.g., <h1>Chapter III</h1>)
    # This prevents the double-title issue seen in your screenshots.
    text = re.sub(r'<h[12][^>]*>.*?</h[12]>', '', text, flags=re.IGNORECASE | re.DOTALL)
    
    return text


def epub_to_jekyll_htmlz(epub_path, css_path, output_folder):
    if not os.path.exists(epub_path):
        print(f"Error: EPUB not found: {epub_path}")
        return

    # Ensure the target directory exists, but DO NOT delete it
    os.makedirs(output_folder, exist_ok=True)
    
    # Ensure the Illustrations subfolder exists for your .png files
    illustrations_dir = os.path.join(output_folder, "Illustrations")
    os.makedirs(illustrations_dir, exist_ok=True)
    
    try:
        book = epub.read_epub(epub_path)
    except Exception as e:
        print(f"Error reading EPUB: {e}")
        return

    chapter_links = []
    count = 0

    print(f"[*] Writing chapters directly to: {output_folder}")

    for item_id, linear in book.spine:
        item = book.get_item_with_id(item_id)
        if not item or item.get_type() != ebooklib.ITEM_DOCUMENT:
            continue
            
        if 'nav' in item.file_name.lower():
            continue

        count += 1
        chapter_filename = f"Chapter_{count}.html" 
        chapter_soup = BeautifulSoup(item.get_content(), 'html.parser')
        body_content = chapter_soup.find('body')
        
        if body_content:
            cleaned_html = clean_text_content(body_content.decode_contents())
            chapter_title = f"Chapter {count}"
            
            # This NEW block combines the Title and Image into one horizontal row
            combined_header_html = f"""
<div class="chapter-header-row" style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 40px; gap: 30px;">
    <h1 class="chapter-title" style="margin: 0; flex: 1; font-size: 2.5em;">{chapter_title}</h1>
    <div class="chapter-illustration" style="flex: 1.5; text-align: right;">
        <img src="Illustrations/Chap_{count}_illus.png" alt="Illustration for {chapter_title}" style="width: 100%; max-width: 500px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.2);">
    </div>
</div>"""
            
            # Now we use {combined_header_html} instead of separate variables
            chapter_page_content = f"""---
layout: default
title: "{chapter_title}"
css: test_style.css
audio_url: "https://media.githubusercontent.com/media/egilchri/wings_one/main/Chapter_{count}.mp3"
---
{combined_header_html}

{cleaned_html}
"""

            # Write individual chapter file
            with open(os.path.join(output_folder, chapter_filename), 'w', encoding='utf-8') as f:
                f.write(chapter_page_content)
            
            chapter_links.append(f"""
                <a href="{chapter_filename}" class="chapter-square">
                   <span class="square-label">Chapter</span>
                   <span class="square-number">{count}</span>
                </a>""")

    # Write the Main Index
    book_title = os.path.splitext(os.path.basename(epub_path))[0].replace('_', ' ')
    index_html = f"""---
layout: default
title: "{book_title}"
css: test_style.css
---
<h1 class="main-title">{book_title}</h1>
<div class="chapter-grid">
    {" ".join(chapter_links)}
</div>
"""
    with open(os.path.join(output_folder, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(index_html)

    # Copy the CSS file
    if os.path.exists(css_path):
        shutil.copy(css_path, os.path.join(output_folder, 'test_style.css'))
    
    print(f"[SUCCESS] Processed {count} chapters into {output_folder}. Existing files were preserved.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Render a Henry James scene via DALL-E.")
    parser.add_argument("--output", type=str, required=True)
    parser.add_argument("--description", type=str, required=True, help="JSON string OR path to a JSON file")

    args = parser.parse_args()

    # Check if the description argument is a path to a file
    if os.path.exists(args.description):
        with open(args.description, 'r') as f:
            description_content = f.read()
    else:
        description_content = args.description

    render_scene_to_png(description_content, args.output)

