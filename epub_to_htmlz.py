import argparse
import os
import shutil
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import re

# Default CSS path based on your setup
DEFAULT_CSS_PATH = '/Users/edgargilchrist/tools/BookTranslator/Books/WingsOfDove/wings/wings_one/test_style.css'

def clean_text_content(text):
    """Removes technical markers, artifacts, and duplicate chapter headings."""
    text = re.sub(r'###\s+SECTION\s+\d+\s+(ORIGINAL|TRANSLATED)', '', text, flags=re.IGNORECASE)
    text = re.sub(r'^\s*[#=]{3,}\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'<div class="chapter-audio">.*?</div>', '', text, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove existing chapter titles from the original text (e.g., <h1>Chapter III</h1>)
    text = re.sub(r'<h[12][^>]*>.*?</h[12]>', '', text, flags=re.IGNORECASE | re.DOTALL)
    
    return text


def epub_to_jekyll_htmlz(epub_path, css_path, output_folder):
    if not os.path.exists(epub_path):
        print(f"Error: EPUB not found: {epub_path}")
        return

    # Ensure the target directory exists
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
            
            # FIXED: Header now uses a class for CSS control rather than hardcoded flex styles
            combined_header_html = f"""
<div class="chapter-header-row">
    <h1 class="chapter-title">{chapter_title}</h1>
    <div class="chapter-illustration">
        <img src="Illustrations/Chap_{count}_illus.png" alt="Illustration for {chapter_title}">
    </div>
</div>"""
            
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
viewport: "width=device-width, initial-scale=1.0"
---
<h1 class="main-title">{book_title}</h1>
<div class="chapter-grid">
    {" ".join(chapter_links)}
</div>
"""
    with open(os.path.join(output_folder, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(index_html)

    # Ensure the CSS file exists and has mobile-responsive rules
    write_responsive_css(css_path, os.path.join(output_folder, 'test_style.css'))
    
    print(f"[SUCCESS] Processed {count} chapters into {output_folder}. Mobile-responsive meta-tags added.")

def write_responsive_css(src_path, dest_path):
    """Copies existing CSS and appends mobile-responsive rules if missing."""
    responsive_rules = """
/* Mobile Responsive Overrides */
.chapter-header-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 40px;
    gap: 30px;
}
.chapter-illustration img {
    width: 100%;
    max-width: 500px;
    border-radius: 8px;
    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
}
@media (max-width: 768px) {
    .chapter-header-row {
        flex-direction: column-reverse;
        text-align: center;
        gap: 20px;
    }
    .chapter-title {
        font-size: 1.8em !important;
    }
    .chapter-illustration img {
        max-width: 100%;
    }
    .chapter-grid {
        grid-template-columns: repeat(auto-fill, minmax(80px, 1fr)) !important;
    }
}
"""
    content = ""
    if os.path.exists(src_path):
        with open(src_path, 'r') as f:
            content = f.read()
    
    if ".chapter-header-row" not in content:
        content += responsive_rules

    with open(dest_path, 'w') as f:
        f.write(content)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert EPUB to Jekyll-ready HTML with responsive design.")
    parser.add_argument("-i", "--input", required=True, help="Path to the source EPUB")
    parser.add_argument("-o", "--output_folder", required=True, help="Target directory for HTML files")
    parser.add_argument("--css", default=DEFAULT_CSS_PATH, help="Path to the source test_style.css")

    args = parser.parse_args()
    epub_to_jekyll_htmlz(args.input, args.css, args.output_folder)
    
